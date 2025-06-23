#!/usr/bin/env python3
"""
Main entry point for Tessellate-AI puzzle generation.
Run this script from the project root directory.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import and run the CLI
from cli import main

if __name__ == '__main__':
    main()