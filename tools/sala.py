#!/usr/bin/env python3
import os
os.environ.setdefault('REDIS_HOST', 'localhost')
os.environ.setdefault('REDIS_PORT', '6379')
from core.paths import detect_project_name
os.environ.setdefault('REDIS_KEY', f"memento_panel_items:{detect_project_name()}")
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(ROOT / "sala.py"), run_name="__main__")
