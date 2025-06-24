from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from datetime import datetime
from enum import Enum


class PuzzlePiece(BaseModel):
    id: int
    x: int
    y: int


class PuzzleManifest(BaseModel):
    width: int
    height: int
    grid: Tuple[int, int]
    pieces: List[PuzzlePiece]
    
    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "width": self.width,
            "height": self.height,
            "grid": list(self.grid),
            "pieces": [piece.model_dump() for piece in self.pieces]
        }


class QualityMetrics(BaseModel):
    edge_density: float = Field(..., ge=0, le=100)
    color_entropy: float = Field(..., ge=0, le=10)
    local_contrast: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    
    def passes_threshold(self, threshold: float) -> bool:
        return self.overall_score >= threshold


class ImageGenerationResult(BaseModel):
    prompt: str
    image_data: bytes
    timestamp: datetime = Field(default_factory=datetime.now)
    model: str = "dall-e-3"


class PuzzleGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING_IMAGE = "generating_image"
    QUALITY_CHECK = "quality_check"
    CUTTING_PIECES = "cutting_pieces"
    COMPLETED = "completed"
    FAILED = "failed"


class PuzzleGenerationResult(BaseModel):
    puzzle_id: str
    status: PuzzleGenerationStatus
    prompt: str
    quality_metrics: Optional[QualityMetrics] = None
    error_message: Optional[str] = None
    attempts: int = 1
    timestamp: datetime = Field(default_factory=datetime.now)


class CuttingStyle(str, Enum):
    CLASSIC = "classic"
    GEOMETRIC = "geometric"
    ORGANIC = "organic"