import pytest
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path

from backend.agents.quality_guardian import QualityGuardian
from backend.core.models import QualityMetrics


class TestQualityGuardian:
    
    @pytest.fixture
    def quality_guardian(self):
        """Create a QualityGuardian instance"""
        return QualityGuardian(threshold=30.0)
    
    @pytest.fixture
    def create_test_image(self):
        """Factory fixture to create test images"""
        def _create_image(image_type="complex"):
            if image_type == "complex":
                # Create a complex image with good texture
                img_array = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
                # Add some patterns
                for i in range(0, 512, 32):
                    img_array[i:i+2, :] = 255
                    img_array[:, i:i+2] = 0
            
            elif image_type == "uniform":
                # Create mostly uniform image (like blue sky)
                img_array = np.full((512, 512, 3), 150, dtype=np.uint8)
                # Add tiny bit of variation
                img_array[100:110, 100:110] = 160
            
            elif image_type == "low_contrast":
                # Create low contrast image
                img_array = np.random.randint(100, 120, (512, 512, 3), dtype=np.uint8)
            
            elif image_type == "edges":
                # Create image with many edges
                img_array = np.zeros((512, 512, 3), dtype=np.uint8)
                # Create checkerboard pattern
                for i in range(0, 512, 16):
                    for j in range(0, 512, 16):
                        if (i//16 + j//16) % 2 == 0:
                            img_array[i:i+16, j:j+16] = 255
            
            return Image.fromarray(img_array, 'RGB')
        
        return _create_image
    
    def test_evaluate_complex_image(self, quality_guardian, create_test_image, tmp_path):
        """Test evaluation of a complex image that should pass"""
        # Create and save test image
        image = create_test_image("complex")
        image_path = tmp_path / "complex_test.png"
        image.save(image_path)
        
        # Evaluate
        metrics = quality_guardian.evaluate(str(image_path))
        
        assert isinstance(metrics, QualityMetrics)
        assert metrics.edge_density > 0
        assert metrics.color_entropy > 0
        assert metrics.local_contrast > 0
        assert 0 <= metrics.overall_score <= 100
    
    def test_evaluate_uniform_image(self, quality_guardian, create_test_image, tmp_path):
        """Test evaluation of a uniform image that should fail"""
        # Create and save test image
        image = create_test_image("uniform")
        image_path = tmp_path / "uniform_test.png"
        image.save(image_path)
        
        # Evaluate
        metrics = quality_guardian.evaluate(str(image_path))
        
        # Uniform image should have low scores
        assert metrics.edge_density < 10
        assert metrics.color_entropy < 2
        assert metrics.local_contrast < 20
        assert not metrics.passes_threshold(30.0)
    
    def test_calculate_edge_density(self, quality_guardian, create_test_image):
        """Test edge density calculation"""
        # Test with edge-heavy image
        edge_image = create_test_image("edges")
        edge_array = np.array(edge_image)
        
        edge_density = quality_guardian.calculate_edge_density(edge_array)
        
        assert isinstance(edge_density, float)
        assert 0 <= edge_density <= 100
        assert edge_density > 20  # Checkerboard should have high edge density
    
    def test_calculate_color_entropy(self, quality_guardian, create_test_image):
        """Test color entropy calculation"""
        # Test with complex image
        complex_image = create_test_image("complex")
        complex_array = np.array(complex_image)
        
        entropy = quality_guardian.calculate_color_entropy(complex_array)
        
        assert isinstance(entropy, float)
        assert entropy > 0
        
        # Test with uniform image (should have low entropy)
        uniform_image = create_test_image("uniform")
        uniform_array = np.array(uniform_image)
        
        uniform_entropy = quality_guardian.calculate_color_entropy(uniform_array)
        assert uniform_entropy < entropy  # Complex should have higher entropy
    
    def test_calculate_local_contrast(self, quality_guardian, create_test_image):
        """Test local contrast calculation"""
        # Test with edge image (high contrast)
        edge_image = create_test_image("edges")
        edge_array = np.array(edge_image)
        
        contrast = quality_guardian.calculate_local_contrast(edge_array)
        
        assert isinstance(contrast, float)
        assert 0 <= contrast <= 100
        assert contrast > 30  # Checkerboard should have high contrast
        
        # Test with low contrast image
        low_contrast_image = create_test_image("low_contrast")
        low_contrast_array = np.array(low_contrast_image)
        
        low_contrast = quality_guardian.calculate_local_contrast(low_contrast_array)
        assert low_contrast < contrast
    
    def test_has_large_uniform_areas(self, quality_guardian, create_test_image):
        """Test detection of large uniform areas"""
        # Test uniform image
        uniform_image = create_test_image("uniform")
        uniform_array = np.array(uniform_image)
        
        assert quality_guardian._has_large_uniform_areas(uniform_array, threshold=0.4)
        
        # Test complex image
        complex_image = create_test_image("complex")
        complex_array = np.array(complex_image)
        
        assert not quality_guardian._has_large_uniform_areas(complex_array, threshold=0.4)
    
    def test_get_failure_reasons(self, quality_guardian):
        """Test failure reason generation"""
        # Create metrics that fail different thresholds
        failing_metrics = QualityMetrics(
            edge_density=5.0,      # Below threshold
            color_entropy=3.0,     # Below threshold
            local_contrast=15.0,   # Below threshold
            overall_score=40.0     # Below threshold
        )
        
        reasons = quality_guardian._get_failure_reasons(failing_metrics)
        
        assert len(reasons) == 4
        assert any("edge density" in r for r in reasons)
        assert any("color variety" in r for r in reasons)
        assert any("contrast" in r for r in reasons)
        assert any("Overall score" in r for r in reasons)
    
    def test_batch_evaluate(self, quality_guardian, create_test_image, tmp_path):
        """Test batch evaluation of multiple images"""
        # Create test images
        images = {
            "complex": create_test_image("complex"),
            "uniform": create_test_image("uniform"),
            "edges": create_test_image("edges")
        }
        
        image_paths = []
        for name, img in images.items():
            path = tmp_path / f"{name}_test.png"
            img.save(path)
            image_paths.append(str(path))
        
        # Batch evaluate
        results = quality_guardian.batch_evaluate(image_paths)
        
        assert len(results) == 3
        for path, metrics in results:
            assert isinstance(metrics, QualityMetrics)
            assert path in image_paths
    
    def test_metric_weights(self, quality_guardian):
        """Test that metric weights sum to 1"""
        total_weight = sum(quality_guardian.metric_weights.values())
        assert abs(total_weight - 1.0) < 0.001
