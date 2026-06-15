#!/usr/bin/env python3
"""Wrapper para iniciar la sala local desde tools/."""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(ROOT / "sala.py"), run_name="__main__")
