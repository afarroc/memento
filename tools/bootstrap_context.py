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
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve workspace first before importing core modules
from core.path_resolver import RESOLVER
WS_ROOT = RESOLVER.WS_ROOT
MEMENTO_ROOT = RESOLVER.ROOT
SCRIPT_ROOT = MEMENTO_ROOT

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
PERSONALITY = WS_ROOT / "memory" / "personality" / "user_personality.md"
AGENT_INSTRUCTIONS_DIR = WS_ROOT / ".agent_context" / "agent" / "instructions"


def _load_agent_instructions() -> Dict[str, Any]:
    """Carga todos los archivos de instrucciones del agente como parte obligatoria del contexto."""
    result: Dict[str, Any] = {
        "exists": False,
        "path": rel(AGENT_INSTRUCTIONS_DIR),
        "files": {},
        "total_files": 0,
        "summary": "",
    }
    if not AGENT_INSTRUCTIONS_DIR.exists() or not AGENT_INSTRUCTIONS_DIR.is_dir():
        return result
    md_files = sorted(AGENT_INSTRUCTIONS_DIR.glob("*.md"))
    if not md_files:
        return result
    result["exists"] = True
    result["total_files"] = len(md_files)
    parts: List[str] = []
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8", errors="replace")
        result["files"][md_file.name] = {
            "path": rel(md_file),
            "lines": len(text.splitlines()),
            "chars": len(text),
        }
        # Extract first meaningful line after title for summary
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parts.append(stripped)
                break
    result["summary"] = " ".join(parts[:10])
    return result


def load_project_priority() -> List[str]:
    if not USER_CONTEXT.exists():
        return []
    text = USER_CONTEXT.read_text(encoding="utf-8", errors="replace")
    in_section = False
    priorities: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_section = line.lower() in {"## proyectos activos", "## proyectos prioritarios"}
            continue
        if not in_section or not line.startswith("-"):
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            priorities.append(match.group(1))
    return priorities


def discover_projects_from_fs() -> List[str]:
    projects_dir = WS_ROOT / "projects"
    if not projects_dir.exists():
        return []
    found: List[str] = []
    for entry in projects_dir.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            has_context = (entry / "PROJECT_CONTEXT.md").exists()
            has_handoffs = (entry / "handoffs").exists() and any((entry / "handoffs").glob("HANDOFF_*.md"))
            if has_context or has_handoffs:
                found.append(entry.name)
    return sorted(found)


def discover_projects_from_memory(index: List[Dict[str, Any]], max_entries: int = 50) -> List[str]:
    seen: Dict[str, int] = {}
    for entry in index[:max_entries]:
        project = entry.get("project")
        if project:
            seen[project] = seen.get(project, 0) + 1
    return [name for name, _ in sorted(seen.items(), key=lambda x: x[1], reverse=True)]


