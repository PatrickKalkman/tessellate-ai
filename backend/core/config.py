from pathlib import Path
from typing import Tuple

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # Image Generation Settings
    image_width: int = Field(1792, env="IMAGE_WIDTH")
    image_height: int = Field(1024, env="IMAGE_HEIGHT")
    dalle_size: str = Field("1792x1024", env="DALLE_SIZE")  # DALL-E 3 image size
    grid_rows: int = Field(5, env="GRID_ROWS")  # Number of rows
    grid_cols: int = Field(9, env="GRID_COLS")  # Number of columns
    piece_size: int = Field(
        192, env="PIECE_SIZE"
    )  # Legacy - will be calculated dynamically

    # Quality Settings
    quality_threshold: float = Field(30.0, env="QUALITY_THRESHOLD")

    # Output Configuration
    output_dir: str = Field("../public/puzzles", env="OUTPUT_DIR")

    # Development Settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    @property
    def grid_size(self) -> Tuple[int, int]:
        return (self.grid_rows, self.grid_cols)

    @property
    def total_pieces(self) -> int:
        return self.grid_rows * self.grid_cols

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir).resolve()

    @property
    def image_size(self) -> Tuple[int, int]:
        """Return image dimensions as a tuple (width, height)"""
        return (self.image_width, self.image_height)

    @property
    def piece_width(self) -> int:
        """Calculate exact piece width based on image width and columns"""
        return self.image_width // self.grid_cols

    @property
    def piece_height(self) -> int:
        """Calculate exact piece height based on image height and rows"""
        return self.image_height // self.grid_rows

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()
