# Tessellate-AI Backend

AI-powered jigsaw puzzle generator that creates high-quality puzzles through an agent-based pipeline.

## Features

- **Prompt Artisan**: Generates optimized image prompts using DALL-E 3
- **Quality Guardian**: Evaluates images for puzzle suitability using computer vision
- **Digital Cutter**: Creates interlocking puzzle pieces with multiple cutting styles
- **Learning System**: Improves prompt generation based on solve-time feedback

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Basic Usage

Generate 20 puzzles with default settings:
```bash
python cli.py
```

### Advanced Options

```bash
# Generate 10 puzzles with high complexity
python cli.py --count 10 --complexity 0.8

# Use geometric cutting style
python cli.py --style geometric

# Custom output directory
python cli.py --output /path/to/puzzles

# Enable debug mode
python cli.py --debug
```

### Command Line Options

- `--count, -c`: Number of puzzles to generate (default: 20)
- `--output, -o`: Output directory (default: public/puzzles)
- `--complexity, -x`: Complexity level 0-1 (default: 0.5)
- `--style, -s`: Cutting style - classic/geometric/organic (default: classic)
- `--debug`: Enable debug logging

## Output Structure

Each generated puzzle creates a directory with:
```
public/puzzles/
└── 0001/
    ├── manifest.json      # Piece positions and grid info
    ├── metadata.json      # Generation details and quality metrics
    ├── original.jpg       # Full puzzle image
    └── piece_000.png      # Individual puzzle pieces (256 total)
        ...
        piece_255.png
```

## Quality Metrics

The Quality Guardian evaluates images based on:

- **Edge Density**: Percentage of edge pixels (Canny detection)
- **Color Entropy**: Variety in color distribution (HSV histogram)
- **Local Contrast**: Standard deviation of Sobel gradients
- **Overall Score**: Weighted combination (threshold: 80/100)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

## Architecture

The system uses an agent-based architecture where each agent has a single responsibility:

1. **Image Generation**: Prompt Artisan creates images optimized for puzzles
2. **Quality Control**: Quality Guardian ensures images meet puzzle standards
3. **Piece Creation**: Digital Cutter generates individual pieces with proper edges
4. **Orchestration**: CLI coordinates the pipeline and handles retries

## Environment Variables

See `.env.example` for all configuration options:

- `OPENAI_API_KEY`: Required for image generation
- `IMAGE_SIZE`: Puzzle image size (default: 2048)
- `GRID_ROWS/GRID_COLS`: Puzzle grid dimensions (default: 16x16)
- `QUALITY_THRESHOLD`: Minimum quality score (default: 30.0)