"""Referencias y wrappers de cliente - Inversión de control.

Este módulo expone una API cliente amigable que delega en core/ del
repositorio mementobloom, permitiendo que proyectos externos accedan
a funcionalidades sin acoplamiento directo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

MEMENTO_WORKSPACE = os.environ.get("MEMENTO_WORKSPACE")
SCRIPT_ROOT = Path(__file__).resolve().parent.parent

if MEMENTO_WORKSPACE:
    WS_ROOT = Path(MEMENTO_WORKSPACE).expanduser().resolve()
    MEMENTO_ROOT = WS_ROOT / "mementobloom"
else:
    WS_ROOT = SCRIPT_ROOT
    MEMENTO_ROOT = WS_ROOT

sys.path.insert(0, str(MEMENTO_ROOT))

__all__ = ["client_context", "project_meta_path", "workspace_status", "get_workspace_root"]


def _get_workspace_root() -> Path:
    """Obtiene el workspace raíz donde está instalado el cliente."""
    return WS_ROOT


def client_context(project_name: str | None = None) -> dict:
    """Genera contexto cliente para el proyecto activo.

    Args:
        project_name: Nombre del proyecto (por defecto, detecta del workspace)

    Returns:
        Diccionario con rutas y estado del contexto cliente
    """
    from core.index import default_index_path, load_index

    ws = _get_workspace_root()
    return {
        "project": project_name or ws.name,
        "workspace": str(ws),
        "memento_root": str(MEMENTO_ROOT),
        "index_path": str(default_index_path()),
        "index_entries": len(load_index()),
    }


def project_meta_path(project_name: str | None = None) -> Path:
    """Obtiene la ruta del PROJECT_META.md del cliente."""
    return _get_workspace_root() / ".agent_context" / "PROJECT_META.md"


def workspace_status() -> dict:
    """Obtiene estado del workspace cliente (Git, servicios)."""
    from core.git import git_status, latest_commit
    from core.services import service_status

    ws = _get_workspace_root()
    return {
        "git": {"status": git_status(root=ws), "latest": latest_commit(root=ws)},
        "services": service_status(fresh=True),
    }


def get_workspace_root() -> Path:
    """Alias público para _get_workspace_root."""
    return _get_workspace_root()