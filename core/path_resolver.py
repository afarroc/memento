"""Resolvedor de rutas único para MementoBloom."""
from pathlib import Path
import os


class PathResolver:
    def __init__(self):
        # ROOT: siempre el directorio del código fuente
        self.ROOT = Path(__file__).resolve().parent.parent

        # WS_ROOT: por env var, o detectar hacia arriba
        env_workspace = os.environ.get("MEMENTO_WORKSPACE")
        if env_workspace:
            self.WS_ROOT = Path(env_workspace).expanduser().resolve()
        else:
            # Buscar hacia arriba .agent_context o projects/
            current = Path.cwd().resolve()
            for parent in [current] + list(current.parents):
                if (parent / ".agent_context").exists() or (parent / "projects").exists():
                    self.WS_ROOT = parent
                    break
            else:
                # Fallback: asumir que WS_ROOT es el padre del ROOT
                self.WS_ROOT = self.ROOT.parent

        # Determinar modo
        self.MODO = "dev" if self.ROOT == self.WS_ROOT else "instalado"

    def get_handoff_path(self, project_name: str, filename: str) -> Path:
        """Retorna el path correcto para un handoff."""
        if project_name == "mementobloom" and self.MODO == "dev":
            # En modo dev, mementobloom NO es un proyecto cliente
            # Los handoffs de mementobloom van en projects/mementobloom/
            # PERO se resuelven contra WS_ROOT (que == ROOT en dev)
            return self.WS_ROOT / "projects" / project_name / filename
        elif project_name == "mementobloom" and self.MODO == "instalado":
            # En modo instalado, mementobloom es un proyecto más del cliente
            return self.WS_ROOT / "projects" / project_name / filename
        else:
            # Cualquier otro proyecto cliente
            return self.WS_ROOT / "projects" / project_name / filename

    def resolve_path(self, path: str) -> Path:
        """Resuelve un path relativo contra WS_ROOT."""
        return self.WS_ROOT / path


RESOLVER = PathResolver()
