import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel

from ..core.config import settings
from ..core.models import ImageGenerationResult

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
        self.last_generated_prompts = []  # Track last few prompts in memory

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
            "field of wildflowers at golden hour",
            "Japanese zen garden with koi pond",
            "Victorian greenhouse with exotic plants",
            "Mediterranean coastal village at sunset",
            "African savanna with acacia trees",
            "colorful macaw parrots in jungle",
            "vintage train station in autumn",
            "lighthouse on rocky coastline during storm",
            "cherry blossoms in full bloom",
            "Venetian canal with gondolas",
            "desert canyon with layered rock formations",
            "butterfly garden with diverse species",
            "snowy owl in winter forest",
            "tide pools with starfish and anemones",
            "terraced rice fields at sunrise",
            "street art mural with vibrant colors",
        ]
        
        # Additional variation elements
        self.variation_elements = [
            "dramatic lighting",
            "morning mist",
            "golden sunbeams",
            "reflections in water",
            "interesting shadows",
            "natural patterns",
            "organic shapes",
            "flowing water",
            "dappled sunlight",
            "atmospheric perspective",
        ]

        # Complexity modifiers that affect puzzle difficulty
        self.complexity_modifiers = {
            "low": [
                "simple composition",
                "clear focal point",
                "distinct color regions",
            ],
            "medium": ["varied textures", "multiple subjects", "balanced composition"],
            "high": [
                "intricate details",
                "complex patterns",
                "high texture density",
                "asymmetrical composition",
            ],
        }

    def _load_history(self) -> List[PromptHistory]:
        """Load prompt history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                return [PromptHistory(**item) for item in data]
            except Exception as e:
                logger.warning(f"Failed to load prompt history: {e}")
        return []

    def _save_history(self):
        """Save prompt history to file"""
        try:
            data = [
                h.model_dump(mode="json") for h in self.prompt_history[-100:]
            ]  # Keep last 100
            with open(self.history_file, "w") as f:
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
        # Get recent prompts to avoid duplicates
        recent_prompts = self._get_recent_prompts(hours=24)
        recent_themes = [self._extract_theme(p) for p in recent_prompts]
        
        # Select a theme that hasn't been used recently
        available_themes = [t for t in self.base_themes if t not in recent_themes]
        if not available_themes:
            # If all themes used recently, use all themes but prefer less used ones
            theme_counts = {theme: recent_themes.count(theme) for theme in self.base_themes}
            least_used = min(theme_counts.values())
            available_themes = [t for t, count in theme_counts.items() if count == least_used]
        
        theme = random.choice(available_themes)

        # Determine complexity modifiers based on level
        modifiers = []
        if complexity_level < 0.33:
            modifiers = random.sample(self.complexity_modifiers["low"], 2)
        elif complexity_level < 0.66:
            modifiers = random.sample(self.complexity_modifiers["medium"], 2)
        else:
            modifiers = random.sample(self.complexity_modifiers["high"], 3)

        # Add random variation element
        variation = random.choice(self.variation_elements)
        
        # Build the prompt
        prompt_parts = [
            "Ultra-realistic photograph",
            theme,
            *modifiers,
            variation,
            "professional lighting",
            "8K resolution",
            "sharp focus",
        ]

        prompt = ", ".join(prompt_parts)

        # Add successful patterns from history
        if self.prompt_history:
            successful_prompts = [
                h for h in self.prompt_history if h.success and h.complexity_score > 0.7
            ]
            if (
                successful_prompts and random.random() < 0.3
            ):  # 30% chance to use learned patterns
                # Extract common successful patterns
                learned_modifier = self._extract_successful_patterns(successful_prompts)
                if learned_modifier:
                    prompt += f", {learned_modifier}"

        # Check if this exact prompt was recently generated
        if prompt in self.last_generated_prompts:
            # Add more variation to make it unique
            extra_variations = ["subtle details", "high contrast", "soft focus background", "macro details"]
            prompt += f", {random.choice(extra_variations)}"
        
        # Track this prompt
        self.last_generated_prompts.append(prompt)
        if len(self.last_generated_prompts) > 10:
            self.last_generated_prompts.pop(0)

        logger.info(
            f"Generated prompt with complexity {complexity_level}: {prompt[:100]}..."
        )
        return prompt

    def _extract_successful_patterns(
        self, successful_prompts: List[PromptHistory]
    ) -> Optional[str]:
        """Extract common patterns from successful prompts"""
        # This is a simplified version - in production, you might use NLP techniques
        common_words = [
            "vibrant colors",
            "rich textures",
            "natural lighting",
            "detailed foreground",
        ]
        return random.choice(common_words)
    
    def _get_recent_prompts(self, hours: int = 24) -> List[str]:
        """Get prompts generated in the last N hours"""
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for entry in self.prompt_history:
            # Parse timestamp if it's a string
            if isinstance(entry.timestamp, str):
                timestamp = datetime.fromisoformat(entry.timestamp)
            else:
                timestamp = entry.timestamp
                
            if timestamp > cutoff_time:
                recent.append(entry.prompt)
                
        return recent
    
    def _extract_theme(self, prompt: str) -> Optional[str]:
        """Extract the base theme from a generated prompt"""
        # Look for themes in the prompt
        prompt_lower = prompt.lower()
        
        for theme in self.base_themes:
            if theme.lower() in prompt_lower:
                return theme
                
        return None

    def create_image(
        self, prompt: str, size: Optional[str] = None
    ) -> ImageGenerationResult:
        """
        Generate an image using DALL-E 3

        Args:
            prompt: The prompt to generate from
            size: Image size (1792x1024, 1024x1024, or 1024x1792) - defaults to config.dalle_size

        Returns:
            ImageGenerationResult with image data
        """
        try:
            # Use configured size if not specified
            if size is None:
                size = settings.dalle_size
                
            logger.info(f"Generating image with DALL-E 3 at size {size}...")

            response = self.client.images.generate(
                model="dall-e-3", prompt=prompt, size=size, quality="hd", n=1
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
                success=True,
            )
            self.prompt_history.append(history_entry)
            self._save_history()

            return ImageGenerationResult(
                prompt=prompt, image_data=image_response.content, model="dall-e-3"
            )

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            # Record failure
            history_entry = PromptHistory(
                prompt=prompt, complexity_score=0.0, success=False
            )
            self.prompt_history.append(history_entry)
            self._save_history()
            raise

    def _estimate_complexity(self, prompt: str) -> float:
        """Estimate complexity score based on prompt content"""
        score = 0.5  # Base score

        # Check for complexity indicators
        high_complexity_words = [
            "intricate",
            "complex",
            "detailed",
            "asymmetrical",
            "dense",
        ]
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
                logger.info(
                    f"Updated prompt feedback: {solve_time_seconds}s solve time"
                )
                break
