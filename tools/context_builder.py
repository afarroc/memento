#!/usr/bin/env python3
"""Context Builder - Autorreferencia desde índice compacto"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re
from datetime import datetime as _dt_mod
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.index import parse_ts

_DT_MIN = _dt_mod.min
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
            if not isinstance(entry, dict):
                continue
            # Skip external entries (unavailable in this workspace)
            if entry.get("external"):
                continue
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
        """Ranking: recencia manda, luego identidad válida y tipo HANDOFF.

        Antes solo daba +0.1 a entradas con ts en junio-2026 (ventana
        hardcoded): los 221 handoffs de sep-oct 2026 empataban en 0 y el
        orden era el de inserción del JSON — el agente veía handoffs viejos
        sobre los nuevos (autoopt 2026-10-15).
        """
        try:
            base = float(entry.get("score") or 0)
        except (TypeError, ValueError):
            base = 0.0
        ts = parse_ts(entry.get("ts"))
        if ts != _DT_MIN:
            # Revision 2026-10-15: con /1e10 la identidad (+1) pesaba ~107
            # años de recencia — identity mandaba, al revés del docstring.
            # /1e8: +1 de identidad ≈ 3 años. Recencia domina.
            base += 10.0 + ts.timestamp() / 1e8
        if entry.get("identity_valid"):
            base += 1.0
        if str(entry.get("type")) == "HANDOFF":
            base += 0.5
        return base

    def _format_context(self, entries: List[Dict]) -> str:
        lines = ["# 🜄 MEMENTO CONTEXT // Ranked"]
        for e in entries:
            header = e.get("summary", "")[:120].replace("\n", " ")
            kws = e.get("keywords") or []
            keywords = ", ".join(str(k) for k in (kws if isinstance(kws, (list, tuple)) else [kws])[:5])
            score = e.get("score", "?")
            path = e.get("path", "?")
            lines.append(f"- [{e.get('id', '?')}] {e.get('type', '?')} :: {e.get('project', '?')} | {e.get('ts', '?')} | score={score} | {keywords} | {header}")
            lines.append(f"  path={path}")
        return "\n".join(lines)
    
    def ready_check(self) -> Dict:
        """Verifica estado de expansión."""
        handoffs = sum(1 for e in self.index.values() if isinstance(e, dict) and e.get("type") == "HANDOFF")
        contexts = sum(1 for e in self.index.values() if isinstance(e, dict) and e.get("type") == "CONTEXT")
        return {"total": handoffs + contexts, "handoffs": handoffs, "contexts": contexts, "ready": True}

if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path
    from core.paths import workspace_root
    parser = argparse.ArgumentParser(description="MementoBloom Context Builder")
    parser.add_argument("--ready", action="store_true", help="Show ready status only")
    parser.add_argument("--limit", type=int, default=20, help="Limit entries")
    parser.add_argument("--project", default=None, help="Filter by project name")
    args = parser.parse_args()

    ws_root = workspace_root()
    index_path = ws_root / "memory" / "graph" / "memory_index.json"

    cb = ContextBuilder(str(index_path))
    
    if args.ready:
        print(json.dumps(cb.ready_check(), indent=2))
    else:
        print(cb.get_expanded_context(project=args.project, limit=args.limit))
        print("\n---\n")
        print(json.dumps(cb.ready_check(), indent=2))