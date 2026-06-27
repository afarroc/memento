#!/usr/bin/env python3
"""Bootstrap unificado de sesión MementoBloom.

Genera/actualiza SESSION.md (estado canónico) y SESSION.md (vista markdown).
Reemplaza el flujo múltiple de scripts por un solo comando de arranque.

Uso:
    python3 tools/session_bootstrap.py          # Modo normal
    python3 tools/session_bootstrap.py --json   # Solo JSON
    python3 tools/session_bootstrap.py --md     # Solo markdown
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import workspace_root

WS = Path(__file__).resolve().parent.parent
WS_ROOT = workspace_root()
SESSION_FILE = WS_ROOT / "SESSION.md"
SESSION_REPORT_FILE = WS_ROOT / "SESSION_REPORT.md"


def _run(cmd: str, cwd: Path = WS, timeout: int = 15) -> str:
    try:
        out = subprocess.check_output(
            cmd, shell=True, cwd=str(cwd), stderr=subprocess.STDOUT, timeout=timeout
        )
        return out.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def _get_git_state() -> Dict[str, Any]:
    branch = _run("git branch --show-current")
    if branch.startswith("ERROR:"):
        branch = "unknown"
    commit_hash = _run("git rev-parse --short HEAD")
    if commit_hash.startswith("ERROR:"):
        commit_hash = "unknown"
    commit_msg = _run("git log -1 --format=%s --abbrev-commit")
    if commit_msg.startswith("ERROR:"):
        commit_msg = "unknown"
    status_raw = _run("git status --short")
    pending = [line for line in status_raw.splitlines() if line.strip()] if not status_raw.startswith("ERROR:") else []
    return {
        "branch": branch,
        "commit_hash": commit_hash,
        "commit_message": commit_msg,
        "pending_count": len(pending),
        "pending": pending[:10],
    }


def _get_services() -> Dict[str, str]:
    doctor = _run("python3 tools/doctor.py --startup")
    services = {"sala": "NO", "panel": "NO", "redis": "NO"}
    for line in doctor.splitlines():
        low = line.lower()
        if "sala:" in low and "ok" in low:
            services["sala"] = "OK"
        if "panel:" in low and "ok" in low:
            services["panel"] = "OK"
        if "redis:" in low:
            services["redis"] = line.split(":", 1)[1].strip().split()[0].upper()
    return services


def _get_memory() -> Dict[str, Any]:
    scan = _run("python3 tools/quick_scan.py")
    entries = 0
    manifest_ts = ""
    for line in scan.splitlines():
        if "Total:" in line:
            try:
                entries = int(line.split("Total:")[1].split()[0])
            except Exception:
                pass
        if "Manifest:" in line:
            manifest_ts = line.split("Manifest:")[1].strip()
    return {"indexed_entries": entries, "manifest_ts": manifest_ts}


def _load_existing_session() -> Optional[Dict[str, Any]]:
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_session() -> Dict[str, Any]:
    now = datetime.now().isoformat()
    existing = _load_existing_session() or {}
    git = _get_git_state()
    services = _get_services()
    memory = _get_memory()
    session = existing.get("session", {})
    return {
        "session": {
            "project": "mementobloom",
            "role": "asistente-gtd",
            "workspace": str(WS_ROOT),
            "last_event_time": now,
            "last_event_type": "bootstrap",
            "last_event_summary": git.get("commit_message", "Sesión iniciada"),
            "git_branch": git["branch"],
            "git_commit": git["commit_hash"],
            "generated_at": now,
            "next_review": (datetime.now() + timedelta(hours=24)).isoformat(),
        },
        "state": {
            "git": git,
            "services": services,
            "memory": memory,
        },
        "pending_tasks": existing.get("pending_tasks") or [
            {"id": "T2.1", "description": "Portabilidad memento_install (sed macOS/Linux)", "status": "pending", "sprint": 2},
            {"id": "T2.2", "description": "Declarar dependencias mínimas en requirements.txt", "status": "pending", "sprint": 2},
            {"id": "T2.3", "description": "Dockerfile + docker-compose.yml de referencia", "status": "pending", "sprint": 2},
            {"id": "T2.4", "description": "Lockfiles y procedimiento de reproducible build", "status": "pending", "sprint": 2},
            {"id": "MB-Auth", "description": "Definir estrategia auth para escritura en /api/v1/ (POST/PATCH)", "status": "pending"},
            {"id": "MB-Redis", "description": "Resolver disponibilidad de Redis para panel/sala", "status": "blocked"},
            {"id": "MB-Docs", "description": "Actualizar docs/PROJECT_CONTEXT.md para reflejar nueva estructura", "status": "pending"},
        ],
        "blockers": existing.get("blockers") or [],
        "forbidden_paths": [
            ".agent_context/secure/*",
            "memory/**/*.json",
            "*.env",
            ".memento/**",
            "archive/**",
        ],
        "entrypoint": "python3 tools/session_bootstrap.py",
    }


def render_json(session: Dict[str, Any]) -> str:
    return json.dumps(session, ensure_ascii=False, indent=2)


def render_markdown(session: Dict[str, Any]) -> str:
    s = session.get("session", {})
    st = session.get("state", {})
    lines = [
        "# SESSION — Estado canónico de sesión",
        "",
        f"- **Proyecto:** {s.get('project', '?')}",
        f"- **Rol:** {s.get('role', '?')}",
        f"- **Workspace:** {s.get('workspace', '?')}",
        f"- **Generado:** {s.get('generated_at', '?')}",
        f"- **Último evento:** {s.get('last_event_time', '?')} ({s.get('last_event_type', '?')}): {s.get('last_event_summary', '?')}",
        "",
        "## Git",
        f"- Rama: {st.get('git', {}).get('branch', '?')}",
        f"- Commit: {st.get('git', {}).get('commit_hash', '?')} — {st.get('git', {}).get('commit_message', '?')}",
        f"- Pendientes: {st.get('git', {}).get('pending_count', 0)}",
        "",
        "## Servicios",
    ]
    svcs = st.get("services", {})
    lines.append(f"- Sala: {svcs.get('sala', '?')}")
    lines.append(f"- Panel: {svcs.get('panel', '?')}")
    lines.append(f"- Redis: {svcs.get('redis', '?')}")
    lines += [
        "",
        "## Memoria",
        f"- Entradas indexadas: {st.get('memory', {}).get('indexed_entries', 0)}",
        "",
        "## Tareas pendientes",
    ]
    for t in session.get("pending_tasks", []):
        lines.append(f"- [{t.get('status', '?')}] {t.get('id', '?')}: {t.get('description', '?')}")
    lines += [
        "",
        "## Bloqueos",
    ]
    for b in session.get("blockers", []):
        lines.append(f"- {b}")
    lines += [
        "",
        "## Próxima revisión",
        f"- {s.get('next_review', '?')}",
        "",
        f"```bash\n{session.get('entrypoint', '')}\n```",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap unificado de sesión MementoBloom")
    parser.add_argument("--json", action="store_true", help="Salida solo JSON")
    parser.add_argument("--md", action="store_true", help="Salida solo Markdown")
    args = parser.parse_args()

    session = build_session()

    # Escribir SESSION.md (canónico JSON)
    SESSION_FILE.write_text(render_json(session), encoding="utf-8")

    # Escribir SESSION_REPORT.md (vista markdown para humanos)
    SESSION_REPORT_FILE.write_text(render_markdown(session), encoding="utf-8")

    if args.json:
        print(render_json(session))
    elif args.md:
        print(render_markdown(session))
    else:
        print("SESSION.md actualizado.")
        print(f"Proyecto: {session['session']['project']}")
        print(f"Rama: {session['state']['git']['branch']}")
        print(f"Servicios: sala={session['state']['services']['sala']}, panel={session['state']['services']['panel']}, redis={session['state']['services']['redis']}")
        print(f"Memoria: {session['state']['memory']['indexed_entries']} entradas")
        print(f"Pendientes: {len(session['pending_tasks'])} tareas")
        if session["blockers"]:
            print("Bloqueos:")
            for b in session["blockers"]:
                print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
