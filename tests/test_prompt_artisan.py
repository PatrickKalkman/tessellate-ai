import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from backend.agents.prompt_artisan import PromptArtisan, PromptHistory
from backend.core.models import ImageGenerationResult


class TestPromptArtisan:
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client"""
        client = Mock()
        return client
    
    @pytest.fixture
    def prompt_artisan(self, mock_openai_client, tmp_path):
        """Create a PromptArtisan instance with mocked dependencies"""
        with patch('backend.agents.prompt_artisan.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            artisan = PromptArtisan(openai_client=mock_openai_client)
            artisan.history_file = tmp_path / "test_history.json"
            return artisan
    
    def test_generate_prompt_low_complexity(self, prompt_artisan):
        """Test prompt generation with low complexity"""
        prompt = prompt_artisan.generate_prompt(complexity_level=0.2)
        
        assert isinstance(prompt, str)
        assert "Ultra-realistic photograph" in prompt
        assert any(theme in prompt for theme in prompt_artisan.base_themes)
        # Should contain low complexity modifiers
        assert any(mod in prompt for mod in ["simple composition", "clear focal point", "distinct color regions"])
    
    def test_generate_prompt_high_complexity(self, prompt_artisan):
        """Test prompt generation with high complexity"""
        prompt = prompt_artisan.generate_prompt(complexity_level=0.8)
        
        assert isinstance(prompt, str)
        assert "Ultra-realistic photograph" in prompt
        # Should contain high complexity modifiers
        assert any(mod in prompt for mod in ["intricate details", "complex patterns", "high texture density"])
    
    def test_create_image_success(self, prompt_artisan, mock_openai_client):
        """Test successful image creation"""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(url="https://example.com/image.png")]
        mock_openai_client.images.generate.return_value = mock_response
        
        # Mock requests.get
        with patch('backend.agents.prompt_artisan.requests.get') as mock_get:
            mock_get.return_value.content = b"fake_image_data"
            mock_get.return_value.raise_for_status = Mock()
            
            result = prompt_artisan.create_image("test prompt")
            
            assert isinstance(result, ImageGenerationResult)
            assert result.prompt == "test prompt"
            assert result.image_data == b"fake_image_data"
            assert result.model == "dall-e-3"
            
            # Verify OpenAI was called correctly
            mock_openai_client.images.generate.assert_called_once_with(
                model="dall-e-3",
                prompt="test prompt",
                size="1024x1024",
                quality="hd",
                n=1
            )
    
    def test_create_image_failure(self, prompt_artisan, mock_openai_client):
        """Test image creation failure handling"""
        # Mock OpenAI to raise an exception
        mock_openai_client.images.generate.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            prompt_artisan.create_image("test prompt")
        
        # Verify failure was recorded in history
        assert len(prompt_artisan.prompt_history) == 1
        assert not prompt_artisan.prompt_history[0].success
    
    def test_estimate_complexity(self, prompt_artisan):
        """Test complexity estimation"""
        # High complexity prompt
        high_prompt = "intricate details with complex patterns"
        assert prompt_artisan._estimate_complexity(high_prompt) > 0.5
        
        # Low complexity prompt  
        low_prompt = "simple and clear minimal design"
        assert prompt_artisan._estimate_complexity(low_prompt) < 0.5
        
        # Neutral prompt
        neutral_prompt = "beautiful landscape photography"
        assert 0.4 <= prompt_artisan._estimate_complexity(neutral_prompt) <= 0.6
    
    def test_update_feedback(self, prompt_artisan):
        """Test updating prompt with feedback"""
        # Add a prompt to history
        prompt = "test prompt for feedback"
        prompt_artisan.prompt_history.append(
            PromptHistory(prompt=prompt, complexity_score=0.5, success=True)
        )
        
        # Update with feedback
        prompt_artisan.update_feedback(prompt, 120.5)
        
        # Verify feedback was recorded
        assert prompt_artisan.prompt_history[-1].solve_time_seconds == 120.5
    
    def test_load_save_history(self, prompt_artisan, tmp_path):
        """Test loading and saving prompt history"""
        # Add some history
        prompt_artisan.prompt_history = [
            PromptHistory(prompt="prompt1", complexity_score=0.3, success=True),
            PromptHistory(prompt="prompt2", complexity_score=0.7, success=True, solve_time_seconds=100)
        ]
        
        # Save history
        prompt_artisan._save_history()
        
        # Create new instance and load history
        new_artisan = PromptArtisan(openai_client=Mock())
        new_artisan.history_file = prompt_artisan.history_file
        loaded_history = new_artisan._load_history()
        
        assert len(loaded_history) == 2
        assert loaded_history[0].prompt == "prompt1"
        assert loaded_history[1].solve_time_seconds == 100
