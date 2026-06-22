import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import load_index, top_entries, resolve_index_path


class ContextRetriever:
    def __init__(self, graph_index_path: Optional[str] = None, workspace: Optional[Path] = None):
        self._graph_index_path = graph_index_path
        self._workspace = workspace
        self._index = None
        self._index_path = None

    def _get_index(self) -> Dict[str, Dict]:
        """Get index from configured path or workspace."""
        if self._index is not None:
            return self._index
        index_path = resolve_index_path(self._graph_index_path, workspace=self._workspace)
        self._index_path = index_path
        return load_index(index_path)

    def get_context(self, query: str, limit: int = 5, project: Optional[str] = None) -> str:
        """Recupera contexto compacto para prompt."""
        entries = self._search(query, limit, project=project)
        return self._format_compact(entries)

    def _search(self, query: str, limit: int, project: Optional[str] = None) -> List[Dict]:
        """Búsqueda en el índice de memoria usando palabras clave y resúmenes.

        Estrategia simple de ranking sin embeddings:
        - Coincidencia exacta en palabras clave: +10 puntos
        - Coincidencia parcial en palabras clave: +5 puntos
        - Coincidencia en resumen (case-insensitive): +3 puntos
        - Coincidencia en project: +2 puntos
        - Reciente (por timestamp): +1 punto
        """
        index = self._get_index()
        if not index:
            return []

        query_lower = query.lower().strip()
        if not query_lower:
            return top_entries(index, limit, project=project)

        query_terms = set(query_lower.split())

        def score_entry(entry: Dict) -> float:
            score = 0.0

            # Score por palabras clave (formato: "kw1, kw2, kw3")
            keywords_str = str(entry.get("keywords", "") or "")
            keywords = set(kw.strip().lower() for kw in keywords_str.split(",") if kw.strip())
            exact_matches = query_terms & keywords
            partial_matches = sum(1 for term in query_terms if any(term in kw for kw in keywords))
            score += len(exact_matches) * 10 + (partial_matches - len(exact_matches)) * 5

            # Score por resumen
            summary = str(entry.get("summary", "")).lower()
            for term in query_terms:
                if term in summary:
                    score += 3

            # Score por proyecto
            if project and entry.get("project") == project:
                score += 2

            return score

        entries = list(index.values())
        if project:
            entries = [e for e in entries if str(e.get("project")) == project]

        scored = [(entry, score_entry(entry)) for entry in entries]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [entry for entry, _ in scored[:limit] if _ > 0]

    def _format_compact(self, entries: List[Dict]) -> str:
        lines = ["# CONTEXT_COMPACT"]
        for e in entries:
            lines.append(
                f"- [{e.get('id','?')}] {e.get('type','?')} "
                f"project={e.get('project','?')} ts={e.get('ts','')} :: {e.get('summary','')[:100]}"
            )
        return "\n".join(lines)
