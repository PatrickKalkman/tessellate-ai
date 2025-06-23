import random
import logging
from typing import Optional, List, Dict
from datetime import datetime
import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel

from ..core.models import ImageGenerationResult
from ..core.config import settings


logger = logging.getLogger(__name__)


class PromptHistory(BaseModel):
    prompt: str
    complexity_score: float
    solve_time_seconds: Optional[float] = None
    success: bool = True
    timestamp: datetime = datetime.now()


class PromptArtisan:
    """Agent responsible for generating optimized prompts and images for puzzles"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI(api_key=settings.openai_api_key)
        self.history_file = Path("prompt_history.json")
        self.prompt_history: List[PromptHistory] = self._load_history()
        
        # Base themes for puzzle generation
        self.base_themes = [
            "vibrant coral reef with exotic fish",
            "misty mountain landscape at sunrise",
            "dense rainforest canopy with wildlife",
            "underwater shipwreck with marine life",
            "autumn forest path with fallen leaves",
            "tropical beach with crystal clear water",
            "northern lights over snowy mountains",
            "bustling farmer's market with colorful produce",
            "hot air balloons over countryside",
            "field of wildflowers at golden hour"
        ]
        
        # Complexity modifiers that affect puzzle difficulty
        self.complexity_modifiers = {
            "low": [
                "simple composition",
                "clear focal point",
                "distinct color regions"
            ],
            "medium": [
                "varied textures",
                "multiple subjects",
                "balanced composition"
            ],
            "high": [
                "intricate details",
                "complex patterns",
                "high texture density",
                "asymmetrical composition"
            ]
        }
        
    def _load_history(self) -> List[PromptHistory]:
        """Load prompt history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                return [PromptHistory(**item) for item in data]
            except Exception as e:
                logger.warning(f"Failed to load prompt history: {e}")
        return []
    
    def _save_history(self):
        """Save prompt history to file"""
        try:
            data = [h.model_dump(mode='json') for h in self.prompt_history[-100:]]  # Keep last 100
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save prompt history: {e}")
    
    def generate_prompt(self, complexity_level: float = 0.5) -> str:
        """
        Generate an optimized puzzle prompt based on complexity level.
        
        Args:
            complexity_level: Float between 0 and 1, where 0 is simplest and 1 is most complex
            
        Returns:
            Generated prompt string
        """
        # Select random base theme
        theme = random.choice(self.base_themes)
        
        # Determine complexity modifiers based on level
        modifiers = []
        if complexity_level < 0.33:
            modifiers = random.sample(self.complexity_modifiers["low"], 2)
        elif complexity_level < 0.66:
            modifiers = random.sample(self.complexity_modifiers["medium"], 2)
        else:
            modifiers = random.sample(self.complexity_modifiers["high"], 3)
        
        # Build the prompt
        prompt_parts = [
            "Ultra-realistic photograph",
            theme,
            *modifiers,
            "professional lighting",
            "8K resolution",
            "sharp focus",
            "suitable for jigsaw puzzle"
        ]
        
        prompt = ", ".join(prompt_parts)
        
        # Add successful patterns from history
        if self.prompt_history:
            successful_prompts = [h for h in self.prompt_history if h.success and h.complexity_score > 0.7]
            if successful_prompts and random.random() < 0.3:  # 30% chance to use learned patterns
                # Extract common successful patterns
                learned_modifier = self._extract_successful_patterns(successful_prompts)
                if learned_modifier:
                    prompt += f", {learned_modifier}"
        
        logger.info(f"Generated prompt with complexity {complexity_level}: {prompt[:100]}...")
        return prompt
    
    def _extract_successful_patterns(self, successful_prompts: List[PromptHistory]) -> Optional[str]:
        """Extract common patterns from successful prompts"""
        # This is a simplified version - in production, you might use NLP techniques
        common_words = ["vibrant colors", "rich textures", "natural lighting", "detailed foreground"]
        return random.choice(common_words)
    
    def create_image(self, prompt: str, size: str = "1024x1024") -> ImageGenerationResult:
        """
        Generate an image using DALL-E 3
        
        Args:
            prompt: The prompt to generate from
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            
        Returns:
            ImageGenerationResult with image data
        """
        try:
            logger.info("Generating image with DALL-E 3...")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="hd",
                n=1
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            import requests
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Record in history
            history_entry = PromptHistory(
                prompt=prompt,
                complexity_score=self._estimate_complexity(prompt),
                success=True
            )
            self.prompt_history.append(history_entry)
            self._save_history()
            
            return ImageGenerationResult(
                prompt=prompt,
                image_data=image_response.content,
                model="dall-e-3"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            # Record failure
            history_entry = PromptHistory(
                prompt=prompt,
                complexity_score=0.0,
                success=False
            )
            self.prompt_history.append(history_entry)
            self._save_history()
            raise
    
    def _estimate_complexity(self, prompt: str) -> float:
        """Estimate complexity score based on prompt content"""
        score = 0.5  # Base score
        
        # Check for complexity indicators
        high_complexity_words = ["intricate", "complex", "detailed", "asymmetrical", "dense"]
        low_complexity_words = ["simple", "clear", "minimal", "basic"]
        
        prompt_lower = prompt.lower()
        
        for word in high_complexity_words:
            if word in prompt_lower:
                score += 0.1
                
        for word in low_complexity_words:
            if word in prompt_lower:
                score -= 0.1
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))
    
    def update_feedback(self, prompt: str, solve_time_seconds: float):
        """
        Update prompt history with user feedback (solve time)
        
        Args:
            prompt: The prompt that was used
            solve_time_seconds: How long it took to solve the puzzle
        """
        # Find the matching prompt in history
        for entry in reversed(self.prompt_history):
            if entry.prompt == prompt and entry.solve_time_seconds is None:
                entry.solve_time_seconds = solve_time_seconds
                self._save_history()
                logger.info(f"Updated prompt feedback: {solve_time_seconds}s solve time")
                break