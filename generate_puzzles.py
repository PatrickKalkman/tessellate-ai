#!/usr/bin/env python3
"""
Main entry point for Tessellate-AI puzzle generation.
Run this script from the project root directory.
"""

import sys
import subprocess
from pathlib import Path

if __name__ == '__main__':
    # Run the backend module with the provided arguments
    subprocess.run([sys.executable, '-m', 'backend'] + sys.argv[1:])