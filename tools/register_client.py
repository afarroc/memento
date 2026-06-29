#!/usr/bin/env python3
"""Register a new client project in MementoBloom workspace.

Creates conventional project structure with proper isolation:
- projects/CLIENT_NAME/handoffs/
- projects/CLIENT_NAME/PROJECT_CONTEXT.md
- projects/CLIENT_NAME/src/, projects/CLIENT_NAME/memory/

Uso:
    python3 tools/register_client.py --name Ventas_Porta
    python3 tools/register_client.py --name Administracion_UPN --from-project ../otros_proyectos/Admin_UPN
"""

from __future__ import annotations

import argparse
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Register a new client project in MementoBloom")
    parser.add_argument("--name", "-n", required=True, help="Client project name (used for folder name)")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace root (default: current mementobloom)")
    parser.add_argument("--from-project", "-s", default=None, help="Source project to import assets from")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    ws = Path(args.workspace).resolve() if args.workspace else WS
    src = Path(args.from_project).resolve() if args.from_project else None

    result = register_client(args.name, workspace=ws, source_project=src)

    if args.json:
        import json
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