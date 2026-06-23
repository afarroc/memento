from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
ENV_WORKSPACE = os.environ.get("MEMENTO_WORKSPACE")


def detect_workspace_root() -> Path:
    """Detecta la raíz del workspace sin depender de rutas absolutas hardcodeadas."""
    if ENV_WORKSPACE:
        return Path(ENV_WORKSPACE).expanduser().resolve()
    return ROOT.resolve()


def project_root() -> Path:
    return ROOT.resolve()


def workspace_root() -> Path:
    return detect_workspace_root()


def detect_project_name() -> str:
    ws = workspace_root()
    return ws.name


def rel(path: Path, base: Optional[Path] = None) -> str:
    base = (base or ROOT).resolve()
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return str(path)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
