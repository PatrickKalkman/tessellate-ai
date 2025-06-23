#!/usr/bin/env python3
"""
Runner script for the CLI that can be executed directly.
This handles the import path setup properly.
"""

import sys
from pathlib import Path

# Add parent directory to path so imports work
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir.parent))

# Now we can import from backend as a package
from backend.cli import main

if __name__ == '__main__':
    main()