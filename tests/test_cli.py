import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json
from pathlib import Path

from backend.cli import main, PuzzleGenerator
from backend.core.models import QualityMetrics, PuzzleManifest, PuzzleGenerationStatus


class TestCLI:
    
    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()
    
    @pytest.fixture
    def mock_puzzle_generator(self):
        """Mock the PuzzleGenerator class"""
        with patch('backend.cli.PuzzleGenerator') as mock:
            yield mock
    
    def test_cli_basic_run(self, runner, mock_puzzle_generator):
        """Test basic CLI invocation"""
        # Mock the generator
        mock_instance = Mock()
        mock_puzzle_generator.return_value = mock_instance
        
        result = runner.invoke(main, ['--count', '5'])
        
        assert result.exit_code == 0
        mock_instance.generate_puzzles.assert_called_once_with(
            5, 'public/puzzles', 0.5, MagicMock()
        )
    
    def test_cli_with_options(self, runner, mock_puzzle_generator):
        """Test CLI with various options"""
        mock_instance = Mock()
        mock_puzzle_generator.return_value = mock_instance
        
        result = runner.invoke(main, [
            '--count', '10',
            '--output', '/tmp/puzzles',
            '--complexity', '0.8',
            '--style', 'geometric',
            '--debug'
        ])
        
        assert result.exit_code == 0
        mock_instance.generate_puzzles.assert_called_once()
        
        # Check that debug was enabled
        from backend.core.config import settings
        assert settings.debug == True
    
    def test_cli_invalid_complexity(self, runner):
        """Test CLI with invalid complexity value"""
        result = runner.invoke(main, ['--complexity', '1.5'])
        
        assert result.exit_code == 1
        assert "Complexity must be between 0 and 1" in result.output
    
    def test_cli_help(self, runner):
        """Test CLI help message"""
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "Generate high-quality jigsaw puzzles" in result.output
        assert "--count" in result.output
        assert "--complexity" in result.output


class TestPuzzleGenerator:
    
    @pytest.fixture
    def mock_agents(self):
        """Mock all agents"""
        with patch('backend.cli.PromptArtisan') as mock_artisan, \
             patch('backend.cli.QualityGuardian') as mock_guardian, \
             patch('backend.cli.DigitalCutter') as mock_cutter, \
             patch('backend.cli.OpenAI') as mock_openai:
            
            yield {
                'artisan': mock_artisan,
                'guardian': mock_guardian,
                'cutter': mock_cutter,
                'openai': mock_openai
            }
    
    def test_puzzle_generator_init(self, mock_agents):
        """Test PuzzleGenerator initialization"""
        generator = PuzzleGenerator()
        
        assert generator.stats['attempts'] == 0
        assert generator.stats['accepted'] == 0
        assert generator.stats['rejected'] == 0
        assert generator.stats['failed'] == 0
    
    def test_generate_single_puzzle_success(self, mock_agents, tmp_path):
        """Test successful single puzzle generation"""
        # Setup mocks
        generator = PuzzleGenerator()
        
        # Mock artisan
        generator.artisan.generate_prompt.return_value = "test prompt"
        generator.artisan.create_image.return_value = Mock(
            prompt="test prompt",
            image_data=b"fake_image_data"
        )
        
        # Mock guardian
        generator.guardian.evaluate.return_value = QualityMetrics(
            edge_density=25.0,
            color_entropy=5.0,
            local_contrast=30.0,
            overall_score=85.0
        )
        
        # Mock cutter
        generator.cutter.cut_puzzle.return_value = PuzzleManifest(
            size=2048,
            grid=(16, 16),
            pieces=[Mock(id=i, x=0, y=0) for i in range(256)]
        )
        
        # Create mock progress
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1
        
        # Generate puzzle
        result = generator._generate_single_puzzle(
            "0001", tmp_path, 0.5, Mock(), mock_progress
        )
        
        assert result.status == PuzzleGenerationStatus.COMPLETED
        assert result.quality_metrics.overall_score == 85.0
        assert result.prompt == "test prompt"
    
    def test_generate_single_puzzle_quality_fail(self, mock_agents, tmp_path):
        """Test puzzle generation with quality failure"""
        generator = PuzzleGenerator()
        
        # Mock artisan
        generator.artisan.generate_prompt.return_value = "test prompt"
        generator.artisan.create_image.return_value = Mock(
            prompt="test prompt",
            image_data=b"fake_image_data"
        )
        
        # Mock guardian to fail quality check
        generator.guardian.evaluate.return_value = QualityMetrics(
            edge_density=5.0,
            color_entropy=2.0,
            local_contrast=10.0,
            overall_score=40.0  # Below threshold
        )
        
        # Create mock progress
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1
        
        # Generate puzzle
        result = generator._generate_single_puzzle(
            "0001", tmp_path, 0.5, Mock(), mock_progress
        )
        
        assert result.status == PuzzleGenerationStatus.FAILED
        assert "Quality score too low" in result.error_message
        assert result.quality_metrics.overall_score == 40.0
    
    def test_generate_puzzles_with_retries(self, mock_agents, tmp_path):
        """Test generating puzzles with quality rejections"""
        generator = PuzzleGenerator()
        
        # Mock console to avoid output
        generator.console = Mock()
        
        # Mock artisan
        generator.artisan.generate_prompt.return_value = "test prompt"
        generator.artisan.create_image.return_value = Mock(
            prompt="test prompt",
            image_data=b"fake_image_data"
        )
        
        # Mock guardian to fail first attempt, succeed second
        quality_scores = [40.0, 85.0]  # First fails, second passes
        generator.guardian.evaluate.side_effect = [
            QualityMetrics(
                edge_density=25.0,
                color_entropy=5.0,
                local_contrast=30.0,
                overall_score=score
            ) for score in quality_scores * 10  # Repeat pattern
        ]
        
        # Mock cutter
        generator.cutter.cut_puzzle.return_value = PuzzleManifest(
            size=2048,
            grid=(16, 16),
            pieces=[Mock(id=i, x=0, y=0) for i in range(256)]
        )
        
        # Generate 1 puzzle (should take 2 attempts)
        generator.generate_puzzles(1, str(tmp_path))
        
        assert generator.stats['attempts'] == 2
        assert generator.stats['accepted'] == 1
        assert generator.stats['rejected'] == 1