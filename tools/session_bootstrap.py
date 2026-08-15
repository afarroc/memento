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
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import workspace_root

WS = Path(__file__).resolve().parent.parent
WS_ROOT = workspace_root()
SESSION_FILE = WS_ROOT / "SESSION.md"
SESSION_REPORT_FILE = WS_ROOT / "SESSION_REPORT.md"
BACKUP_DIR = WS_ROOT / ".memento_runtime" / "backups"


def _run(cmd: str, cwd: Path = WS, timeout: int = 15) -> str:
    try:
        out = subprocess.check_output(
            cmd, shell=True, cwd=str(cwd), stderr=subprocess.STDOUT, timeout=timeout
        )
        return out.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def _get_git_state(repo_path: Optional[Path] = None) -> Dict[str, Any]:
    cwd = repo_path if repo_path else WS
    branch = _run("git branch --show-current", cwd=cwd)
    if branch.startswith("ERROR:"):
        branch = "unknown"
    commit_hash = _run("git rev-parse --short HEAD", cwd=cwd)
    if commit_hash.startswith("ERROR:"):
        commit_hash = "unknown"
    commit_msg = _run("git log -1 --format=%s --abbrev-commit", cwd=cwd)
    if commit_msg.startswith("ERROR:"):
        commit_msg = "unknown"
    status_raw = _run("git status --short", cwd=cwd)
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


