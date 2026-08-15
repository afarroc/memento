#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import build_manifest, load_index, resolve_index_path, save_index
from core.paths import detect_workspace_root, rel

HANDOFF_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
IDENTITY_RE = re.compile(r"<!-- IDENTIDAD:\s*project_type=(self|cliente),\s*target_path=[^ ]+/ -->", re.IGNORECASE)


class QuickScan:
    def __init__(self, workspace: Path, index_path: Optional[Path] = None):
        self.workspace = workspace.resolve()
        self.projects = self.workspace / "projects"
        self.index_path = resolve_index_path(str(index_path) if index_path else None, workspace=self.workspace)
        self.index = load_index(self.index_path)
        self.new_count = 0

    def scan(self, incremental_path: Optional[str] = None, build_manifest_output: bool = True, replace_existing: bool = False, prune_missing: bool = False) -> Dict[str, Any]:
        self.projects.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        existing_ids = set(self.index.keys())

        if incremental_path:
            f = Path(incremental_path)
            if not f.is_absolute():
                f = self.workspace / f
            if f.name.startswith("HANDOFF") and f.suffix == ".md":
                entry = self._parse_handoff(f)
                if entry and (replace_existing or entry["id"] not in existing_ids):
                    self.index[entry["id"]] = entry
                    if replace_existing and entry["id"] in existing_ids:
                        self.new_count += 0  # replacement not counted as new
                    else:
                        self.new_count += 1
            elif f.name.endswith("_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and (replace_existing or entry["id"] not in existing_ids):
                    self.index[entry["id"]] = entry
                    if replace_existing and entry["id"] in existing_ids:
                        self.new_count += 0
                    else:
                        self.new_count += 1
        else:
            for f in self.projects.rglob("HANDOFF*.md"):
                entry = self._parse_handoff(f)
                if entry and (replace_existing or entry["id"] not in existing_ids):
                    self.index[entry["id"]] = entry
                    if not replace_existing:
                        existing_ids.add(entry["id"])
                        self.new_count += 1
                    else:
                        # ensure id stays in set for subsequent dedup if needed
                        existing_ids.add(entry["id"])

            for f in self.projects.rglob("*_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and (replace_existing or entry["id"] not in existing_ids):
                    self.index[entry["id"]] = entry
                    if not replace_existing:
                        existing_ids.add(entry["id"])
                        self.new_count += 1
                    else:
                        existing_ids.add(entry["id"])

        if prune_missing:
            to_remove = []
            for entry_id, entry in list(self.index.items()):
                if not isinstance(entry, dict):
                    continue
                path = entry.get("path")
                if not path:
                    continue
                candidate = (self.workspace / path).expanduser()
                if not candidate.exists():
                    to_remove.append(entry_id)
            for entry_id in to_remove:
                del self.index[entry_id]
            self.new_count -= len(to_remove)

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

        project = _extract_project(f)
        identity_valid = bool(IDENTITY_RE.search(content))
        return {
            "id": f"h_{project}_{f.stem}",
            "type": "HANDOFF",
            "project": project,
            "ts": date_m.group(1) if date_m else "unknown",
            "path": rel(f, self.workspace),
            "summary": content[:100],
            "identity_valid": identity_valid,
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

        project = _extract_project(f)
        # Usar mtime como fallback para archivos CONTEXT sin fecha en el nombre
        fallback_ts = _dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds")[:19]
        return {
            "id": f"c_{project}_{f.stem}",
            "type": "CONTEXT",
            "project": project,
            "ts": fallback_ts,
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
    parser.add_argument("--no-manifest", action="store_true", help="No actualizar index_manifest.json")
    parser.add_argument("--json", action="store_true", help="Imprimir resultado en JSON")
    parser.add_argument("--replace", action="store_true", help="Reemplazar entradas existentes durante el escaneo completo")
    parser.add_argument("--verify-all", action="store_true", help="Verificar integridad del índice: duplicados, paths perdidos e identidad")
    parser.add_argument("--prune", action="store_true", help="Eliminar entradas del índice cuyos archivos no existen en el filesystem")
    args = parser.parse_args(argv)

    if args.verify_all:
        workspace = Path(args.workspace).resolve() if args.workspace else detect_workspace()
        index_path = resolve_index_path(args.index, workspace=workspace)
        index = load_index(index_path)
        paths = [e.get('path') for e in index.values() if isinstance(e, dict) and e.get('path')]
        missing = [p for p in paths if not (workspace / p).expanduser().exists()]
        dupes = len(paths) - len(set(paths))
        invalid = [e.get('id') for e in index.values() if isinstance(e, dict) and str(e.get('type')) == 'HANDOFF' and not e.get('identity_valid')]
        print(json.dumps({
            'ok': True,
            'total': len(index),
            'missing_paths': missing,
            'missing_count': len(missing),
            'duplicates': dupes,
            'invalid_identity': invalid,
            'invalid_identity_count': len(invalid),
        }, indent=2, ensure_ascii=False))
        return 0

    workspace = Path(args.workspace).resolve() if args.workspace else detect_workspace()
    scanner = QuickScan(workspace=workspace, index_path=Path(args.index) if args.index else None)
    result = scanner.scan(incremental_path=args.incremental_path, build_manifest_output=not args.no_manifest, replace_existing=args.replace, prune_missing=args.prune)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Scanning projects...")
        print(f"Total: {result['total']} entries (nuevos: {result['new']})")
        print(f"Index: {rel(Path(result['index_path']))}")
        if result.get("manifest"):
            print(f"Manifest: {result['manifest']['updated_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
