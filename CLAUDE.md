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

### Backend (Planned)
- Python CLI for asset generation
- OpenAI API for image generation
- OpenCV and NumPy for image quality analysis
- Pillow for image processing

## Development Commands

Since this is a new project without implementation yet, here are the planned commands based on the specification:

### Python Asset Factory
```bash
# Generate puzzle assets (planned)
python cli/generate_puzzles.py --count 20 --output public/puzzles/

# Test image quality metrics
python cli/test_quality.py --image path/to/test.jpg
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

1. **256-piece puzzles only** in v1 (16x16 grid)
2. **No piece rotation** - pieces are always upright
3. **Static site architecture** - all assets pre-generated
4. **Lazy loading** - pieces fetched on demand
5. **Quality threshold of 80/100** - images below this score are rejected

## Asset Structure

```
/public/puzzles/
   0001/
       manifest.json          // piece coordinates
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