#!/usr/bin/env python3
"""Context Builder - Autorreferencia desde índice compacto"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import re
try:
    from .optimize_memento import MementoOptimizer
except ImportError:
    from optimize_memento import MementoOptimizer


class ContextBuilder:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.index = self._load_index()
        self.optimizer = MementoOptimizer(str(self.index_path), backup=False)
    
    def _load_index(self) -> Dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {}

    def get_expanded_context(self, project: str = None, context_type: str = None, limit: int = 10) -> str:
        """Construye contexto autorreferencial expandido."""
        entries = self._filter_entries(project, context_type, limit)
        return self._format_context(entries)

    def search(self, query: str, limit: int = 10) -> str:
        """Busca entradas por relevancia y devuelve contexto compacto."""
        entries = self.optimizer.search(query, limit=limit)
        return self._format_context(entries)
    
    def _filter_entries(self, project: str, context_type: str, limit: int) -> List[Dict]:
        results = []
        for entry_id, entry in self.index.items():
            if project and context_type:
                if entry.get("project") != project or entry.get("type") != context_type:
                    continue
            elif project:
                if entry.get("project") != project:
                    continue
            elif context_type:
                if entry.get("type") != context_type:
                    continue
            results.append(entry)

        results.sort(key=lambda e: self._scored_entry(e), reverse=True)
        return results[:limit]

    def _scored_entry(self, entry: Dict) -> float:
        base = float(entry.get("score", 0))
        ts = str(entry.get("ts", ""))
        if ts and "2026-06-1" in ts and "unknown" not in ts:
            base += 0.1
        return base
    
    def _format_context(self, entries: List[Dict]) -> str:
        lines = ["# 🜄 MEMENTO CONTEXT // Ranked"]
        for e in entries:
            header = e.get("summary", "")[:120].replace("\n", " ")
            keywords = ", ".join(e.get("keywords", [])[:5])
            score = e.get("score", "?")
            lines.append(f"- [{e.get('id', '?')}] {e.get('type', '?')} :: {e.get('project', '?')} | {e.get('ts', '?')} | score={score} | {keywords} | {header}")
        return "\n".join(lines)
    
    def ready_check(self) -> Dict:
        """Verifica estado de expansión."""
        handoffs = sum(1 for e in self.index.values() if e["type"] == "HANDOFF")
        contexts = sum(1 for e in self.index.values() if e["type"] == "CONTEXT")
        return {"total": handoffs + contexts, "handoffs": handoffs, "contexts": contexts, "ready": True}

if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description="MementoBloom Context Builder")
    parser.add_argument("--ready", action="store_true", help="Show ready status only")
    parser.add_argument("--limit", type=int, default=20, help="Limit entries")
    args = parser.parse_args()

    ws_root = Path(__file__).resolve().parent.parent
    index_path = ws_root / "memory" / "graph" / "memory_index.json"

    cb = ContextBuilder(str(index_path))
    
    if args.ready:
        print(json.dumps(cb.ready_check(), indent=2))
    else:
        print(cb.get_expanded_context(limit=args.limit))
        print("\n---\n")
        print(json.dumps(cb.ready_check(), indent=2))