def merged_active_projects(index_entries: List[Dict[str, Any]]) -> List[str]:
    manual = load_project_priority()
    fs_projects = discover_projects_from_fs()
    memory_projects = discover_projects_from_memory(index_entries)
    merged: List[str] = []
    seen = set()
    for name in manual + fs_projects + memory_projects:
        if name not in seen:
            merged.append(name)
            seen.add(name)
    return merged


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
    fast_mode: bool = False,
) -> Dict[str, Any]:
    from core.path_resolver import RESOLVER
    if RESOLVER.MODO == "dev":
        print(f"⚠️  MODO DEV: ROOT == WS_ROOT en {RESOLVER.ROOT}")
        print("   Los handoffs de mementobloom se resolverán como 'self' (proyecto propio)")
    else:
        print(f"✅ MODO INSTALADO: ROOT={RESOLVER.ROOT}, WS_ROOT={RESOLVER.WS_ROOT}")
    index_file = resolve_index_path(str(index_path) if index_path else None, workspace=WS_ROOT)
    index = load_index(index_file)
    entries = top_entries(index, limit, project=project)
    handoffs = latest_handoffs(index, 5, project=project)
    project_meta = read_file(PROJECT_META) if include_files else {"exists": PROJECT_META.exists(), "path": rel(PROJECT_META)}
    user_context = read_file(USER_CONTEXT) if include_files else {"exists": USER_CONTEXT.exists(), "path": rel(USER_CONTEXT)}
    start_context = read_file(START_CONTEXT) if include_files else {"exists": START_CONTEXT.exists(), "path": rel(START_CONTEXT)}
    agent_init = read_file(AGENT_INIT) if include_files else {"exists": AGENT_INIT.exists(), "path": rel(AGENT_INIT)}
    personality = read_file(PERSONALITY) if include_files and not fast_mode else {"exists": PERSONALITY.exists(), "path": rel(PERSONALITY), "fast_skipped": fast_mode}
    agent_instructions = _load_agent_instructions() if include_files else {"exists": AGENT_INSTRUCTIONS_DIR.exists(), "path": rel(AGENT_INSTRUCTIONS_DIR)}
    services = service_status(fresh=fresh_health) if check_services else {"checked": False, "reason": "services disabled"}
    active_projects = merged_active_projects([entry for entry in index.values() if isinstance(entry, dict)])
    return {
        "generated_at": now_iso(),
        "environment": {
            "working_directory": str(WS_ROOT),
            "workspace_root": str(WS_ROOT),
            "project": project or WS_ROOT.name,
        },
        "files": {
            "project_meta": project_meta,
            "user_context": user_context,
            "start_context": start_context,
            "agent_init": agent_init,
            "agent_instructions": agent_instructions,
            "personality": personality,
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
        "active_projects": active_projects,
        "top_context": entries,
        "latest_handoffs": handoffs,
        "services": services,
        "fast_mode": fast_mode,
        "bootstrap_commands": {
            "universal": "python3 tools/session_start.py --print  # Flujo único de arranque del agente main",
            "internal": "python3 tools/bootstrap_context.py --print  # Herramienta interna usada por session_start.py",
            "startup_doctor": "python3 tools/doctor.py --startup",
            "selftest": "python3 tools/selftest.py",
            "ranked_context": "python3 tools/context_builder.py --limit 12",
            "quick_scan": "python3 tools/quick_scan.py <HANDOFF_PATH>",
            "memory_tree": "python3 tools/memory_tree.py [--domain X --tags Y]  # Context Tree (Domain>Tema>Entry, sin volcar contenido)",
        },
    }


def format_markdown(context: Dict[str, Any]) -> str:
    git = context.get("git", {})
    commit = git.get("latest_commit", {})
    status = git.get("status", {})
    memory = context.get("memory", {})
    services_data = context.get("services", {})
    files = context.get("files", {})
    fast_mode = context.get("fast_mode", False)
    lines = [
        "# MementoBloom Bootstrap Context",
        "",
        f"Generated: {context.get('generated_at')}",
        f"Project: {context.get('environment', {}).get('project')}",
        f"Working directory: {rel(Path(context.get('environment', {}).get('working_directory', '.')))}",
        f"Mode: {'fast' if fast_mode else 'full'}",
        "",
        "## User and project meta",
        f"- PROJECT_META.md: {'OK' if files.get('project_meta', {}).get('exists') else 'NO'}",
        f"- USER_CONTEXT.md: {'OK' if files.get('user_context', {}).get('exists') else 'OPTIONAL'}",
        f"- START_CONTEXT.md: {'OK' if files.get('start_context', {}).get('exists') else 'OPTIONAL'}",
        f"- Agent init: {'OK' if files.get('agent_init', {}).get('exists') else 'NO'}",
        f"- Agent instructions: {'OK' if files.get('agent_instructions', {}).get('exists') else 'NO'} ({files.get('agent_instructions', {}).get('total_files', 0)} files)",
        f"- USER_CONTEXT ignored by Git: {'OK' if files.get('user_context_ignored', {}).get('ignored') else 'NO'}",
        "",
        "## Project meta summary",
        files.get("project_meta", {}).get("summary", "No project meta file found."),
        "",
        "## User context summary",
        files.get("user_context", {}).get("summary", "No user context file found or optional."),
        "",
        "## Agent instructions",
        files.get("agent_instructions", {}).get("summary", "No agent instructions found.") if not fast_mode else "(omitido en modo rápido)",
        "",
        "## Personality",
        files.get("personality", {}).get("summary", "No personality file found.") if not fast_mode else "(omitido en modo rápido)",
        "",
        "## Git state",
        f"- Rama: {commit.get('branch', '?')}",
        f"- Commit: {commit.get('hash', '?')} {commit.get('message', '')}".strip(),
        f"- Pendientes: {status.get('change_count', 0)}",
    ]
    changes = status.get("changes", [])
    if changes:
        lines.append("- Cambios:")
        for change in changes:
            lines.append(f"  - {change}")
    else:
        lines.append("- Cambios: ninguno")
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
        "## Active projects",
    ])
    for idx, name in enumerate(context.get("active_projects", []), 1):
        lines.append(f"{idx}. {name}")
    lines.extend(["", "## Latest handoffs"])
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

    if not fast_mode:
        lines.extend(_build_bootstrap_checklist(context, files, status, services_data, context.get("latest_handoffs", [])))

    lines.extend([
        "",
        "## Bootstrap commands",
        "- python3 tools/session_start.py --print  # Flujo único de arranque del agente main",
        "- python3 tools/bootstrap_context.py --print  # Herramienta interna de contexto universal",
        "- python3 tools/bootstrap_context.py --fast   # Modo rápido opcional",
        "- python3 tools/doctor.py --startup",
        "- python3 tools/selftest.py",
        "- python3 tools/context_builder.py --limit 12",
        "- python3 tools/quick_scan.py <HANDOFF_PATH>",
        "",
        "## Optional agent-specific commands",
        "- python3 tools/optimize_agent.py --context",
    ])
    return "\n".join(lines) + "\n"


