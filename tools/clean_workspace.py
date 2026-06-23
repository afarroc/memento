#!/usr/bin/env python3
"""Clean Memento-generated artifacts from workspace (safe, reversible)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import workspace_root
from core.index import load_index


def get_cleanable_paths(ws: Path) -> List[dict]:
    items = []
    
    agent_dirs = [
        ws / ".agent_context" / "agent" / "agent-main.md",
        ws / ".agent_context" / "START_CONTEXT.md",
        ws / ".agent_context" / "USER_CONTEXT.md",
        ws / ".agent_context" / "secure" / "USER_CONTEXT.md",
        ws / ".agent_context" / "secure" / "SECURE.md",
    ]
    for p in agent_dirs:
        if p.exists():
            items.append({"path": str(p), "type": "agent_context", "action": "remove"})
    
    runtime_dirs = [
        ws / ".memento_runtime" / "health_cache.json",
        ws / ".memento_runtime" / "logs",
        ws / ".memento_runtime" / "pids",
    ]
    for p in runtime_dirs:
        if p.exists():
            items.append({"path": str(p), "type": "runtime", "action": "remove"})
    
    idx = ws / "memory" / "graph" / "memory_index.json"
    if idx.exists():
        items.append({"path": str(idx), "type": "memory_index", "action": "empty"})
    
    manifest = ws / "memory" / "graph" / "index_manifest.json"
    if manifest.exists():
        items.append({"path": str(manifest), "type": "manifest", "action": "remove"})
    
    uploads = ws / "uploads"
    if uploads.exists() and any(uploads.iterdir()):
        items.append({"path": str(uploads), "type": "uploads", "action": "empty"})
    
    return items


def clean_workspace(dry_run: bool = False, force: bool = False) -> dict:
    ws = workspace_root()
    items = get_cleanable_paths(ws)
    
    if not items:
        return {"ok": True, "cleaned": 0, "items": [], "message": "Nothing to clean"}
    
    if not force and not dry_run:
        print(f"Found {len(items)} cleanable items in {ws}:")
        for item in items:
            print(f"  - {item['type']}: {item['path']}")
        confirm = input("Proceed with cleanup? [y/N] ").strip().lower()
        if confirm != "y":
            return {"ok": True, "cleaned": 0, "items": items, "message": "Cancelled by user"}
    
    cleaned = 0
    errors = []
    backup_dir = ws / ".memento_runtime" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for item in items:
        p = Path(item["path"])
        try:
            if dry_run:
                cleaned += 1
                continue
            
            if item["action"] == "remove":
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                cleaned += 1
            elif item["action"] == "empty":
                if p.suffix == ".json" and p.name == "memory_index.json":
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup_path = backup_dir / p.name
                    if p.exists():
                        shutil.copy2(p, backup_path)
                    p.write_text("{}", encoding="utf-8")
                else:
                    p.write_text("{}", encoding="utf-8")
                cleaned += 1
        except Exception as exc:
            errors.append({"path": item["path"], "error": str(exc)})
    
    return {
        "ok": len(errors) == 0,
        "cleaned": cleaned,
        "errors": errors,
        "items": items,
        "backup_dir": str(backup_dir) if not dry_run else None,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Clean Memento workspace artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)
    
    result = clean_workspace(dry_run=args.dry_run, force=args.force)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status = "DRY RUN" if args.dry_run else "CLEANED"
        print(f"{status}: {result['cleaned']} items")
        if result.get("errors"):
            print(f"Errors: {len(result['errors'])}")
            for err in result["errors"]:
                print(f"  - {err['path']}: {err['error']}")
        if result.get("backup_dir"):
            print(f"Backup: {result['backup_dir']}")
        if result.get("message"):
            print(result["message"])
    
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
