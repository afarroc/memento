#!/usr/bin/env python3
"""Delta semántico entre backups de SESSION.md.

Compara el SESSION.md actual con el último backup disponible y genera:
- Cambios en tareas (nuevas, completadas, bloqueadas)
- Cambios en bloqueos
- Cambios en servicios
- Resumen de cambios desde última sesión

Uso:
    python3 tools/session_diff.py
    python3 tools/session_diff.py --backup 20260627_145339
    python3 tools/session_diff.py --json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

WS = Path(__file__).resolve().parent.parent
BACKUPS_DIR = WS / ".backups"
SESSION_FILE = WS / "SESSION.md"


def _load_backup_sessions() -> List[Path]:
    if not BACKUPS_DIR.exists():
        return []
    sessions = []
    for child in BACKUPS_DIR.iterdir():
        if child.is_dir():
            sessions.append(child)
    return sorted(sessions, reverse=True)


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _session_to_set(session: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae conjuntos comparables del estado."""
    pending = session.get("pending_tasks", [])
    blockers = session.get("blockers", [])
    services = session.get("state", {}).get("services", {})
    return {
        "pending_ids": sorted({t.get("id") for t in pending if t.get("id")}),
        "pending_descriptions": sorted({t.get("description") for t in pending if t.get("description")}),
        "blockers": sorted({b.strip() for b in blockers if b and b.strip()}),
        "services": {k: v for k, v in services.items()},
    }


def _compute_diff(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    current_set = _session_to_set(current)
    previous_set = _session_to_set(previous) if previous else {}

    diff = {
        "compared_at": datetime.now().isoformat(),
        "previous_session": previous.get("session", {}).get("last_event_time") if previous else None,
        "current_session": current.get("session", {}).get("last_event_time"),
        "tasks": {
            "added": sorted(set(current_set["pending_ids"]) - set(previous_set.get("pending_ids", []))),
            "removed": sorted(set(previous_set.get("pending_ids", [])) - set(current_set["pending_ids"])),
        },
        "blockers": {
            "added": sorted(set(current_set["blockers"]) - set(previous_set.get("blockers", []))),
            "removed": sorted(set(previous_set.get("blockers", [])) - set(current_set["blockers"])),
        },
        "services_changed": [],
    }

    # Detectar cambios en servicios
    prev_services = previous_set.get("services", {}) if previous else {}
    for key in set(list(current_set["services"].keys()) + list(prev_services.keys())):
        if current_set["services"].get(key) != prev_services.get(key):
            diff["services_changed"].append({
                "service": key,
                "from": prev_services.get(key, "?"),
                "to": current_set["services"].get(key, "?"),
            })

    return diff


def render_text(diff: Dict[str, Any]) -> str:
    lines = [
        "# Delta semántico de sesión",
        "",
        f"- Generado: {diff['compared_at']}",
        f"- Sesión anterior: {diff['previous_session'] or 'N/A'}",
        f"- Sesión actual: {diff['current_session']}",
        "",
        "## Tareas",
    ]
    tasks = diff.get("tasks", {})
    if tasks.get("added"):
        lines.append(f"- Agregadas: {', '.join(tasks['added'])}")
    if tasks.get("removed"):
        lines.append(f"- Removidas: {', '.join(tasks['removed'])}")
    if not any(tasks.values()):
        lines.append("- Sin cambios")
    lines += [
        "",
        "## Bloqueos",
    ]
    blockers = diff.get("blockers", {})
    if blockers.get("added"):
        lines.append(f"- Agregados: {', '.join(blockers['added'])}")
    if blockers.get("removed"):
        lines.append(f"- Removidos: {', '.join(blockers['removed'])}")
    if not any(blockers.values()):
        lines.append("- Sin cambios")
    lines += [
        "",
        "## Servicios",
    ]
    for chg in diff.get("services_changed", []):
        lines.append(f"- {chg['service']}: {chg['from']} → {chg['to']}")
    if not diff.get("services_changed"):
        lines.append("- Sin cambios")
    return "\n".join(lines) + "\n"


def render_json(diff: Dict[str, Any]) -> str:
    return json.dumps(diff, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Delta semántico entre backups de SESSION.md")
    parser.add_argument("--backup", help="Timestamp del backup a comparar (ej. 20260627_145339)")
    parser.add_argument("--json", action="store_true", help="Salida en JSON")
    args = parser.parse_args()

    current = _read_json(SESSION_FILE)
    if not current:
        print("ERROR: No existe SESSION.md actual")
        return 1

    previous = None
    if args.backup:
        backup_dir = BACKUPS_DIR / args.backup
        if backup_dir.exists():
            previous = _read_json(backup_dir / "SESSION.md")
    else:
        sessions = _load_backup_sessions()
        for sess in sessions:
            candidate = sess / "SESSION.md"
            if candidate.exists():
                previous = _read_json(candidate)
                break

    diff = _compute_diff(current, previous)

    if args.json:
        print(render_json(diff))
    else:
        print(render_text(diff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
