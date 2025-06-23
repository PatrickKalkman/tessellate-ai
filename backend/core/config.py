from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Tuple
import os
from pathlib import Path


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Image Generation Settings
    image_size: int = Field(2048, env="IMAGE_SIZE")
    grid_rows: int = Field(16, env="GRID_ROWS")
    grid_cols: int = Field(16, env="GRID_COLS")
    piece_size: int = Field(128, env="PIECE_SIZE")
    
    # Quality Settings
    quality_threshold: float = Field(80.0, env="QUALITY_THRESHOLD")
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()