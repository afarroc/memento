#!/usr/bin/env python3
"""Export Memento memory to various formats for integration into client projects."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import load_index, top_entries, latest_handoffs
from core.paths import workspace_root


def export_markdown(entries: List[Dict[str, Any]], title: str = "Memento Memory Export") -> str:
    lines = [
        f"# {title}",
        "",
        f"Exportado: {datetime.now().isoformat(timespec='seconds')}",
        f"Proyecto: {workspace_root().name}",
        f"Entradas: {len(entries)}",
        "",
        "---",
        "",
    ]
    for entry in entries:
        entry_type = entry.get("type", "?")
        project = entry.get("project", "?")
        ts = entry.get("ts", "?")
        summary = " ".join(str(entry.get("summary", "")).split())
        lines.append(f"## [{entry.get('id', '?')}] {entry_type} | {project} | {ts}")
        lines.append("")
        lines.append(summary[:500])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def export_json(entries: List[Dict[str, Any]]) -> str:
    export_data = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "project": workspace_root().name,
        "total_entries": len(entries),
        "entries": entries,
    }
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_context(entries: List[Dict[str, Any]]) -> str:
    lines = [
        "# MEMENTO CONTEXT EXPORT",
        "",
        f"Project: {workspace_root().name}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Entries: {len(entries)}",
        "",
    ]
    for entry in entries:
        keywords = ", ".join(entry.get("keywords", [])[:8])
        lines.append(
            f"- [{entry.get('id', '?')}] {entry.get('type', '?')} "
            f"| {entry.get('project', '?')} | {entry.get('ts', '?')} "
            f"| score={entry.get('score', 0)} | {keywords}"
        )
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export Memento memory to client project formats")
    parser.add_argument("--format", choices=["markdown", "json", "context"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--output", "-o", default=None, help="Output file path (default: stdout)")
    parser.add_argument("--limit", type=int, default=50, help="Max entries to export")
    parser.add_argument("--project", default=None, help="Filter by project")
    parser.add_argument("--type", default=None, help="Filter by type (HANDOFF, CONTEXT, etc.)")
    parser.add_argument("--handoffs-only", action="store_true", help="Export only HANDOFF entries")
    args = parser.parse_args(argv)

    index = load_index()
    entries = list(index.values())

    if args.project:
        entries = [e for e in entries if e.get("project") == args.project]
    if args.type:
        entries = [e for e in entries if e.get("type") == args.type]
    if args.handoffs_only:
        entries = [e for e in entries if e.get("type") == "HANDOFF"]

    entries.sort(key=lambda e: str(e.get("ts", "")), reverse=True)
    entries = entries[:args.limit]

    if args.format == "markdown":
        output = export_markdown(entries)
    elif args.format == "json":
        output = export_json(entries)
    elif args.format == "context":
        output = export_context(entries)
    else:
        output = export_markdown(entries)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Exportado: {out_path} ({len(entries)} entradas)")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
