# Backend Puzzle Generator Factory - Implementation Plan

## Overview
Build a Python CLI that generates high-quality jigsaw puzzles through an agent-based pipeline. Each agent has a single responsibility and contributes to creating puzzles that are both visually appealing and satisfying to solve.

## Project Structure
```
tessellate-ai/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── prompt_artisan.py
│   │   ├── quality_guardian.py
│   │   └── digital_cutter.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── utils.py
│   ├── cli.py
│   ├── requirements.txt
│   └── .env.example
├── tests/
│   ├── __init__.py
│   ├── test_prompt_artisan.py
│   ├── test_quality_guardian.py
│   └── test_digital_cutter.py
└── public/
    └── puzzles/
```

## Phase 1: Environment Setup (Day 1)

### 1.1 Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Core dependencies
pip install pillow opencv-python numpy
pip install openai python-dotenv
pip install click rich  # CLI tools
pip install svgwrite cairosvg  # For piece generation
pip install pytest pytest-cov  # Testing
```

### 1.2 Configuration Module
```python
# backend/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    image_size: int = 2048
    grid_size: tuple = (16, 16)
    piece_size: int = 128
    quality_threshold: float = 80.0
    output_dir: str = "public/puzzles"
    
    class Config:
        env_file = ".env"
```

### 1.3 Data Models
```python
# backend/core/models.py
from pydantic import BaseModel
from typing import List, Tuple

class PuzzlePiece(BaseModel):
    id: int
    x: int
    y: int
    
class PuzzleManifest(BaseModel):
    size: int
    grid: Tuple[int, int]
    pieces: List[PuzzlePiece]

class QualityMetrics(BaseModel):
    edge_density: float
    color_entropy: float
    local_contrast: float
    overall_score: float
```

## Phase 2: Prompt Artisan Agent (Day 2)

### 2.1 Core Implementation
```python
# backend/agents/prompt_artisan.py
class PromptArtisan:
    def __init__(self, openai_client):
        self.client = openai_client
        self.base_themes = [
            "wildlife photograph",
            "underwater scene",
            "mountain landscape",
            "forest path",
            "coral reef"
        ]
        
    def generate_prompt(self, complexity_level: float = 0.5):
        """Generate optimized puzzle prompt based on learned complexity"""
        # Start with base theme
        # Add complexity modifiers based on feedback
        # Return enhanced prompt
        
    def create_image(self, prompt: str) -> bytes:
        """Generate image using DALL-E 3"""
        # Call OpenAI API
        # Return image bytes
```

### 2.2 Learning Mechanism
- Track successful puzzle prompts
- Store complexity modifiers that work well
- Evolve prompts based on solve time feedback

## Phase 3: Quality Guardian Agent (Day 3-4)

### 3.1 Computer Vision Metrics
```python
# backend/agents/quality_guardian.py
class QualityGuardian:
    def __init__(self, threshold: float = 80.0):
        self.threshold = threshold
        
    def calculate_edge_density(self, image: np.ndarray) -> float:
        """Canny edge detection metric"""
        # Convert to grayscale
        # Apply Canny edge detection
        # Calculate edge pixel ratio
        
    def calculate_color_entropy(self, image: np.ndarray) -> float:
        """Shannon entropy of color distribution"""
        # Convert to HSV
        # Create 32-bin histogram
        # Calculate Shannon entropy
        
    def calculate_local_contrast(self, image: np.ndarray) -> float:
        """Standard deviation of Sobel magnitude"""
        # Apply Sobel filter
        # Calculate magnitude
        # Return std deviation
        
    def evaluate(self, image_path: str) -> QualityMetrics:
        """Comprehensive quality assessment"""
        # Load image
        # Calculate all metrics
        # Compute weighted score
        # Return pass/fail with metrics
```

### 3.2 Rejection Criteria
- Vast single-color areas (>40% of image)
- Insufficient edge density (<10%)
- Low color variety (entropy < 4.0)
- Poor local contrast (std dev < 20)

## Phase 4: Digital Cutter Agent (Day 5-6)

### 4.1 Piece Generation Algorithm
```python
# backend/agents/digital_cutter.py
class DigitalCutter:
    def __init__(self, grid_size=(16, 16)):
        self.rows, self.cols = grid_size
        
    def generate_bezier_path(self, x, y, neighbors):
        """Create unique interlocking piece shape"""
        # Define control points
        # Add perturbation for uniqueness
        # Generate SVG path
        
    def create_piece_mask(self, image, path, piece_id):
        """Extract piece from full image"""
        # Create mask from SVG path
        # Apply mask to image region
        # Resize to 128x128
        # Save as PNG with transparency
        
    def cut_puzzle(self, image_path: str, output_dir: str):
        """Generate all puzzle pieces"""
        # Load full image
        # For each grid position:
        #   - Generate unique path
        #   - Create masked piece
        #   - Save to output_dir
```

### 4.2 Cutting Styles
- Classic: Traditional jigsaw curves
- Geometric: Angular, modern cuts
- Organic: Nature-inspired irregular shapes

## Phase 5: CLI Orchestrator (Day 7)

### 5.1 Main Pipeline
```python
# backend/cli.py
@click.command()
@click.option('--count', default=20, help='Number of puzzles to generate')
@click.option('--output', default='public/puzzles', help='Output directory')
def generate_puzzles(count, output):
    """Generate high-quality jigsaw puzzles"""
    
    # Initialize agents
    artisan = PromptArtisan(openai_client)
    guardian = QualityGuardian()
    cutter = DigitalCutter()
    
    puzzles_created = 0
    attempts = 0
    
    while puzzles_created < count:
        # Generate prompt and image
        prompt = artisan.generate_prompt()
        image = artisan.create_image(prompt)
        
        # Quality check
        metrics = guardian.evaluate(image)
        if metrics.overall_score < 80:
            continue
            
        # Cut into pieces
        puzzle_id = f"{puzzles_created:04d}"
        puzzle_dir = os.path.join(output, puzzle_id)
        cutter.cut_puzzle(image, puzzle_dir)
        
        # Create manifest
        create_manifest(puzzle_dir)
        
        puzzles_created += 1
```

### 5.2 Progress Tracking
- Use `rich` library for beautiful CLI output
- Show real-time metrics
- Display rejection reasons
- Estimate time remaining

## Phase 6: Testing & Refinement (Day 8)

### 6.1 Unit Tests
```python
# tests/test_quality_guardian.py
def test_edge_density_calculation():
    # Test with known images
    # Verify metric accuracy

def test_quality_threshold():
    # Test acceptance/rejection
    # Verify threshold behavior
```

### 6.2 Integration Tests
- End-to-end puzzle generation
- Asset validation
- Performance benchmarks

## Deliverables

1. **Working CLI**: `python backend/cli.py --count 20`
2. **20 High-Quality Puzzles**: Ready for frontend
3. **Comprehensive Tests**: >80% coverage
4. **Documentation**: Usage guide and API docs
5. **Metrics Dashboard**: Quality statistics and insights

## Success Metrics

- Generation success rate >40%
- Average quality score >85
- Piece generation time <2s per puzzle
- All pieces properly masked with transparency
- Manifest files valid JSON

## Future Enhancements

1. **Feedback Loop**: Integrate solve-time data to improve prompts
2. **Parallel Processing**: Multi-threaded piece generation
3. **Style Transfer**: Apply artistic styles to generated images
4. **Difficulty Levels**: Variable piece counts and complexity
5. **API Service**: RESTful API for on-demand generation