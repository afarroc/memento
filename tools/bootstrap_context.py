#!/usr/bin/env python3
"""Bootstrap universal de contexto para MementoBloom.

Este script no depende de ningún agente ni modelo específico. Imprime un contexto
compacto que cualquier modelo, CLI o agente puede usar para continuar una
sesión: proyecto, Git, memoria, handoffs y servicios.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve workspace first before importing core modules
MEMENTO_WORKSPACE = os.environ.get("MEMENTO_WORKSPACE")
SCRIPT_ROOT = Path(__file__).resolve().parent.parent  # mementobloom/ directory

# Determine correct paths based on execution context:
# - Client mode: MEMENTO_WORKSPACE is the client workspace, core/ is in mementobloom/
# - Dev mode: Running directly from mementobloom repo, no MEMENTO_WORKSPACE
if MEMENTO_WORKSPACE:
    WS_ROOT = Path(MEMENTO_WORKSPACE).expanduser().resolve()
    MEMENTO_ROOT = WS_ROOT / "mementobloom"  # Client has mementobloom/ subdir
else:
    WS_ROOT = SCRIPT_ROOT  # Running from mementobloom repo directly
    MEMENTO_ROOT = WS_ROOT  # Same directory in dev mode

# Add mementobloom directory to path for core imports
sys.path.insert(0, str(MEMENTO_ROOT))

from core.git import check_ignore, git_diff_stat, git_status, latest_commit
from core.index import count_by, latest_handoffs, load_index, resolve_index_path, top_entries
from core.paths import rel
from core.services import service_status, service_summary

INDEX_PATH = WS_ROOT / "memory" / "graph" / "memory_index.json"
PROJECT_META = WS_ROOT / ".agent_context" / "PROJECT_META.md"
USER_CONTEXT = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
START_CONTEXT = WS_ROOT / ".agent_context" / "START_CONTEXT.md"
AGENT_INIT = WS_ROOT / ".agent_context" / "agent" / "init.md"
SECURE_CONTEXT = WS_ROOT / ".agent_context" / "secure" / "SECURE.md"


def load_project_priority() -> List[str]:
    if not USER_CONTEXT.exists():
        return []
    text = USER_CONTEXT.read_text(encoding="utf-8", errors="replace")
    in_section = False
    priorities: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_section = line.lower() == "## proyectos prioritarios"
            continue
        if not in_section or not line.startswith("-"):
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            priorities.append(match.group(1))
    return priorities


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": rel(path), "lines": 0, "chars": 0, "summary": ""}
    text = path.read_text(encoding="utf-8", errors="replace")
    summary = " ".join(line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))
    return {
        "exists": True,
        "path": rel(path),
        "lines": len(text.splitlines()),
        "chars": len(text),
        "summary": " ".join(summary.split()),
    }


def build_context(
    limit: int = 8,
    project: Optional[str] = None,
    include_files: bool = True,
    index_path: Optional[Path] = None,
    check_services: bool = True,
    fresh_health: bool = False,
) -> Dict[str, Any]:
    index_file = resolve_index_path(str(index_path) if index_path else None, workspace=WS_ROOT)
    index = load_index(index_file)
    entries = top_entries(index, limit, project=project)
    handoffs = latest_handoffs(index, 5, project=project)
    project_meta = read_file(PROJECT_META) if include_files else {"exists": PROJECT_META.exists(), "path": rel(PROJECT_META)}
    user_context = read_file(USER_CONTEXT) if include_files else {"exists": USER_CONTEXT.exists(), "path": rel(USER_CONTEXT)}
    start_context = read_file(START_CONTEXT) if include_files else {"exists": START_CONTEXT.exists(), "path": rel(START_CONTEXT)}
    agent_init = read_file(AGENT_INIT) if include_files else {"exists": AGENT_INIT.exists(), "path": rel(AGENT_INIT)}
    services = service_status(fresh=fresh_health) if check_services else {"checked": False, "reason": "services disabled"}
    return {
        "generated_at": now_iso(),
        "environment": {
            "working_directory": str(WS_ROOT),
            "workspace_root": str(WS_ROOT),
            "project": WS_ROOT.name,
        },
        "files": {
            "project_meta": project_meta,
            "user_context": user_context,
            "start_context": start_context,
            "agent_init": agent_init,
            "user_context_ignored": check_ignore(rel(USER_CONTEXT)) if USER_CONTEXT.exists() else {"ignored": True, "rule": "optional"},
        },
        "git": {
            "latest_commit": latest_commit(root=WS_ROOT),
            "status": git_status(root=WS_ROOT),
            "diff_stat": git_diff_stat(root=WS_ROOT),
        },
        "memory": {
            "index_path": rel(index_file),
            "entries": len(index),
            "by_type": count_by(index.values(), "type"),
            "by_project": count_by(index.values(), "project"),
        },
        "top_context": entries,
        "latest_handoffs": handoffs,
        "services": services,
        "bootstrap_commands": {
            "universal": "python3 tools/bootstrap_context.py --print",
            "startup_doctor": "python3 tools/doctor.py --startup",
            "selftest": "python3 tools/selftest.py",
            "ranked_context": "python3 tools/context_builder.py --limit 12",
            "quick_scan": "python3 tools/quick_scan.py <HANDOFF_PATH>",
        },
    }


def format_markdown(context: Dict[str, Any]) -> str:
    git = context.get("git", {})
    commit = git.get("latest_commit", {})
    status = git.get("status", {})
    memory = context.get("memory", {})
    services_data = context.get("services", {})
    files = context.get("files", {})
    lines = [
        "# MementoBloom Bootstrap Context",
        "",
        f"Generated: {context.get('generated_at')}",
        f"Project: {context.get('environment', {}).get('project')}",
        f"Working directory: {context.get('environment', {}).get('working_directory')}",
        "",
        "## User and project meta",
        f"- PROJECT_META.md: {'OK' if files.get('project_meta', {}).get('exists') else 'NO'}",
        f"- USER_CONTEXT.md: {'OK' if files.get('user_context', {}).get('exists') else 'OPTIONAL'}",
        f"- START_CONTEXT.md: {'OK' if files.get('start_context', {}).get('exists') else 'OPTIONAL'}",
        f"- Agent init: {'OK' if files.get('agent_init', {}).get('exists') else 'NO'}",
        f"- USER_CONTEXT ignored by Git: {'OK' if files.get('user_context_ignored', {}).get('ignored') else 'NO'}",
        "",
        "## Project meta summary",
        files.get("project_meta", {}).get("summary", "No project meta file found."),
        "",
        "## User context summary",
        files.get("user_context", {}).get("summary", "No user context file found or optional."),
        "",
        "## Git state",
        f"- Commit: {commit.get('hash', '?')} {commit.get('message', '')}".strip(),
        f"- Pending changes: {status.get('change_count', 0)}",
    ]
    for change in status.get("changes", [])[:6]:
        lines.append(f"  - {change}")
    diff = git.get("diff_stat", {}).get("text", "").strip()
    if diff:
        lines.extend(["", "## Diff stat", diff])
    lines.extend([
        "",
        "## Memory",
        f"- Index: {memory.get('index_path')} ({memory.get('entries', 0)} entries)",
        f"- By type: {json.dumps(memory.get('by_type', {}), ensure_ascii=False)}",
        f"- By project: {json.dumps(memory.get('by_project', {}), ensure_ascii=False)}",
        "",
        "## Latest handoffs",
    ])
    for entry in context.get("latest_handoffs", []):
        summary = " ".join(str(entry.get("summary", "")).split())[:220]
        lines.append(f"- {entry.get('id', '?')} | {entry.get('project', '?')} | {entry.get('ts', '?')} | {summary}")
    lines.extend(["", "## Top context entries"])
    for entry in context.get("top_context", []):
        summary = " ".join(str(entry.get("summary", "")).split())[:180]
        lines.append(f"- {entry.get('id', '?')} | {entry.get('type', '?')} | {entry.get('project', '?')} | {entry.get('ts', '?')} | {summary}")

    if services_data.get("checked") is False:
        lines.extend([
            "",
            "## Services",
            "- Services: not checked",
        ])
    else:
        lines.extend([
            "",
            "## Services",
            service_summary(services_data),
        ])
    lines.extend([
        "",
        "## Bootstrap commands",
        "- python3 tools/bootstrap_context.py --print",
        "- python3 tools/doctor.py --startup",
        "- python3 tools/selftest.py",
        "- python3 tools/context_builder.py --limit 12",
        "- python3 tools/quick_scan.py <HANDOFF_PATH>",
        "",
        "## Optional agent-specific commands",
        "- python3 tools/optimize_agent.py --context",
    ])
    return "\n".join(lines) + "\n"


def write_session_md(context: Dict[str, Any]) -> None:
    session_file = WS_ROOT / "SESSION.md"
    git = context.get("git", {})
    services_data = context.get("services", {})
    memory = context.get("memory", {})
    session = {
        "session": {
            "project": context.get("environment", {}).get("project", "mementobloom"),
            "role": "asistente-gtd",
            "workspace": str(WS_ROOT),
            "last_event_time": context.get("generated_at"),
            "last_event_type": "bootstrap",
            "last_event_summary": git.get("latest_commit", {}).get("message", "Bootstrap ejecutado"),
            "git_branch": git.get("latest_commit", {}).get("branch", "unknown"),
            "git_commit": git.get("latest_commit", {}).get("hash", "unknown"),
            "generated_at": context.get("generated_at"),
        },
        "state": {
            "git": {
                "branch": git.get("latest_commit", {}).get("branch", "unknown"),
                "commit_hash": git.get("latest_commit", {}).get("hash", "unknown"),
                "commit_message": git.get("latest_commit", {}).get("message", "unknown"),
                "pending_count": git.get("status", {}).get("change_count", 0),
            },
            "services": {
                "sala": services_data.get("sala", "NO"),
                "panel": services_data.get("panel", "NO"),
                "redis": services_data.get("redis", "NO"),
            },
            "memory": {
                "indexed_entries": memory.get("entries", 0),
                "manifest_ts": memory.get("manifest_ts", ""),
            },
        },
        "forbidden_paths": [
            ".agent_context/secure/*",
            "memory/**/*.json",
            "*.env",
            ".memento/**",
            "archive/**",
        ],
        "entrypoint": "python3 tools/session_bootstrap.py",
    }
    session_file.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Imprime contexto universal modelo-agnóstico para MementoBloom")
    parser.add_argument("--print", action="store_true", help="Imprime contexto en Markdown")
    parser.add_argument("--json", action="store_true", help="Imprime contexto en JSON")
    parser.add_argument("--limit", type=int, default=8, help="Cantidad de entradas de contexto")
    parser.add_argument("--project", default=None, help="Filtrar memoria por proyecto")
    parser.add_argument("--no-files", action="store_true", help="No incluir resúmenes de archivos")
    parser.add_argument("--index", default=None, help="Ruta del índice de memoria")
    parser.add_argument("--no-services", action="store_true", help="No verificar servicios locales/remotos")
    parser.add_argument("--fresh-health", action="store_true", help="Forzar chequeo de servicios sin usar caché")
    args = parser.parse_args(argv or sys.argv[1:])

    context = build_context(
        limit=args.limit,
        project=args.project,
        include_files=not args.no_files,
        index_path=Path(args.index) if args.index else None,
        check_services=not args.no_services,
        fresh_health=args.fresh_health,
    )

    write_session_md(context)

    if args.json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
