import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import load_index, top_entries


class ContextRetriever:
    def __init__(self, graph_index_path: Optional[str] = None):
        self.graph_index_path = graph_index_path

    def get_context(self, query: str, limit: int = 5) -> str:
        """Recupera contexto compacto para prompt."""
        entries = self._search(query, limit)
        return self._format_compact(entries)

    def _search(self, query: str, limit: int) -> List[Dict]:
        # Fallback controlado: devuelve entradas principales cuando no hay backend de búsqueda
        index = load_index()
        if not index:
            return []
        return top_entries(index, limit)

    def _format_compact(self, entries: List[Dict]) -> str:
        lines = ["# CONTEXT_COMPACT"]
        for e in entries:
            lines.append(
                f"- [{e.get('id','?')}] {e.get('type','?')} "
                f"project={e.get('project','?')} ts={e.get('ts','')} :: {e.get('summary','')[:100]}"
            )
        return "\n".join(lines)
