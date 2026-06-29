#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import build_manifest, load_index, resolve_index_path, save_index
from core.paths import detect_workspace_root, rel

HANDOFF_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


class QuickScan:
    def __init__(self, workspace: Path, index_path: Optional[Path] = None, legacy_index: bool = False):
        self.workspace = workspace.resolve()
        self.projects = self.workspace / "projects"
        self.index_path = resolve_index_path(str(index_path) if index_path else None, workspace=self.workspace, legacy=legacy_index)
        self.index = load_index(self.index_path)
        self.new_count = 0

    def scan(self, incremental_path: Optional[str] = None, build_manifest_output: bool = True) -> Dict[str, Any]:
        self.projects.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        existing_ids = set(self.index.keys())

        if incremental_path:
            f = Path(incremental_path)
            if not f.is_absolute():
                f = self.workspace / f
            if f.name.startswith("HANDOFF") and f.suffix == ".md":
                entry = self._parse_handoff(f)
                if entry and entry["id"] not in existing_ids:
                    self.index[entry["id"]] = entry
                    self.new_count += 1
            elif f.name.endswith("_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and entry["id"] not in existing_ids:
                    self.index[entry["id"]] = entry
                    self.new_count += 1
        else:
            for f in self.projects.rglob("HANDOFF*.md"):
                entry = self._parse_handoff(f)
                if entry and entry["id"] not in existing_ids:
                    self.index[entry["id"]] = entry
                    existing_ids.add(entry["id"])
                    self.new_count += 1

            for f in self.projects.rglob("*_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and entry["id"] not in existing_ids:
                    self.index[entry["id"]] = entry
                    existing_ids.add(entry["id"])
                    self.new_count += 1

        saved = save_index(self.index, self.index_path)
        manifest = None
        if build_manifest_output:
            manifest = build_manifest(self.index, self.index_path.parent / "index_manifest.json")
        return {
            "ok": True,
            "index_path": str(saved),
            "total": len(self.index),
            "new": self.new_count,
            "manifest": manifest,
        }

    def _parse_handoff(self, f: Path) -> Dict[str, Any]:
        content = f.read_text(encoding="utf-8", errors="replace")[:500]
        date_m = HANDOFF_RE.search(f.name)

        def _extract_project(path: Path) -> str:
            """Extract project name from path, handling handoffs/ subdirectories."""
            parts = path.parts
            # Buscar 'projects' en la ruta y tomar el siguiente componente
            for i, part in enumerate(parts):
                if part == "projects" and i + 1 < len(parts):
                    return parts[i + 1]
            return path.parent.name

        return {
            "id": f"h_{f.stem}",
            "type": "HANDOFF",
            "project": _extract_project(f),
            "ts": date_m.group(1) if date_m else "unknown",
            "path": rel(f, self.workspace),
            "summary": content[:100],
        }

    def _parse_context(self, f: Path) -> Dict[str, Any]:
        content = f.read_text(encoding="utf-8", errors="replace")[:500]

        def _extract_project(path: Path) -> str:
            """Extract project name from path, handling handouts/ subdirectories."""
            parts = path.parts
            for i, part in enumerate(parts):
                if part == "projects" and i + 1 < len(parts):
                    return parts[i + 1]
            return path.parent.name

        return {
            "id": f"c_{f.stem}",
            "type": "CONTEXT",
            "project": _extract_project(f),
            "ts": "discover",
            "path": rel(f, self.workspace),
            "summary": content[:100],
        }


def detect_workspace() -> Path:
    return detect_workspace_root()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Escaneo incremental de memoria MementoBloom")
    parser.add_argument("incremental_path", nargs="?", help="HANDOFF o *_CONTEXT.md a indexar")
    parser.add_argument("--workspace", default=None, help="Workspace raíz")
    parser.add_argument("--index", default=None, help="Ruta del índice de memoria")
    parser.add_argument("--legacy-index", action="store_true", help="Usar .memento/memory/graph/memory_index.json")
    parser.add_argument("--no-manifest", action="store_true", help="No actualizar index_manifest.json")
    parser.add_argument("--json", action="store_true", help="Imprimir resultado en JSON")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve() if args.workspace else detect_workspace()
    scanner = QuickScan(workspace=workspace, index_path=Path(args.index) if args.index else None, legacy_index=args.legacy_index)
    result = scanner.scan(incremental_path=args.incremental_path, build_manifest_output=not args.no_manifest)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Scanning projects...")
        print(f"Total: {result['total']} entries (nuevos: {result['new']})")
        print(f"Index: {result['index_path']}")
        if result.get("manifest"):
            print(f"Manifest: {result['manifest']['updated_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