def _build_bootstrap_checklist(
    context: Dict[str, Any],
    files: Dict[str, Any],
    status: Dict[str, Any],
    services_data: Dict[str, Any],
    handoffs: List[Dict[str, Any]],
) -> List[str]:
    commit = context.get("git", {}).get("latest_commit", {})
    checks = [
        (
            "1",
            "PROJECT_META",
            files.get("project_meta", {}).get("exists"),
            "Leer PROJECT_META.md",
        ),
        (
            "2",
            "USER_CONTEXT",
            files.get("user_context", {}).get("exists"),
            "Leer USER_CONTEXT.md",
        ),
        (
            "3",
            "PERSONALITY",
            files.get("personality", {}).get("exists"),
            "Leer user_personality.md",
        ),
        (
            "4",
            "AGENT_INIT",
            files.get("agent_init", {}).get("exists"),
            "Leer agent/init.md",
        ),
        (
            "4.1",
            "AGENT_INSTRUCTIONS",
            files.get("agent_instructions", {}).get("exists"),
            "Cargar TODAS las instrucciones de agent/instructions/*.md (obligatorio para agente main)",
        ),
        (
            "5",
            "START_CONTEXT",
            files.get("start_context", {}).get("exists"),
            "Leer START_CONTEXT.md",
        ),
        (
            "6",
            "BOOTSTRAP",
            True,
            "Ejecutar bootstrap_context.py --print",
        ),
        (
            "7",
            "SESSION_BOOTSTRAP",
            None,
            "Ejecutar session_bootstrap.py --print (flujo externo, opcional)",
        ),
        (
            "8",
            "HANDOFFS",
            len(handoffs) > 0,
            f"Leer handoffs recientes ({len(handoffs)} encontrados)",
        ),
        (
            "9",
            "GIT",
            commit.get("hash") is not None,
            "Verificar Git (rama, commit y status)",
        ),
        (
            "10",
            "SERVICES",
            services_data.get("checked") is not False,
            "Verificar Redis/sala/panel",
        ),
        (
            "11",
            "CONTINUITY",
            True,
            "Continuar desde último handoff relevante",
        ),
    ]
    lines = [
        "",
        "## Bootstrap checklist (11 pasos)",
        "",
    ]
    for num, key, ok, desc in checks:
        if key == "USER_CONTEXT" and ok is False:
            icon = "OPTIONAL"
        elif key == "START_CONTEXT" and ok is False:
            icon = "OPTIONAL"
        elif key == "SESSION_BOOTSTRAP":
            icon = "INFO"
        elif ok:
            icon = "OK"
        else:
            icon = "NO"
        lines.append(f"- [{num}] {icon}: {desc}")
    return lines


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _backup_session(session_file: Path) -> None:
    if not session_file.exists():
        return
    try:
        backup_dir = WS_ROOT / ".memento_runtime" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"session_{ts}.json"
        backup_path.write_text(session_file.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass


def _recover_from_git() -> Optional[Dict[str, Any]]:
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", str(WS_ROOT), "show", "HEAD:SESSION.md"],
            stderr=subprocess.DEVNULL,
            timeout=5,
            text=True,
        )
        data = json.loads(out)
        if isinstance(data, dict) and data.get("completed_tasks"):
            return data
    except Exception:
        pass
    return None


def _validate_session_schema(session: Dict[str, Any]) -> None:
    required_top = {"session", "state", "forbidden_paths", "entrypoint"}
    missing = required_top - session.keys()
    if missing:
        raise ValueError(f"SESIÓN inválida: faltan secciones {missing}")
    required_session = {"project", "role", "workspace", "last_event_time", "last_event_type", "last_event_summary", "git_branch", "git_commit", "generated_at"}
    missing = required_session - session["session"].keys()
    if missing:
        raise ValueError(f"SESIÓN inválida: faltan campos en 'session' {missing}")
    required_state = {"git", "services", "memory"}
    missing = required_state - session["state"].keys()
    if missing:
        raise ValueError(f"SESIÓN inválida: faltan secciones en 'state' {missing}")


