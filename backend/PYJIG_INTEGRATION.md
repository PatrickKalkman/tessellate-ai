# PyJig Integration

## Overview
The backend now uses PyJig algorithm for generating jigsaw puzzle pieces with the CLASSIC cutting style. This provides more realistic-looking interlocking pieces compared to the previous custom implementation.

## Implementation Details

### New Files
- `backend/agents/pyjig_adapter.py` - PyJig implementation adapted from https://github.com/tomdeabreucodes/PyJig/

### Modified Files  
- `backend/agents/digital_cutter.py` - Updated to use PyJig for CLASSIC style pieces
- `backend/requirements.txt` - Added `svgpathtools>=1.6.0` dependency

### Key Changes
1. **PyJig Integration**: When using `CuttingStyle.CLASSIC`, the system now:
   - Uses PyJig to generate SVG-based puzzle pieces with realistic curves
   - Converts SVG pieces to PNG format for compatibility
   - Falls back to simple rectangular pieces if SVG conversion fails

2. **SVG to PNG Conversion**: Supports multiple converters in priority order:
   - CairoSVG (if installed with cairo library)
   - Wand/ImageMagick (if installed)
   - Inkscape command line (if available)
   - Fallback to simple rectangular pieces

3. **Backward Compatibility**: 
   - GEOMETRIC and ORGANIC cutting styles still use the original implementation
   - Output format remains the same (individual PNG pieces + manifest.json)
   - All existing tests pass

## Dependencies

### Required
- `svgpathtools>=1.6.0` - For SVG path manipulation

### Optional (for better SVG rendering)
- `cairosvg>=2.7.0` - Requires cairo library system dependency
- `Wand` - Requires ImageMagick system dependency  
- `inkscape` - Command line tool

## Usage
No changes to the API. Continue using the DigitalCutter as before:

```python
from backend.agents.digital_cutter import DigitalCutter
from backend.core.models import CuttingStyle

cutter = DigitalCutter()
manifest = cutter.cut_puzzle(
    image_path="puzzle.jpg",
    output_dir="output/",
    style=CuttingStyle.CLASSIC  # Now uses PyJig!
)
```

## Notes
- The PyJig algorithm generates more complex, realistic puzzle piece shapes
- Piece generation may be slightly slower due to SVG generation and conversion
- Without an SVG-to-PNG converter, pieces will be simple rectangles (functional but less aesthetic)