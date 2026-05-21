#!/usr/bin/env python3
"""Compatibility entrypoint.

The thesis experiment chapter is now numbered as Chapter 3. This wrapper keeps
the old script name usable while delegating to the summary-driven generator.
"""
import runpy
from pathlib import Path


runpy.run_path(str(Path(__file__).resolve().parents[1] / "generate_thesis_figures.py"), run_name="__main__")