def _update_canonical_backup(session: Dict[str, Any]) -> None:
    """Actualiza el backup canónico local con el estado actual de la sesión."""
    try:
        canonical_path = WS_ROOT / ".memento_runtime" / "session_canonical.json"
        canonical_path.parent.mkdir(parents=True, exist_ok=True)
        backup = dict(session)
        backup["canonical_version"] = 1
        backup["last_verified"] = datetime.now().isoformat(timespec="seconds")
        canonical_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass  # Non-fatal


def write_session_md(context: Dict[str, Any]) -> Dict[str, Any]:
    session_file = WS_ROOT / "SESSION.md"
    git = context.get("git", {})
    services_data = context.get("services", {})
    memory = context.get("memory", {})
    active_projects = context.get("active_projects", [])

    # Cargar sesión existente para preservar secciones que no se regeneran aquí
    existing_session: Dict[str, Any] = {}
    if session_file.exists():
        try:
            raw = session_file.read_text(encoding="utf-8")
            if raw.strip():
                existing_session = json.loads(raw)
        except Exception:
            existing_session = {}

    # Fallback a git si faltan datos operativos en el archivo actual
    if not existing_session.get("completed_tasks"):
        recovered = _recover_from_git()
        if recovered:
            existing_session.setdefault("completed_tasks", recovered.get("completed_tasks", []))
            existing_session.setdefault("pending_tasks", recovered.get("pending_tasks", []))
            existing_session.setdefault("blockers", recovered.get("blockers", []))
            existing_session.setdefault("lessons_learned", recovered.get("lessons_learned", []))

    # Validar que lo que vamos a escribir cumpla el esquema mínimo
    session: Dict[str, Any] = {
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
        "entrypoint": "python3 tools/bootstrap_context.py --print",
    }

    # Reconstruir activos desde memoria / filesystem cuando corresponda
    if active_projects:
        new_active_project = {
            "name": active_projects[0],
            "app": None,
            "last_commit": None,
            "entrypoints": [],
            "example": None,
            "next_step": None,
        }
        # Fusionar con active_project existente para preservar campos extra (app, last_commit, entrypoints)
        existing_active_project = existing_session.get("active_project")
        if isinstance(existing_active_project, dict):
            merged_active_project = dict(existing_active_project)
            merged_active_project.update(new_active_project)
            session["active_project"] = merged_active_project
        else:
            session["active_project"] = new_active_project
        session["active_projects"] = active_projects

    # Preservar secciones operativas existentes si están presentes y no fueron reconstruidas arriba
    for key in ("pending_tasks", "completed_tasks", "blockers", "lessons_learned"):
        if key in existing_session:
            session[key] = existing_session[key]

    # Preservar state.services existente (puede tener formato enriquecido)
    existing_services = existing_session.get("state", {}).get("services") if isinstance(existing_session.get("state"), dict) else None
    if isinstance(existing_services, dict) and existing_services:
        session["state"]["services"] = existing_services

    _backup_session(session_file)
    _validate_session_schema(session)
    _atomic_write_json(session_file, session)

    # Validación post-escritura: asegurar que las secciones operativas no desaparezcan
    try:
        reloaded = json.loads(session_file.read_text(encoding="utf-8"))
        had_tasks = any(
            key in reloaded for key in ("pending_tasks", "completed_tasks", "blockers", "active_project", "active_projects")
        )
        if not had_tasks:
            recovered = _recover_from_git()
            if recovered:
                for key in ("pending_tasks", "completed_tasks", "blockers", "active_project", "active_projects"):
                    if key in recovered and key not in reloaded:
                        reloaded[key] = recovered[key]
                _atomic_write_json(session_file, reloaded)
    except Exception:
        pass
    return session


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
    parser.add_argument("--fast", action="store_true", help="Arranque rápido: omite checklist detallado y lectura de personalidad")
    args = parser.parse_args(argv or sys.argv[1:])

    context = build_context(
        limit=args.limit,
        project=args.project,
        include_files=not args.no_files,
        index_path=Path(args.index) if args.index else None,
        check_services=not args.no_services,
        fresh_health=args.fresh_health,
        fast_mode=args.fast,
    )

    session = write_session_md(context)
    _update_canonical_backup(session)

    if args.json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
