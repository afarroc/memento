#!/usr/bin/env python3
"""Initialize Memento memory structure in a client project."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import ROOT, workspace_root


def init_project(workspace: Optional[Path] = None, force: bool = False) -> dict:
    ws = workspace or workspace_root()
    ws = ws.resolve()
    
    created = []
    skipped = []
    
    dirs = [
        ws / ".agent_context" / "agent" / "instructions",
        ws / ".agent_context" / "secure",
        ws / ".memento" / "memory" / "graph",
        ws / ".memento_runtime" / "logs",
        ws / ".memento_runtime" / "pids",
        ws / "memory" / "graph",
        ws / "projects" / ws.name,
    ]
    
    for d in dirs:
        if d.exists():
            skipped.append(str(d))
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    
    files = {
        ws / "memory" / "graph" / "memory_index.json": "{}",
        ws / ".agent_context" / "PROJECT_META.md": (
            ROOT / ".agent_context" / "PROJECT_META.md"
        ).read_text(encoding="utf-8") if (ROOT / ".agent_context" / "PROJECT_META.md").exists() else "",
    }
    
    for target, content in files.items():
        if target.exists() and not force:
            skipped.append(str(target))
        else:
            if isinstance(content, str) and content:
                target.write_text(content, encoding="utf-8")
            elif not target.exists():
                target.write_text(content, encoding="utf-8")
            created.append(str(target))
    
    agent_files = [
        "init.md",
        "agent-main.md",
    ]
    agent_dir = ws / ".agent_context" / "agent"
    src_agent_dir = ROOT / ".agent_context" / "agent"
    
    for fname in agent_files:
        src = src_agent_dir / fname
        dst = agent_dir / fname
        if src.exists():
            if dst.exists() and not force:
                skipped.append(str(dst))
            else:
                shutil.copy2(src, dst)
                created.append(str(dst))
    
    instr_dir = agent_dir / "instructions"
    src_instr = src_agent_dir / "instructions"
    if src_instr.exists():
        for f in src_instr.glob("*.md"):
            dst = instr_dir / f.name
            if dst.exists() and not force:
                skipped.append(str(dst))
            else:
                shutil.copy2(f, dst)
                created.append(str(dst))
    
    return {
        "workspace": str(ws),
        "project": ws.name,
        "created": created,
        "skipped": skipped,
        "ok": True,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize Memento in a client project")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace path (default: current dir)")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)
    
    ws = Path(args.workspace).resolve() if args.workspace else workspace_root()
    result = init_project(ws, force=args.force)
    
    if args.json:
        print(__import__("json").dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Memento initialization for project: {result['project']}")
        print(f"Workspace: {result['workspace']}")
        print(f"Created: {len(result['created'])} items")
        for item in result['created']:
            print(f"  + {item}")
        print(f"Skipped: {len(result['skipped'])} items")
        for item in result['skipped']:
            print(f"  = {item}")
        print("\nNext steps:")
        print(f"  1. Edit .agent_context/secure/USER_CONTEXT.md with user preferences")
        print(f"  2. Run: python3 tools/session_start.py --quick")
        print(f"  3. Run: python3 tools/bootstrap_context.py --print")
    
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
