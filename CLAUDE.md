# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tessellate-AI is a self-improving jigsaw puzzle generation system that combines AI agents to create, evaluate, and serve digital jigsaw puzzles. The project demonstrates an agent-based architecture where each component has a single responsibility in the puzzle creation pipeline.

## Architecture

The system consists of four main agents working in a pipeline:

1. **Prompt Artisan** - Generates image prompts optimized for puzzle creation
2. **Quality Guardian** - Evaluates images for "puzzleability" using computer vision metrics
3. **Digital Cutter** - Slices approved images into unique, interlocking pieces
4. **Experience Orchestrator** - Manages the frontend game and collects telemetry

## Technology Stack

### Frontend (Planned)
- React 18 + Next.js 14 (static export)
- Konva.js for canvas-based puzzle interaction
- Lazy-loading for puzzle pieces
- Local Storage for optional save states

### Backend (Implemented)
- Python CLI for asset generation
- OpenAI API for image generation via DALL-E 3
- OpenCV and NumPy for image quality analysis
- Pillow for image processing and piece generation
- Rich terminal UI with progress tracking

## Development Commands

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Puzzle Generation
```bash
# Recommended: From project root using module
python -m backend --count 20

# Alternative: Using runner script from backend directory
cd backend
python run.py --count 20

# Generate 10 puzzles with high complexity
python -m backend --count 10 --complexity 0.8

# Use different cutting styles
python -m backend --style geometric
python -m backend --style organic

# Custom output directory
python -m backend --output /path/to/puzzles

# Enable debug mode
python -m backend --debug
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_quality_guardian.py -v
```

### Frontend Development
```bash
# Install dependencies (when package.json exists)
npm install

# Run development server
npm run dev

# Build static export
npm run build
npm run export

# Run tests (when implemented)
npm test
```

## Key Design Decisions

1. **45-piece puzzles** in v1 (5x9 grid with 192px pieces)
2. **No piece rotation** - pieces are always upright
3. **Static site architecture** - all assets pre-generated
4. **Lazy loading** - pieces fetched on demand
5. **Quality threshold of 30/100** - images below this score are rejected

## Asset Structure

```
/public/puzzles/
   0001/
       manifest.json          // piece coordinates
       metadata.json          // generation details and quality scores
       original.jpg           // full puzzle image
       piece_000.png ... piece_255.png  // 128x128 transparent PNGs
```

## Quality Metrics

The Quality Guardian evaluates images based on:
- **Edge density**: Canny edge detection / pixel count
- **Color entropy**: Shannon entropy over 32-bin HSV histogram  
- **Local contrast**: Standard deviation of Sobel magnitude

## Future Extensibility

The v1 design includes hooks for:
- Variable piece counts (parameterized grid size)
- Tablet/multitouch support (Konva pinch-zoom ready)
- User accounts (telemetry endpoint abstracted)
- User-generated prompts (CLI logic extractable to microservice)
- CDN deployment (configurable asset base URL)