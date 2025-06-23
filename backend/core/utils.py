import json
import logging
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

# Initialize rich console
console = Console()


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("tessellate-ai")


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if not"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: dict, filepath: Union[str, Path]) -> None:
    """Save dictionary to JSON file"""
    filepath = Path(filepath)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_image(filepath: Union[str, Path]) -> Image.Image:
    """Load an image file"""
    return Image.open(filepath)


def save_image(image: Image.Image, filepath: Union[str, Path]) -> None:
    """Save an image file"""
    filepath = Path(filepath)
    image.save(filepath)


def image_to_array(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array"""
    return np.array(image)


def array_to_image(array: np.ndarray) -> Image.Image:
    """Convert numpy array to PIL Image"""
    return Image.fromarray(array.astype(np.uint8))


def create_progress_bar() -> Progress:
    """Create a rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )


def format_puzzle_id(index: int) -> str:
    """Format puzzle ID with zero padding"""
    return f"{index:04d}"


def calculate_piece_position(
    piece_index: int, grid_cols: int, piece_size: int
) -> tuple[int, int]:
    """Calculate the x, y position of a piece based on its index"""
    row = piece_index // grid_cols
    col = piece_index % grid_cols
    x = col * piece_size
    y = row * piece_size
    return x, y


def validate_image_size(image: Image.Image, expected_size: int) -> bool:
    """Validate that image is square and matches expected size"""
    width, height = image.size
    return width == height == expected_size


def resize_image_if_needed(image: Image.Image, target_size: int) -> Image.Image:
    """Resize image to target size if needed"""
    if image.size != (target_size, target_size):
        return image.resize((target_size, target_size), Image.Resampling.LANCZOS)
    return image
