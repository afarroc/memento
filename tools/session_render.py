#!/usr/bin/env python3
"""Renderiza SESSION.md a Markdown para consumo humano.

Uso:
    python3 tools/session_render.py
    python3 tools/session_render.py --input SESSION.md --output SESSION.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
DEFAULT_SESSION = WS / "SESSION.md"
DEFAULT_OUTPUT = WS / "SESSION_REPORT.md"


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
    parser = argparse.ArgumentParser(description="Renderiza SESSION.md a Markdown")
    parser.add_argument("--input", type=Path, default=DEFAULT_SESSION, help="Ruta a SESSION.md JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Ruta de salida markdown")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: No existe {args.input}")
        return 1

    session = json.loads(args.input.read_text(encoding="utf-8"))
    md = render_markdown(session)
    args.output.write_text(md, encoding="utf-8")
    print(f"Renderizado guardado en: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
