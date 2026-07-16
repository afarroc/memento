#!/usr/bin/env python3
"""Register a new client project in MementoBloom workspace.

Creates conventional project structure with proper isolation:
- projects/CLIENT_NAME/handoffs/
- projects/CLIENT_NAME/PROJECT_CONTEXT.md
- projects/CLIENT_NAME/src/, projects/CLIENT_NAME/memory/

Uso:
    python3 tools/register_client.py --name Ventas_Porta
    python3 tools/register_client.py --name Administracion_UPN --from-project ../otros_proyectos/Admin_UPN
    python3 tools/register_client.py --sync
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Optional


WS = Path(__file__).resolve().parent.parent


def register_client(name: str, workspace: Optional[Path] = None, source_project: Optional[Path] = None) -> dict:
    ws = workspace or WS
    client_dir = ws / "projects" / name

    created = []
    skipped = []

    # Estructura convencional
    dirs = [
        client_dir / "handoffs",
        client_dir / "src",
        client_dir / "memory" / "graph",
        client_dir / "docs",
    ]

    for d in dirs:
        if d.exists():
            skipped.append(str(d.relative_to(ws)))
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(ws)))

    # PROJECT_CONTEXT.md placeholder
    context_file = client_dir / "PROJECT_CONTEXT.md"
    if context_file.exists():
        skipped.append(str(context_file.relative_to(ws)))
    else:
        context_file.write_text(
            f"# {name} — Project Context\n\n"
            f"## Visión general\n"
            f"- Workspace: {ws}\n"
            f"- Project: {name}\n\n"
            f"## Handoffs\n"
            f"Ver `handoffs/` para historial de sesión.\n",
            encoding="utf-8"
        )
        created.append(str(context_file.relative_to(ws)))

    # .gitignore para cliente
    gitignore = client_dir / ".gitignore"
    if gitignore.exists():
        skipped.append(str(gitignore.relative_to(ws)))
    else:
        gitignore.write_text(
            "# Client-specific exclusions\n"
            "memory/graph/*.json\n"
            "handoffs/*.md\n"
            ".env\n"
            "__pycache__/\n",
            encoding="utf-8"
        )
        created.append(str(gitignore.relative_to(ws)))

    # Copiar desde proyecto fuente si existe
    if source_project and source_project.exists():
        src_contents = source_project / "Ciclo_01"
        if src_contents.exists():
            dst_src = client_dir / "src" / "Ciclo_01"
            if not dst_src.exists():
                shutil.copytree(src_contents, dst_src)
                created.append(str(dst_src.relative_to(ws)))

    # Inicializar memory_index vacío para cliente
    client_index = client_dir / "memory" / "graph" / "memory_index.json"
    if not client_index.exists():
        client_index.write_text("{}", encoding="utf-8")
        created.append(str(client_index.relative_to(ws)))

    return {
        "workspace": str(ws),
        "client": name,
        "client_dir": str(client_dir),
        "created": created,
        "skipped": skipped,
        "ok": True,
    }


def _parse_project_context(context_path: Path) -> dict:
    text = context_path.read_text(encoding="utf-8", errors="replace")
    data: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        # Fuente/local del proyecto cliente
        m = re.search(r"-\s*(?:Fuente cliente|Source|Project root|Workspace cliente):\s*(.+)", stripped)
        if m:
            data["source"] = m.group(1).strip()
            continue
        # venv
        m = re.search(r"-\s*(?:Entorno venv|venv):\s*(.+)", stripped)
        if m:
            data["venv"] = m.group(1).strip()
            continue
        # repo
        m = re.search(r"-\s*\*\*Repo(?: GitHub)?:\*\*\s*(.+)", stripped)
        if m:
            repo_text = m.group(1).strip()
            data["repo"] = repo_text
            branch = re.search(r"rama\s+`([^`]+)`", repo_text)
            if branch:
                data["branch"] = branch.group(1).strip()
            continue
        # producción / URL
        m = re.search(r"-\s*\*\*(?:URL|Producción):\*\*\s*(https?://[^\s—]+)", stripped)
        if m:
            data["production"] = m.group(1).strip()
            continue
        # documentación Memento
        m = re.search(r"-\s*Documentación Memento:\s*(.+)", stripped)
        if m:
            data["memento_docs"] = m.group(1).strip()
            continue
    return data


def sync_client_projects(workspace: Optional[Path] = None) -> dict:
    ws = workspace or WS
    projects_dir = ws / "projects"
    secure_dir = ws / ".agent_context" / "secure"
    secure_dir.mkdir(parents=True, exist_ok=True)
    output_path = secure_dir / "client_projects.json"

    registry: dict[str, dict] = {}
    if not projects_dir.exists():
        return {"ok": True, "projects": registry, "output": str(output_path)}

    for context_file in projects_dir.rglob("PROJECT_CONTEXT.md"):
        try:
            project_name = context_file.parent.name
            data = _parse_project_context(context_file)
            if data:
                registry[project_name] = data
        except Exception:
            continue

    output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "projects": registry,
        "output": str(output_path),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Register a new client project in MementoBloom")
    parser.add_argument("--name", "-n", default=None, help="Client project name (used for folder name)")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace root (default: current mementobloom)")
    parser.add_argument("--from-project", "-s", default=None, help="Source project to import assets from")
    parser.add_argument("--sync", action="store_true", help="Scan projects/*/PROJECT_CONTEXT.md and write .agent_context/secure/client_projects.json")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    ws = Path(args.workspace).resolve() if args.workspace else WS

    if args.sync:
        result = sync_client_projects(workspace=ws)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"client_projects.json actualizado: {result['output']}")
            print(f"Proyectos registrados: {len(result['projects'])}")
            for name, meta in result["projects"].items():
                print(f"  + {name}: {meta.get('source', '-')}")
        return 0 if result["ok"] else 1

    if not args.name:
        parser.error("--name es requerido si no usas --sync")

    src = Path(args.from_project).resolve() if args.from_project else None
    result = register_client(args.name, workspace=ws, source_project=src)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Cliente registrado: {result['client']}")
        print(f"Directorio: {result['client_dir']}")
        print(f"Creados: {len(result['created'])}")
        for item in result["created"]:
            print(f"  + {item}")
        print(f"Saltados: {len(result['skipped'])}")
        for item in result["skipped"]:
            print(f"  = {item}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
