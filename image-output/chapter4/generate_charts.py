#!/usr/bin/env python3
"""Compatibility entrypoint for Chapter 4 architecture figures."""
import runpy
from pathlib import Path


runpy.run_path(str(Path(__file__).resolve().parents[1] / "generate_chapter4_architecture.py"), run_name="__main__")