def _load_canonical_backup() -> Optional[Dict[str, Any]]:
    """Carga el backup canónico local inmutable (.memento_runtime/session_canonical.json)."""
    try:
        canonical_path = WS_ROOT / ".memento_runtime" / "session_canonical.json"
        if not canonical_path.exists():
            return None
        data = json.loads(canonical_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("completed_tasks"):
            return data
    except Exception:
        pass
    return None


def _load_lessons() -> List[str]:
    """Carga lecciones aprendidas desde handoff de cierre."""
    try:
        from pathlib import Path
        import re
        # Buscar el handoff más reciente con lecciones (patrón de búsqueda)
        lessons_path = None
        handoff_dir = WS_ROOT / "projects" / "mementobloom"
        if handoff_dir.exists():
            handoffs = sorted(handoff_dir.glob("HANDOFF_*_cierre_sesion*.md"), reverse=True)
            lessons_path = handoffs[0] if handoffs else None
        if not lessons_path or not lessons_path.exists():
            return []
        text = lessons_path.read_text(encoding="utf-8", errors="replace")
        lessons = []
        in_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## Lecciones aprendidas"):
                in_section = True
                continue
            if in_section and stripped.startswith("## "):
                in_section = False
            if in_section and re.match(r'^\d+\.\s', stripped):
                lessons.append(stripped[3:].strip())
        return lessons
    except Exception:
        return []


def _load_existing_session() -> Optional[Dict[str, Any]]:
    """Carga estado con fallback jerárquica: SESSION.md -> canonical -> backups -> Git."""
    # 1. Intentar SESSION.md
    if SESSION_FILE.exists():
        try:
            raw = SESSION_FILE.read_text(encoding="utf-8").strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("completed_tasks"):
                    return data
        except Exception:
            pass

    # 2. Fallback a backup canónico local
    canonical = _load_canonical_backup()
    if canonical:
        return canonical

    # 3. Fallback a backups timestamped recientes
    backup_recovered = _recover_from_backups()
    if backup_recovered:
        return backup_recovered

    # 4. Git como último recurso extremo
    return _recover_from_git() or {}


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


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _backup_session() -> None:
    if not SESSION_FILE.exists():
        return
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"session_{ts}.json"
        backup_path.write_text(SESSION_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass  # Non-fatal


def _recover_from_backups() -> Optional[Dict[str, Any]]:
    """Recupera desde backups timestamped cuando canonical no existe."""
    try:
        backup_dir = WS_ROOT / ".memento_runtime" / "backups"
        if not backup_dir.exists():
            return None
        backups = sorted(backup_dir.glob("session_*.json"), reverse=True)
        for backup_path in backups:
            try:
                data = json.loads(backup_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("completed_tasks"):
                    return data
            except Exception:
                continue
    except Exception:
        pass
    return None


def _recover_from_git() -> Optional[Dict[str, Any]]:
    try:
        raw = _run("git show HEAD:SESSION.md")
        if raw.startswith("ERROR:"):
            return None
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("completed_tasks"):
            return data
    except Exception:
        pass
    return None


def _get_client_context() -> Dict[str, Any]:
    """Detecta el proyecto cliente activo desde USER_CONTEXT.md y el último handoff relevante."""
    context: Dict[str, Any] = {
        "name": "mementobloom",
        "app": None,
        "last_commit": None,
        "entrypoints": [],
        "example": None,
        "next_step": None,
    }
    try:
        user_context_path = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
        if user_context_path.exists():
            text = user_context_path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if line.startswith("1. `") and "` (activo actual" in line:
                    project = line.split("`")[1]
                    context["name"] = project
                    break
    except Exception:
        pass
    try:
        from pathlib import Path
        import re
        project_dir = WS_ROOT / "projects" / context.get("name") if context.get("name") else None
        search_dirs = [project_dir] if project_dir else []
        search_dirs.append(WS_ROOT / "projects")
        handoffs = []
        for directory in search_dirs:
            if directory.exists():
                handoffs.extend(sorted(directory.rglob("HANDOFF_*.md"), key=lambda p: p.stat().st_mtime, reverse=True))
        handoffs = sorted(handoffs, key=lambda p: p.stat().st_mtime, reverse=True)
        for path in handoffs[:8]:
            content = path.read_text(encoding="utf-8", errors="replace")
            commit_match = re.search(r"Commit[:#]?\s*([0-9a-f]{7,40})", content)
            if commit_match:
                context["last_commit"] = commit_match.group(1)
            app_match = re.search(r"app [`']([^`']+)[`']", content)
            if app_match:
                context["app"] = app_match.group(1)
            url_matches = re.findall(r"/digitalizacion/(?:preparacion|digitalizar|qc1|metadatos|qc2|auditoria|certificar|preprocesamiento)/[^\s\)\"]+", content)
            if url_matches:
                context["entrypoints"] = url_matches[:5]
            example_match = re.search(r"Lote:\s*([^\n]+)\nDocumento:\s*([^\n]+)", content)
            if example_match:
                context["example"] = {
                    "lote": example_match.group(1).strip(),
                    "documento": example_match.group(2).strip(),
                }
            if context.get("entrypoints") or context.get("example"):
                break
    except Exception:
        pass
    return context


def _detect_active_project() -> Optional[str]:
    """Detecta el proyecto cliente activo desde USER_CONTEXT.md."""
    try:
        user_context_path = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
        if user_context_path.exists():
            text = user_context_path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if line.startswith("1. `") and "` (activo actual" in line:
                    return line.split("`")[1]
    except Exception:
        pass
    return None


def build_session() -> Dict[str, Any]:
    now = datetime.now().isoformat()
    existing = _load_existing_session() or {}
    active_project = _detect_active_project()
    client_repo = None
    if active_project:
        try:
            client_repo = WS_ROOT / "projects" / active_project
        except Exception:
            client_repo = None
    git = _get_git_state(client_repo) if client_repo and client_repo.exists() else _get_git_state()
    services = _get_services()
    memory = _get_memory()
    client_context = _get_client_context()
    session = existing.get("session", {})
    existing_services = existing.get("state", {}).get("services") if isinstance(existing.get("state"), dict) else None
    merged_services = dict(services)
    if isinstance(existing_services, dict) and existing_services:
        merged_services.update(existing_services)
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
        "active_project": client_context,
        "state": {
            "git": git,
            "services": merged_services,
            "memory": memory,
        },
        "pending_tasks": existing.get("pending_tasks") or [],
        "completed_tasks": existing.get("completed_tasks") or [],
        "blockers": existing.get("blockers") or [],
        "forbidden_paths": [
            ".agent_context/secure/*",
            "memory/**/*.json",
            "*.env",
            ".memento/**",
            "archive/**",
        ],
        "entrypoint": "python3 tools/bootstrap_context.py --print",
        "lessons_learned": _load_lessons() or existing.get("lessons_learned", []),
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
        "## Lo aprendido",
    ]
    lessons = session.get("lessons_learned") or []
    if lessons:
        for lesson in lessons:
            lines.append(f"- {lesson}")
    else:
        lines.append("- (sin lecciones registradas en el último handoff)")
    lines += [
        "",
        "## Próxima revisión",
        f"- {s.get('next_review', '?')}",
        "",
        f"```bash\n{session.get('entrypoint', '')}\n```",
    ]
    return "\n".join(lines)


def _sync_user_context(session: Dict[str, Any]) -> None:
    """Actualiza USER_CONTEXT.md con el estado actual del proyecto activo, memoria y servicios."""
    try:
        active = session.get("active_project") or {}
        project = active.get("name") or "mementobloom"
        app = active.get("app")
        entrypoints = active.get("entrypoints") or []
        example = active.get("example")
        next_step = active.get("next_step")
        git = session.get("state", {}).get("git", {})
        memory = session.get("state", {}).get("memory", {})

        # Preservar prioridades existentes del USER_CONTEXT.md si existe
        user_context_path = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
        existing_priorities: List[str] = []
        if user_context_path.exists():
            try:
                text = user_context_path.read_text(encoding="utf-8", errors="replace")
                in_section = False
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("## Proyectos prioritarios"):
                        in_section = True
                        continue
                    if in_section and stripped.startswith("## "):
                        in_section = False
                    if in_section and stripped.startswith("-"):
                        existing_priorities.append(stripped)
            except Exception:
                pass

        if not existing_priorities:
            existing_priorities = [
                f"2. `Administracion_UPN`",
                "3. `mementobloom`",
                "4. `Ventas_Porta`",
            ]

        # Asegurar que el proyecto activo esté primero
        active_line = f"1. `{project}` (activo actual — app `{app or 'N/D'}`)"
        if existing_priorities and existing_priorities[0].startswith("1."):
            existing_priorities[0] = active_line
        else:
            existing_priorities.insert(0, active_line)

        lines = [
            "# Contexto de Usuario MementoBloom",
            "",
            f"Actualizado: {session.get('session', {}).get('last_event_time', datetime.now().isoformat())}",
            "",
            "## Preferencias de comunicación",
            "",
            "- Idioma principal: español.",
            "- Estilo preferido: directo, técnico y orientado a acción.",
            "- Evitar conversación innecesaria.",
            "- Responder con resúmenes claros, comandos concretos y estado verificable.",
            "",
            "## Objetivo meta del usuario",
            "",
            "El usuario quiere que MementoBloom sea útil para que cada sesión iniciada sepa exactamente todo lo necesario sobre el usuario y el proyecto sin depender de un modelo específico.",
            "",
            "Cualquier modelo debería poder proseguir con la gestión del proyecto si puede leer:",
            "",
            "- `.agent_context/PROJECT_META.md`",
            "- `.agent_context/secure/USER_CONTEXT.md`",
            "- `.agent_context/START_CONTEXT.md`",
            "- `tools/bootstrap_context.py`",
            "- handoffs recientes",
            "- `memory/graph/memory_index.json`",
            "- estado Git",
            "- servicios locales/remotos relevantes",
            "",
            "## Proyectos prioritarios",
            "",
        ]
        lines.extend(existing_priorities)
        lines.extend([
            "",
            "## Estado actual del proyecto",
            f"- Rama principal: `{git.get('branch', '?')}`",
            f"- Último commit: `{git.get('commit_hash', '?')}` {git.get('commit_message', '')}",
            f"- Memoria indexada: {memory.get('indexed_entries', '?')} entradas",
        ])
        if entrypoints:
            lines.extend([
                "",
                "## Puntos de retorno",
            ])
            for ep in entrypoints:
                lines.append(f"- `{ep}`")
        if example:
            lines.extend([
                "",
                "## Ejemplo activo",
                f"- Lote: `{example.get('lote')}`",
                f"- Documento: `{example.get('documento')}`",
            ])
        if next_step:
            lines.extend([
                "",
                "## Próximo paso recomendado",
                f"- {next_step}",
            ])
        lines.extend([
            "",
            "## Reglas operativas preferidas",
            "",
            "- No pedir datos ya registrados en memoria.",
            "- Continuar desde el último handoff relevante.",
            "- No trackear contexto local regenerable.",
            "- No commitear sin solicitud explícita.",
            "- No ejecutar operaciones destructivas.",
            "- Publicar resúmenes en la sala cuando el usuario lo pida.",
        ])
        user_context_path = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
        user_context_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(user_context_path, "\n".join(lines) + "\n")
    except Exception:
        pass


def _sync_client_project(session: Dict[str, Any]) -> None:
    """Actualiza PROJECT_CONTEXT.md del proyecto activo y ejecuta quick_scan."""
    try:
        active = session.get("active_project") or {}
        project = active.get("name") or "mementobloom"
        app = active.get("app")
        entrypoints = active.get("entrypoints") or []
        example = active.get("example")
        last_commit = session.get("state", {}).get("git", {}).get("commit_hash")
        client_dir = WS_ROOT / "projects" / project
        context_file = client_dir / "PROJECT_CONTEXT.md"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {project} — Project Context",
            "",
            "## Visión general",
            f"- Workspace: {WS_ROOT}",
            f"- Project: {project}",
            "- Tipo: Proyecto externo / interno según corresponda",
            "",
            "## Referencia externa",
            f"- Documentación Memento: `projects/{project}/` (handoffs/, docs/)",
            "",
            "## Estado actual",
            f"- Rama principal: `main`",
        ]
        if last_commit:
            lines.append(f"- Último commit: `{last_commit}`")
        if app:
            lines.append(f"- App activa: `{app}`")
        if entrypoints:
            lines.append("- Entrypoints:")
            for ep in entrypoints:
                lines.append(f"  - `{ep}`")
        if example:
            lines.append("- Ejemplo activo:")
            lines.append(f"  - Lote: `{example.get('lote')}`")
            lines.append(f"  - Documento: `{example.get('documento')}`")
        lines += [
            "",
            "## Handoffs",
            "Ver `handoffs/` para historial de sesión.",
        ]
        _atomic_write_text(context_file, "\n".join(lines) + "\n")
    except Exception:
        pass

    try:
        _run("python3 tools/quick_scan.py")
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap unificado de sesión MementoBloom")
    parser.add_argument("--print", action="store_true", help="Alias de --json: imprime el estado de sesión como JSON por stdout")
    parser.add_argument("--json", action="store_true", help="Salida solo JSON")
    parser.add_argument("--md", action="store_true", help="Salida solo Markdown")
    parser.add_argument("--sync", action="store_true", help="Actualiza también PROJECT_CONTEXT.md del proyecto activo y ejecuta quick_scan")
    args = parser.parse_args()

    session = build_session()

    _backup_session()

    # Escribir SESSION.md (canónico JSON)
    _atomic_write_text(SESSION_FILE, render_json(session))

    # Actualizar backup canónico local (fuente de verdad inmutable)
    _update_canonical_backup(session)

    # Sync automático de proyecto cliente
    if args.sync:
        _sync_client_project(session)
        _sync_user_context(session)

    # Validación post-escritura
    try:
        reloaded = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        had_tasks = any(
            key in reloaded for key in ("pending_tasks", "completed_tasks", "blockers")
        )
        if not had_tasks:
            recovered = _recover_from_git()
            if recovered:
                for key in ("pending_tasks", "completed_tasks", "blockers"):
                    if key in recovered and key not in reloaded:
                        reloaded[key] = recovered[key]
                _atomic_write_text(SESSION_FILE, json.dumps(reloaded, ensure_ascii=False, indent=2))
    except Exception:
        pass

    # Escribir SESSION_REPORT.md (vista markdown para humanos)
    _atomic_write_text(SESSION_REPORT_FILE, render_markdown(session))

    if args.json or args.print:
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
        lessons = session.get("lessons_learned") or []
        if lessons:
            print("Lo aprendido:")
            for lesson in lessons:
                print(f"- {lesson}")
        if session["blockers"]:
            print("Bloqueos:")
            for b in session["blockers"]:
                print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
