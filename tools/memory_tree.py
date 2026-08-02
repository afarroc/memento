#!/usr/bin/env python3
"""memory_tree.py — lista el Context Tree de memento sin volcar contenido.

Context Tree jerárquico: Domain (project) > Tema (type/tags) > Entry.
Da "ambient awareness" al agente: ve qué existe sin saturar el contexto
(contenido de las entries NO se imprime). Inspirado en ByteRover (arxiv 2604.01599).

Uso:
    python3 tools/memory_tree.py
    python3 tools/memory_tree.py --domain Administracion_UPN
    python3 tools/memory_tree.py --domain m360 --tags curso
    python3 tools/memory_tree.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import load_index, resolve_index_path
from core.paths import detect_workspace_root


def _iter_entries(index: Dict[str, Any]):
    for _k, v in index.items():
        if isinstance(v, dict):
            yield v


def build_tree(index: Dict[str, Any]) -> Dict[str, Any]:
    """Domain > Tema(type) > lista de entries (id, ts, tags)."""
    tree: Dict[str, Any] = defaultdict(lambda: {"by_type": defaultdict(list), "total": 0})
    for v in _iter_entries(index):
        dom = v.get("project") or "unknown"
        ttype = v.get("type") or "unknown"
        tree[dom]["by_type"][ttype].append({
            "id": v.get("id"),
            "ts": v.get("ts"),
            "tags": v.get("tags") or [],
        })
        tree[dom]["total"] += 1
    return tree


def _print_tree(tree: Dict[str, Any], domain_filter: Optional[str], tag_filter: Optional[str]) -> None:
    domains = sorted(tree.keys())
    for dom in domains:
        if domain_filter and dom != domain_filter:
            continue
        node = tree[dom]
        print(f"\n■ {dom}  ({node['total']} entries)")
        for ttype in sorted(node["by_type"].keys()):
            entries = node["by_type"][ttype]
            if tag_filter:
                entries = [e for e in entries if tag_filter in (e["tags"] or [])]
            if not entries:
                continue
            print(f"  ├─ {ttype}  ({len(entries)})")
            for e in sorted(entries, key=lambda x: str(x.get("ts") or ""), reverse=True)[:12]:
                tags = ",".join((e["tags"] or [])[:4])
                tag_s = f"  [{tags}]" if tags else ""
                print(f"  │    • {e['id']}{tag_s}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Lista el Context Tree de memento (sin volcar contenido).")
    ap.add_argument("--domain", help="Filtrar por dominio (campo project).")
    ap.add_argument("--tags", help="Filtrar entries por tag (solo visible en modo --domain).")
    ap.add_argument("--json", action="store_true", help="Salida JSON del árbol.")
    ap.add_argument("--index", help="Ruta al memory_index.json (opcional).")
    args = ap.parse_args()

    ws = detect_workspace_root()
    idx_path = resolve_index_path(args.index, workspace=ws)
    index = load_index(idx_path)

    tree = build_tree(index)

    if args.json:
        out = {d: {"total": n["total"], "types": {t: len(es) for t, es in n["by_type"].items()}}
               for d, n in tree.items()}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    total = sum(n["total"] for n in tree.values())
    print(f"# Context Tree de memento — {total} entries, {len(tree)} dominios")
    print("# (estructura Domain > Tema > Entry; contenido NO se imprime)")
    _print_tree(tree, args.domain, args.tags)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
