#!/usr/bin/env python3
"""
Alternative entry point for the refactored MyCobot320 Web Controller

Usage:
    python run.py          # Run with default config
    python src/main.py     # Direct execution
"""

import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from src.main import main

if __name__ == '__main__':
    main()