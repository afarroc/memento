from typing import Dict, List, Optional

class ContextRetriever:
    def __init__(self, graph_index_path: str):
        self.index_path = graph_index_path
    
    def get_context(self, query: str, limit: int = 5) -> str:
        """Recupera contexto compacto para prompt."""
        entries = self._search(query, limit)
        return self._format_compact(entries)
    
    def _search(self, query: str, limit: int) -> List[Dict]:
        # Placeholder - implementar búsqueda por relevancia
        return []
    
    def _format_compact(self, entries: List[Dict]) -> str:
        lines = ["# CONTEXT_COMPACT"]
        for e in entries:
            lines.append(f"- [{e.get('id','?')}] {e.get('ts','')} :: {e.get('summary','')[:100]}")
        return "\n".join(lines)