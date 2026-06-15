#!/usr/bin/env python3
"""Bootstrap universal de contexto para MementoBloom.

Este script no depende de ningún agente ni modelo específico. Imprime un contexto
compacto que cualquier modelo, CLI o agente puede usar para continuar una
sesión: usuario, meta del proyecto, Git, memoria, handoffs y servicios.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "memory" / "graph" / "memory_index.json"
PROJECT_META = ROOT / ".kilo" / "PROJECT_META.md"
USER_CONTEXT = ROOT / ".kilo" / "secure" / "USER_CONTEXT.md"
START_CONTEXT = ROOT / ".kilo" / "START_CONTEXT.md"
AGENT_INIT = ROOT / ".kilo" / "agent" / "init.md"
SECURE_CONTEXT = ROOT / ".kilo" / "secure" / "SECURE.md"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost" if os.environ.get("REDIS_DISABLE") else "192.168.18.59")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
PROJECT_PRIORITY: List[str] = []


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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def run_command(args: List[str], timeout: int = 10) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "returncode": None}


def parse_ts(value: str) -> datetime:
    text = str(value or "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return datetime.min


def entry_sort_key(entry: Dict[str, Any]) -> tuple[Any, ...]:
    ts = parse_ts(str(entry.get("ts", "")))
    project = str(entry.get("project", ""))
    entry_type = str(entry.get("type", ""))
    priorities = PROJECT_PRIORITY or load_project_priority()
    project_priority = priorities.index(project) if priorities and project in priorities else 99
    type_priority = {"HANDOFF": 0, "SOURCE": 1, "NOTE": 2, "CONTEXT": 3, "COMPONENT": 4}.get(entry_type, 50)
    return (ts, -project_priority, -type_priority, str(entry.get("id", "")))


def load_index() -> Dict[str, Dict[str, Any]]:
    if not INDEX_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def top_entries(index: Dict[str, Dict[str, Any]], limit: int, project: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = list(index.values())
    if project:
        entries = [entry for entry in entries if str(entry.get("project")) == project]
    entries.sort(key=entry_sort_key, reverse=True)
    return entries[:limit]


def latest_handoffs(index: Dict[str, Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    return [entry for entry in top_entries(index, limit * 2) if str(entry.get("type")) == "HANDOFF"][:limit]


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
        "summary": " ".join(summary.split())[:700],
    }


def git_check_ignore(path: str) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(ROOT), "check-ignore", "-v", path])
    return {"ignored": result["ok"], "rule": result["stdout"].strip(), "error": result["stderr"].strip() if not result["ok"] else ""}


def git_state() -> Dict[str, Any]:
    status = run_command(["git", "-C", str(ROOT), "status", "--short"])
    diff = run_command(["git", "-C", str(ROOT), "diff", "--stat"])
    commit = run_command(["git", "-C", str(ROOT), "log", "-1", "--oneline"])
    changes = [line for line in status.get("stdout", "").splitlines() if line.strip()]
    commit_parts = commit.get("stdout", "").split(" ", 1)
    return {
        "latest_commit": {
            "hash": commit_parts[0] if commit_parts else "",
            "message": commit_parts[1] if len(commit_parts) > 1 else "",
            "raw": commit.get("stdout", ""),
            "ok": bool(commit.get("ok")),
        },
        "status": {
            "changes": changes,
            "change_count": len(changes),
            "raw": status.get("stdout", ""),
            "ok": bool(status.get("ok")),
        },
        "diff_stat": {
            "text": diff.get("stdout", ""),
            "ok": bool(diff.get("ok")),
        },
    }


def redis_ping(timeout: float = 1.0) -> Dict[str, Any]:
    try:
        with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=timeout) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(128).decode(errors="replace")
        return {"ok": "PONG" in data, "detail": data.strip(), "host": REDIS_HOST, "port": REDIS_PORT}
    except OSError as exc:
        return {"ok": False, "detail": str(exc), "host": REDIS_HOST, "port": REDIS_PORT}


def http_json(url: str, timeout: float = 1.0) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw[:500]}
            return {"ok": 200 <= response.status < 500, "status": response.status, "data": parsed}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def services() -> Dict[str, Any]:
    sala = http_json(f"http://127.0.0.1:{SALA_PORT}/stats")
    panel = http_json(f"http://127.0.0.1:{PANEL_PORT}/stats")
    return {
        "redis": redis_ping(timeout=0.6),
        "sala": {"ok": bool(sala.get("ok")), "status": sala.get("status"), "data": sala.get("data"), "error": sala.get("error")},
        "panel": {"ok": bool(panel.get("ok")), "status": panel.get("status"), "data": panel.get("data"), "error": panel.get("error")},
    }


def count_by(entries: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in entries:
        value = str(entry.get(field, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_context(limit: int = 8, project: Optional[str] = None, include_files: bool = True) -> Dict[str, Any]:
    index = load_index()
    entries = top_entries(index, limit, project=project)
    handoffs = latest_handoffs(index, 5)
    project_meta = read_file(PROJECT_META)
    user_context = read_file(USER_CONTEXT)
    start_context = read_file(START_CONTEXT)
    agent_init = read_file(AGENT_INIT)
    return {
        "generated_at": now_iso(),
        "environment": {
            "working_directory": str(ROOT),
            "workspace_root": str(ROOT.parent),
            "project": ROOT.name,
        },
        "files": {
            "project_meta": project_meta,
            "user_context": user_context,
            "start_context": start_context,
            "agent_init": agent_init,
            "user_context_ignored": git_check_ignore(rel(USER_CONTEXT)) if USER_CONTEXT.exists() else {"ignored": False, "rule": ""},
        },
        "git": git_state(),
        "memory": {
            "index_path": rel(INDEX_PATH),
            "entries": len(index),
            "by_type": count_by(list(index.values()), "type"),
            "by_project": count_by(list(index.values()), "project"),
        },
        "top_context": entries,
        "latest_handoffs": handoffs,
        "services": services(),
        "bootstrap_commands": {
            "universal": "python3 tools/bootstrap_context.py --print",
            "audit": "python3 tools/optimize_agent.py --context",
            "ranked_context": "python3 tools/context_builder.py --limit 12",
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
        f"- USER_CONTEXT.md: {'OK' if files.get('user_context', {}).get('exists') else 'NO'}",
        f"- START_CONTEXT.md: {'OK' if files.get('start_context', {}).get('exists') else 'NO'}",
        f"- Agent init: {'OK' if files.get('agent_init', {}).get('exists') else 'NO'}",
        f"- USER_CONTEXT ignored by Git: {'OK' if files.get('user_context_ignored', {}).get('ignored') else 'NO'}",
        "",
        "## Project meta summary",
        files.get("project_meta", {}).get("summary", "No project meta file found."),
        "",
        "## User context summary",
        files.get("user_context", {}).get("summary", "No user context file found."),
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
    redis = services_data.get("redis", {})
    sala = services_data.get("sala", {})
    panel = services_data.get("panel", {})
    lines.extend([
        "",
        "## Services",
        f"- Redis: {'OK' if redis.get('ok') else 'NO'} at {redis.get('host', '?')}:{redis.get('port', '?')}",
        f"- Sala: {'OK' if sala.get('ok') else 'NO'} at http://127.0.0.1:{SALA_PORT}",
        f"- Panel: {'OK' if panel.get('ok') else 'NO'} at http://127.0.0.1:{PANEL_PORT}",
        "",
        "## Bootstrap commands",
        "- python3 tools/bootstrap_context.py --print",
        "- python3 tools/context_builder.py --limit 12",
        "- python3 tools/quick_scan.py <HANDOFF_PATH>",
        "",
        "## Optional agent-specific commands",
        "- python3 tools/optimize_agent.py --context",
    ])
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Imprime contexto universal modelo-agnóstico para MementoBloom")
    parser.add_argument("--print", action="store_true", help="Imprime contexto en Markdown")
    parser.add_argument("--json", action="store_true", help="Imprime contexto en JSON")
    parser.add_argument("--limit", type=int, default=8, help="Cantidad de entradas de contexto")
    parser.add_argument("--project", default=None, help="Filtrar memoria por proyecto")
    parser.add_argument("--no-files", action="store_true", help="No incluir resúmenes de archivos")
    args = parser.parse_args(argv or sys.argv[1:])

    context = build_context(limit=args.limit, project=args.project, include_files=not args.no_files)
    if args.json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
