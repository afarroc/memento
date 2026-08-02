#!/usr/bin/env python3
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault('REDIS_HOST', 'localhost')
os.environ.setdefault('REDIS_PORT', '6379')
from core.paths import detect_project_name
os.environ.setdefault('REDIS_KEY', f"memento_panel_items:{detect_project_name()}")
import runpy
runpy.run_path(str(ROOT / "sala.py"), run_name="__main__")
