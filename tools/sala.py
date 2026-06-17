#!/usr/bin/env python3
import os
os.environ.setdefault('REDIS_HOST', '192.168.18.59')
os.environ.setdefault('REDIS_PORT', '6379')
os.environ.setdefault('REDIS_KEY', 'memento_panel_items')
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(ROOT / "sala.py"), run_name="__main__")
