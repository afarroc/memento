"""Paquete memento - Cliente para proyectos externos.

Este paquete actúa como capa de inyección de dependencias, exponiendo
API cliente amigable que delega en core/ del repositorio mementobloom.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .references import client_context, project_meta_path, workspace_status

__all__ = ["client_context", "project_meta_path", "workspace_status"]