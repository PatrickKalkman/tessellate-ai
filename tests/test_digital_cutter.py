import pytest
import numpy as np
from PIL import Image
from pathlib import Path
import json

from backend.agents.digital_cutter import DigitalCutter
from backend.core.models import PuzzleManifest, CuttingStyle


class TestDigitalCutter:
    
    @pytest.fixture
    def digital_cutter(self):
        """Create a DigitalCutter instance with small grid for testing"""
        return DigitalCutter(grid_size=(4, 4))  # 4x4 grid for faster tests
    
    @pytest.fixture
    def test_image(self, tmp_path):
        """Create a test image with distinct patterns"""
        # Create a colorful test image with patterns
        size = 2048
        img_array = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Create a gradient pattern with different colors in each quadrant
        for i in range(size):
            for j in range(size):
                # Top-left: Red gradient
                if i < size//2 and j < size//2:
                    img_array[i, j] = [255 * (i/(size//2)), 0, 0]
                # Top-right: Green gradient
                elif i < size//2 and j >= size//2:
                    img_array[i, j] = [0, 255 * (i/(size//2)), 0]
                # Bottom-left: Blue gradient
                elif i >= size//2 and j < size//2:
                    img_array[i, j] = [0, 0, 255 * ((i-size//2)/(size//2))]
                # Bottom-right: Yellow gradient
                else:
                    img_array[i, j] = [255 * ((i-size//2)/(size//2)), 
                                     255 * ((j-size//2)/(size//2)), 0]
        
        # Save test image
        image = Image.fromarray(img_array, 'RGB')
        image_path = tmp_path / "test_puzzle.png"
        image.save(image_path)
        
        return str(image_path)
    
    def test_cut_puzzle_classic_style(self, digital_cutter, test_image, tmp_path):
        """Test cutting a puzzle with classic style"""
        output_dir = str(tmp_path / "puzzle_output")
        
        # Cut the puzzle
        manifest = digital_cutter.cut_puzzle(
            test_image, 
            output_dir, 
            style=CuttingStyle.CLASSIC
        )
        
        # Verify manifest
        assert isinstance(manifest, PuzzleManifest)
        assert manifest.size == 2048
        assert manifest.grid == (4, 4)
        assert len(manifest.pieces) == 16
        
        # Verify all pieces were created
        output_path = Path(output_dir)
        piece_files = list(output_path.glob("piece_*.png"))
        assert len(piece_files) == 16
        
        # Verify manifest file exists
        manifest_file = output_path / "manifest.json"
        assert manifest_file.exists()
        
        # Load and verify manifest content
        with open(manifest_file) as f:
            manifest_data = json.load(f)
        assert manifest_data["size"] == 2048
        assert manifest_data["grid"] == [4, 4]
        assert len(manifest_data["pieces"]) == 16
    
    def test_piece_positions(self, digital_cutter, test_image, tmp_path):
        """Test that piece positions are calculated correctly"""
        output_dir = str(tmp_path / "puzzle_output")
        manifest = digital_cutter.cut_puzzle(test_image, output_dir)
        
        # Check piece positions
        piece_size = digital_cutter.piece_size
        for piece in manifest.pieces:
            expected_row = piece.id // 4
            expected_col = piece.id % 4
            expected_x = expected_col * piece_size
            expected_y = expected_row * piece_size
            
            assert piece.x == expected_x
            assert piece.y == expected_y
    
    def test_piece_transparency(self, digital_cutter, test_image, tmp_path):
        """Test that pieces have transparent backgrounds"""
        output_dir = str(tmp_path / "puzzle_output")
        digital_cutter.cut_puzzle(test_image, output_dir)
        
        # Load a piece and check for transparency
        piece_path = Path(output_dir) / "piece_000.png"
        piece_img = Image.open(piece_path)
        
        # Verify RGBA mode
        assert piece_img.mode == 'RGBA'
        
        # Check that piece has expected size
        assert piece_img.size == (digital_cutter.piece_size, digital_cutter.piece_size)
        
        # Verify some pixels are transparent (alpha < 255)
        piece_array = np.array(piece_img)
        alpha_channel = piece_array[:, :, 3]
        assert np.any(alpha_channel < 255)  # Some transparent pixels
        assert np.any(alpha_channel == 255)  # Some opaque pixels
    
    def test_edge_patterns_generation(self, digital_cutter):
        """Test edge pattern generation for pieces"""
        patterns = digital_cutter._generate_edge_patterns()
        
        # Check horizontal edges (3 rows of edges for 4x4 grid)
        for row in range(3):
            for col in range(4):
                key = f"h_{row}_{col}"
                assert key in patterns
                assert isinstance(patterns[key], bool)
        
        # Check vertical edges (4 rows, 3 cols of edges for 4x4 grid)
        for row in range(4):
            for col in range(3):
                key = f"v_{row}_{col}"
                assert key in patterns
                assert isinstance(patterns[key], bool)
        
        # Total edges should be (rows-1)*cols + rows*(cols-1)
        expected_edges = 3*4 + 4*3
        assert len(patterns) == expected_edges
    
    def test_edge_type_methods(self, digital_cutter):
        """Test edge type determination methods"""
        patterns = {
            "h_0_1": True,   # Tab pointing down
            "h_1_1": False,  # Tab pointing up
            "v_1_0": True,   # Tab pointing right
            "v_1_1": False,  # Tab pointing left
        }
        
        # Test top edge
        assert digital_cutter._get_top_edge_type(0, 0, patterns) == 'straight'  # Top row
        assert digital_cutter._get_top_edge_type(1, 1, patterns) == 'blank'     # Has tab above
        assert digital_cutter._get_top_edge_type(2, 1, patterns) == 'tab'       # Has blank above
        
        # Test bottom edge
        assert digital_cutter._get_bottom_edge_type(3, 0, patterns) == 'straight'  # Bottom row
        assert digital_cutter._get_bottom_edge_type(1, 1, patterns) == 'blank'     # Has blank below
        
        # Test left edge
        assert digital_cutter._get_left_edge_type(0, 0, patterns) == 'straight'  # Left column
        assert digital_cutter._get_left_edge_type(1, 1, patterns) == 'blank'     # Has tab to left
        
        # Test right edge
        assert digital_cutter._get_right_edge_type(0, 3, patterns) == 'straight'  # Right column
        assert digital_cutter._get_right_edge_type(1, 0, patterns) == 'tab'       # Has tab to right
    
    def test_different_cutting_styles(self, digital_cutter, test_image, tmp_path):
        """Test different cutting styles produce different results"""
        styles = [CuttingStyle.CLASSIC, CuttingStyle.GEOMETRIC, CuttingStyle.ORGANIC]
        
        for style in styles:
            output_dir = str(tmp_path / f"puzzle_{style.value}")
            manifest = digital_cutter.cut_puzzle(test_image, output_dir, style=style)
            
            # Verify pieces were created
            assert len(manifest.pieces) == 16
            
            # Check that at least one piece exists and is valid
            piece_path = Path(output_dir) / "piece_000.png"
            assert piece_path.exists()
            
            piece_img = Image.open(piece_path)
            assert piece_img.mode == 'RGBA'
    
    def test_image_resizing(self, digital_cutter, tmp_path):
        """Test that non-standard size images are resized correctly"""
        # Create a small test image
        small_img = Image.new('RGB', (512, 512), color='red')
        img_path = tmp_path / "small_image.png"
        small_img.save(img_path)
        
        output_dir = str(tmp_path / "resized_output")
        manifest = digital_cutter.cut_puzzle(str(img_path), output_dir)
        
        # Should still produce correct number of pieces
        assert len(manifest.pieces) == 16
        assert manifest.size == 2048  # Should be resized to standard size
    
    def test_piece_mask_creation(self, digital_cutter):
        """Test piece mask creation"""
        patterns = digital_cutter._generate_edge_patterns()
        
        # Test corner piece (0,0) - should have two straight edges
        mask = digital_cutter._create_piece_mask(0, 0, patterns, CuttingStyle.CLASSIC)
        assert isinstance(mask, Image.Image)
        assert mask.mode == 'L'
        
        # Mask should be larger than piece size to accommodate tabs
        expected_size = digital_cutter.piece_size + 2 * digital_cutter.tab_size
        assert mask.size == (expected_size, expected_size)
        
        # Test that mask has both black and white pixels
        mask_array = np.array(mask)
        assert np.any(mask_array == 0)    # Black pixels (transparent)
        assert np.any(mask_array == 255)  # White pixels (piece)
    
    def test_extract_piece_boundaries(self, digital_cutter, test_image, tmp_path):
        """Test piece extraction at image boundaries"""
        # Create a simple mask
        mask_size = digital_cutter.piece_size + 2 * digital_cutter.tab_size
        mask = Image.new('L', (mask_size, mask_size), 255)  # All white
        
        # Load test image
        image = Image.open(test_image).convert('RGBA')
        
        # Test extraction at corner (should handle boundary correctly)
        piece = digital_cutter._extract_piece(image, 0, 0, mask)
        assert piece.size == (digital_cutter.piece_size, digital_cutter.piece_size)
        assert piece.mode == 'RGBA'