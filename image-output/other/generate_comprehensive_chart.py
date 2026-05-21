#!/usr/bin/env python3
"""Compatibility entrypoint for summary-driven thesis figures."""
import runpy
from pathlib import Path


runpy.run_path(str(Path(__file__).resolve().parents[1] / "generate_thesis_figures.py"), run_name="__main__")
