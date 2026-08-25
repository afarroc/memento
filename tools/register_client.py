#!/usr/bin/env python3
"""Register, update, migrate and validate client projects in MementoBloom workspace.

This tool is the single source of truth for client project structure.
It can:
- register a new client with canonical structure and rich context
- update an existing client without destroying existing content
- migrate all registered clients to the current structure version
- validate structure completeness
- list registered clients with metadata summary
- sync global registry from PROJECT_CONTEXT.md files

Uso:
    python3 tools/register_client.py --name Ventas_Porta
    python3 tools/register_client.py --name Administracion_UPN --from-project ../otros_proyectos/Admin_UPN
    python3 tools/register_client.py --update Ventas_Porta
    python3 tools/register_client.py --migrate-all --dry-run
    python3 tools/register_client.py --migrate-all
    python3 tools/register_client.py --validate
    python3 tools/register_client.py --list
    python3 tools/register_client.py --sync
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


WS = Path(__file__).resolve().parent.parent
PROJECTS_BASE = Path(os.environ.get("MEMENTO_PROJECTS_BASE", WS / "projects"))
SCHEMA_VERSION = "1.1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kebab_case(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or name


def _rel(ws: Path, path: Path) -> str:
    try:
        return str(path.relative_to(ws))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

PROJECT_CONTEXT_TEMPLATE = """\
# {name} — Project Context

## Identidad
- Proyecto: {name}
- Nombre canonico: {name}
- Tipo: {project_type}
- Dominio memoria: {memory_domain}

## Fuente
- Ruta local: {source}
- Repo GitHub: {repo}
- Rama: {branch}

## Entorno
- venv: {venv}
- Producción: {production}
- Servicios: {services}

## Relación con mementobloom
- Documentación Memento: {memento_docs}
- Notas: {notes}

## Estado
- Registrado: {registered_at}
- Última actualización estructura: {last_structure_update}
- Handoffs: {handoffs_count}
- Memoria indexada: {memory_entries} entries

## Próximos pasos
- {next_steps}

---

*Este archivo es la fuente de verdad del registro del cliente.*
*No editar manualmente campos generados por herramientas.*
"""

README_CLIENT_TEMPLATE = """\
# {name}

Resumen operativo del proyecto cliente {name}.

## Vínculo mementobloom
- Documentación: `docs/`
- Handoffs: `handoffs/`
- Contexto: `PROJECT_CONTEXT.md`

## Comandos útiles
- Ver estado: `python3 tools/project_status.py`
- Actualizar estructura: `python3 tools/register_client.py --update {name}`
"""

GITIGNORE_CLIENT_TEMPLATE = """\
# Client-specific exclusions
memory/graph/*.json
handoffs/*.md
.env
__pycache__/
.agent_context/START_CONTEXT.md
.memento_runtime/
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_handoffs(client_dir: Path) -> int:
    return len(list(client_dir.rglob("HANDOFF*.md")))


def _count_memory_entries(client_dir: Path) -> int:
    index = client_dir / "memory" / "graph" / "memory_index.json"
    if not index.exists():
        return 0
    try:
        data = json.loads(index.read_text(encoding="utf-8") or "{}")
        if isinstance(data, dict):
            return len(data)
        return 0
    except Exception:
        return 0


def _detect_project_type(client_dir: Path, name: str) -> str:
    if name == "Management360":
        return "cliente"
    marker = client_dir / "src"
    if marker.exists() and any(marker.iterdir()):
        return "cliente"
    return "documentacion"


def _detect_memory_domain(name: str) -> str:
    return name


def _detect_services(client_dir: Path, name: str) -> str:
    services = []
    if name == "Management360":
        services.extend(["m360", "redis", "sala", "panel"])
    if (client_dir / "src").exists():
        services.append("src")
    return ", ".join(services) if services else "—"


def _detect_next_steps(name: str) -> str:
    mapping = {
        "Management360": "Completar code review pendiente y sync SPRINT_1-5",
        "Administracion_UPN": "Completar pipeline digitalización UPN",
        "Ventas_Porta": "Definir backlog y nomenclatura items",
    }
    return mapping.get(name, "Actualizar PROJECT_CONTEXT.md y handoffs")


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def ensure_structure(client_dir: Path, ws: Path) -> Dict[str, Any]:
    dirs = [
        client_dir / "handoffs",
        client_dir / "src",
        client_dir / "memory" / "graph",
        client_dir / "docs" / "guides",
        client_dir / "docs" / "runbooks",
        client_dir / "docs" / "reference",
    ]
    created = []
    skipped = []
    for d in dirs:
        if d.exists():
            skipped.append(_rel(ws, d))
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(_rel(ws, d))
    return {"created": created, "skipped": skipped}


def ensure_readme(client_dir: Path, name: str, ws: Path, force: bool = False) -> Dict[str, Any]:
    readme = client_dir / "README.md"
    if readme.exists() and not force:
        return {"created": [], "skipped": [_rel(ws, readme)]}
    readme.write_text(README_CLIENT_TEMPLATE.format(name=name), encoding="utf-8")
    return {"created": [_rel(ws, readme)], "skipped": []}


def ensure_gitignore(client_dir: Path, ws: Path, force: bool = False) -> Dict[str, Any]:
    gitignore = client_dir / ".gitignore"
    if gitignore.exists() and not force:
        return {"created": [], "skipped": [_rel(ws, gitignore)]}
    gitignore.write_text(GITIGNORE_CLIENT_TEMPLATE, encoding="utf-8")
    return {"created": [_rel(ws, gitignore)], "skipped": []}


def ensure_project_context(
    client_dir: Path,
    name: str,
    ws: Path,
    force: bool = False,
    refresh: bool = False,
) -> Dict[str, Any]:
    context_file = client_dir / "PROJECT_CONTEXT.md"
    now = _now()

    if context_file.exists() and not force and not refresh:
        return {"created": [], "skipped": [_rel(ws, context_file)], "updated": False}

    existing = {}
    if context_file.exists():
        existing = _parse_project_context(context_file)

    project_type = existing.get("project_type") or _detect_project_type(client_dir, name)
    memory_domain = existing.get("memory_domain") or _detect_memory_domain(name)
    source = existing.get("source") or _rel(ws, client_dir)
    repo = existing.get("repo") or "—"
    branch = existing.get("branch") or "—"
    venv = existing.get("venv") or "—"
    production = existing.get("production") or "—"
    services = existing.get("services") or _detect_services(client_dir, name)
    memento_docs = existing.get("memento_docs") or f"projects/{name}/"
    notes = existing.get("notes") or ""
    registered_at = existing.get("registered_at") or now
    last_structure_update = now
    handoffs_count = existing.get("handoffs_count") or _count_handoffs(client_dir)
    memory_entries = existing.get("memory_entries") or _count_memory_entries(client_dir)
    next_steps = existing.get("next_steps") or _detect_next_steps(name)

    content = PROJECT_CONTEXT_TEMPLATE.format(
        name=name,
        project_type=project_type,
        memory_domain=memory_domain,
        source=source,
        repo=repo,
        branch=branch,
        venv=venv,
        production=production,
        services=services,
        memento_docs=memento_docs,
        notes=notes,
        registered_at=registered_at,
        last_structure_update=last_structure_update,
        handoffs_count=handoffs_count,
        memory_entries=memory_entries,
        next_steps=next_steps,
    )

    context_file.write_text(content, encoding="utf-8")
    updated = context_file.exists() and bool(existing)
    return {
        "created": [] if updated else [_rel(ws, context_file)],
        "skipped": [] if updated else [],
        "updated": updated,
    }


def register_client(
    name: str,
    workspace: Optional[Path] = None,
    source_project: Optional[Path] = None,
    force: bool = False,
) -> dict:
    ws = workspace or WS
    name = _kebab_case(name)
    client_dir = PROJECTS_BASE / name

    if not client_dir.exists():
        client_dir.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    updated = []

    # 1. estructura
    result = ensure_structure(client_dir, ws)
    created.extend(result["created"])
    skipped.extend(result["skipped"])

    # 2. .gitignore
    result = ensure_gitignore(client_dir, ws, force=force)
    created.extend(result["created"])
    skipped.extend(result["skipped"])

    # 3. PROJECT_CONTEXT.md
    result = ensure_project_context(client_dir, name, ws, force=force)
    if result.get("created"):
        created.extend(result["created"])
    if result.get("skipped"):
        skipped.extend(result["skipped"])
    if result.get("updated"):
        updated.append("PROJECT_CONTEXT.md")

    # 4. README
    result = ensure_readme(client_dir, name, ws, force=force)
    created.extend(result["created"])
    skipped.extend(result["skipped"])

    # 5. source import
    if source_project and source_project.exists():
        src_contents = source_project / "Ciclo_01"
        if src_contents.exists():
            dst_src = client_dir / "src" / "Ciclo_01"
            if not dst_src.exists():
                shutil.copytree(src_contents, dst_src)
                created.append(_rel(ws, dst_src))

    # 6. memory index placeholder
    client_index = client_dir / "memory" / "graph" / "memory_index.json"
    if not client_index.exists():
        client_index.write_text("{}", encoding="utf-8")
        created.append(_rel(ws, client_index))

    return {
        "workspace": str(ws),
        "client": name,
        "client_dir": str(client_dir),
        "created": created,
        "skipped": skipped,
        "updated": updated,
        "ok": True,
    }


# ---------------------------------------------------------------------------
# Update / migrate
# ---------------------------------------------------------------------------

def update_client(name: str, workspace: Optional[Path] = None, force: bool = False, dry_run: bool = False) -> dict:
    ws = workspace or WS
    name = _kebab_case(name)
    client_dir = PROJECTS_BASE / name

    if not client_dir.exists():
        return {"ok": False, "error": f"Cliente no encontrado: {name}", "path": str(client_dir)}

    created = []
    skipped = []
    updated = []

    checks = []

    result = ensure_structure(client_dir, ws)
    created.extend(result["created"])
    skipped.extend(result["skipped"])
    checks.append(("estructura", len(result["created"]), len(result["skipped"])))

    result = ensure_gitignore(client_dir, ws, force=force)
    created.extend(result["created"])
    skipped.extend(result["skipped"])
    if result.get("created"):
        updated.append(".gitignore")
    checks.append((".gitignore", len(result["created"]), len(result["skipped"])))

    result = ensure_project_context(client_dir, name, ws, force=force, refresh=True)
    if result.get("created"):
        created.extend(result["created"])
    if result.get("skipped"):
        skipped.extend(result["skipped"])
    if result.get("updated"):
        updated.append("PROJECT_CONTEXT.md")
    checks.append(("PROJECT_CONTEXT.md", len(result.get("created", [])), len(result.get("skipped", []))))

    result = ensure_readme(client_dir, name, ws, force=force)
    created.extend(result["created"])
    skipped.extend(result["skipped"])
    if result.get("created"):
        updated.append("README.md")
    checks.append(("README.md", len(result["created"]), len(result["skipped"])))

    if dry_run:
        return {
            "ok": True,
            "client": name,
            "client_dir": str(client_dir),
            "dry_run": True,
            "would_create": created,
            "would_skip": skipped,
            "would_update": updated,
            "checks": checks,
        }

    return {
        "ok": True,
        "client": name,
        "client_dir": str(client_dir),
        "created": created,
        "skipped": skipped,
        "updated": updated,
        "checks": checks,
    }


def migrate_all(workspace: Optional[Path] = None, force: bool = False, dry_run: bool = False) -> dict:
    ws = workspace or WS
    projects_dir = PROJECTS_BASE
    if not projects_dir.exists():
        return {"ok": True, "clients": [], "dry_run": dry_run}

    results = []
    for client_dir in sorted(projects_dir.iterdir()):
        if not client_dir.is_dir():
            continue
        name = client_dir.name
        result = update_client(name, workspace=ws, force=force, dry_run=dry_run)
        results.append(result)

    return {
        "ok": True,
        "clients": results,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Validate / list
# ---------------------------------------------------------------------------

def validate_client(name: str, workspace: Optional[Path] = None) -> dict:
    ws = workspace or WS
    name = _kebab_case(name)
    client_dir = PROJECTS_BASE / name

    required = [
        client_dir / "handoffs",
        client_dir / "docs",
        client_dir / "docs" / "guides",
        client_dir / "docs" / "runbooks",
        client_dir / "docs" / "reference",
        client_dir / "memory" / "graph",
        client_dir / "PROJECT_CONTEXT.md",
        client_dir / "README.md",
        client_dir / ".gitignore",
    ]
    missing = [str(p.relative_to(ws)) for p in required if not p.exists()]
    return {
        "ok": len(missing) == 0,
        "client": name,
        "missing": missing,
        "valid": len(missing) == 0,
    }


def validate_all(workspace: Optional[Path] = None) -> dict:
    ws = workspace or WS
    projects_dir = PROJECTS_BASE
    results = []
    if projects_dir.exists():
        for client_dir in sorted(projects_dir.iterdir()):
            if client_dir.is_dir():
                results.append(validate_client(client_dir.name, workspace=ws))
    return {
        "ok": all(r["ok"] for r in results),
        "clients": results,
    }


def list_clients(workspace: Optional[Path] = None) -> dict:
    ws = workspace or WS
    projects_dir = PROJECTS_BASE
    clients = []
    if projects_dir.exists():
        for client_dir in sorted(projects_dir.iterdir()):
            if not client_dir.is_dir():
                continue
            name = client_dir.name
            context = client_dir / "PROJECT_CONTEXT.md"
            ctx_data = _parse_project_context(context) if context.exists() else {}
            handoffs = _count_handoffs(client_dir)
            memory = _count_memory_entries(client_dir)
            clients.append({
                "name": name,
                "path": _rel(ws, client_dir),
                "source": ctx_data.get("source", "—"),
                "repo": ctx_data.get("repo", "—"),
                "branch": ctx_data.get("branch", "—"),
                "production": ctx_data.get("production", "—"),
                "handoffs": handoffs,
                "memory_entries": memory,
                "has_context": context.exists(),
            })
    return {
        "ok": True,
        "clients": clients,
        "count": len(clients),
    }


# ---------------------------------------------------------------------------
# Sync client_projects.json
# ---------------------------------------------------------------------------

def _parse_project_context(context_path: Path) -> dict:
    text = context_path.read_text(encoding="utf-8", errors="replace")
    data: Dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        m = re.search(r"-\s*(?:Fuente local|Ruta local|Source|Workspace cliente|Project root):\s*(.+)", stripped)
        if m:
            data["source"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*(?:Entorno venv|venv):\s*(.+)", stripped)
        if m:
            data["venv"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*\*\*Repo(?: GitHub)?:\*\*\s*(.+)", stripped)
        if m:
            repo_text = m.group(1).strip()
            data["repo"] = repo_text
            branch = re.search(r"rama\s+`([^`]+)`", repo_text)
            if branch:
                data["branch"] = branch.group(1).strip()
            continue
        m = re.search(r"-\s*\*\*(?:URL|Producción):\*\*\s*(https?://[^\s—]+)", stripped)
        if m:
            data["production"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Documentación Memento:\s*(.+)", stripped)
        if m:
            data["memento_docs"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Tipo:\s*(.+)", stripped)
        if m:
            data["project_type"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Dominio memoria:\s*(.+)", stripped)
        if m:
            data["memory_domain"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Registrado:\s*(.+)", stripped)
        if m:
            data["registered_at"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Última actualización estructura:\s*(.+)", stripped)
        if m:
            data["last_structure_update"] = m.group(1).strip()
            continue
        m = re.search(r"-\s*Handoffs:\s*(\d+)", stripped)
        if m:
            data["handoffs_count"] = int(m.group(1))
            continue
        m = re.search(r"-\s*Memoria indexada:\s*(\d+)", stripped)
        if m:
            data["memory_entries"] = int(m.group(1))
            continue
    return data


def sync_client_projects(workspace: Optional[Path] = None) -> dict:
    ws = workspace or WS
    projects_dir = PROJECTS_BASE
    secure_dir = ws / ".agent_context" / "secure"
    secure_dir.mkdir(parents=True, exist_ok=True)
    output_path = secure_dir / "client_projects.json"

    registry: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "last_synced": _now(),
        "projects": {},
    }
    if not projects_dir.exists():
        output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"ok": True, "projects": registry, "output": str(output_path)}

    for context_file in projects_dir.rglob("PROJECT_CONTEXT.md"):
        try:
            project_name = context_file.parent.name
            data = _parse_project_context(context_file)
            if not data:
                continue
            registry["projects"][project_name] = {
                "project": project_name,
                "canonical_name": data.get("canonical_name") or project_name,
                "type": data.get("project_type") or "cliente",
                "domain": data.get("memory_domain") or project_name,
                "source": data.get("source") or str(context_file.parent.relative_to(ws)),
                "repo": data.get("repo") or None,
                "branch": data.get("branch") or None,
                "venv": data.get("venv") or None,
                "produccion": data.get("production") or None,
                "servicios": [s.strip() for s in data.get("services", "").split(",") if s.strip() and s.strip() != "—"],
                "memento_docs": data.get("memento_docs") or f"projects/{project_name}/",
                "registered_at": data.get("registered_at"),
                "last_structure_update": data.get("last_structure_update"),
                "handoffs_count": data.get("handoffs_count") or _count_handoffs(context_file.parent),
                "memory_entries": data.get("memory_entries") or _count_memory_entries(context_file.parent),
            }
        except Exception:
            continue

    output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "projects": registry,
        "output": str(output_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Register, update, migrate and validate client projects in MementoBloom")
    parser.add_argument("--name", "-n", default=None, help="Client project name (used for folder name)")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace root (default: current mementobloom)")
    parser.add_argument("--from-project", "-s", default=None, help="Source project to import assets from")
    parser.add_argument("--sync", action="store_true", help="Scan projects/*/PROJECT_CONTEXT.md and write .agent_context/secure/client_projects.json")
    parser.add_argument("--update", "-u", default=None, help="Update existing client structure without destroying content")
    parser.add_argument("--migrate-all", action="store_true", help="Update all registered clients to current structure")
    parser.add_argument("--validate", action="store_true", help="Validate structure completeness of all clients")
    parser.add_argument("--list", action="store_true", help="List registered clients with metadata summary")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files (PROJECT_CONTEXT.md, README.md, .gitignore)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    ws = Path(args.workspace).resolve() if args.workspace else WS
    result: Dict[str, Any] = {"ok": False}

    if args.sync:
        result = sync_client_projects(workspace=ws)
        if not args.json:
            print(f"client_projects.json actualizado: {result['output']}")
            print(f"Proyectos registrados: {len(result.get('projects', {}).get('projects', {}))}")
            for name, meta in result.get("projects", {}).get("projects", {}).items():
                print(f"  + {name}: {meta.get('source', '-')}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.list:
        result = list_clients(workspace=ws)
        if not args.json:
            print(f"Clientes registrados: {result['count']}")
            for c in result.get("clients", []):
                print(f"  + {c['name']}: {c['path']} (handoffs={c['handoffs']}, memoria={c['memory_entries']})")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.validate:
        result = validate_all(workspace=ws)
        if not args.json:
            print(f"Validación: {'OK' if result['ok'] else 'FAIL'}")
            for c in result.get("clients", []):
                status = "OK" if c["valid"] else f"FALTAN: {', '.join(c['missing'])}"
                print(f"  {c['client']}: {status}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.migrate_all:
        result = migrate_all(workspace=ws, force=args.force, dry_run=args.dry_run)
        if not args.json:
            print(f"Migrate-all (dry_run={args.dry_run})")
            for c in result.get("clients", []):
                client = c.get("client", "?")
                if c.get("dry_run"):
                    print(f"  [dry-run] {client}: crearía {len(c.get('would_create', []))}, preservaría {len(c.get('would_skip', []))}, actualizaría {len(c.get('would_update', []))}")
                else:
                    print(f"  {client}: creados={len(c.get('created', []))}, preservados={len(c.get('skipped', []))}, actualizados={len(c.get('updated', []))}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.update:
        result = update_client(args.update, workspace=ws, force=args.force, dry_run=args.dry_run)
        if not args.json:
            if result.get("dry_run"):
                print(f"[dry-run] Update {args.update}: crearía {len(result.get('would_create', []))}, preservaría {len(result.get('would_skip', []))}, actualizaría {len(result.get('would_update', []))}")
            else:
                print(f"Update {args.update}: creados={len(result.get('created', []))}, preservados={len(result.get('skipped', []))}, actualizados={len(result.get('updated', []))}")
                if result.get("created"):
                    for item in result["created"]:
                        print(f"  + {item}")
                if result.get("updated"):
                    for item in result["updated"]:
                        print(f"  ~ {item}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if not args.name:
        parser.error("--name es requerido si no usas --sync, --list, --validate o --migrate-all")

    name = _kebab_case(args.name)
    if name != args.name:
        print(f"Nombre normalizado: {args.name} -> {name}")

    src = Path(args.from_project).resolve() if args.from_project else None
    result = register_client(name, workspace=ws, source_project=src, force=args.force)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Cliente registrado: {result['client']}")
        print(f"Directorio: {result['client_dir']}")
        print(f"Creados: {len(result['created'])}")
        for item in result["created"]:
            print(f"  + {item}")
        print(f"Preservados: {len(result['skipped'])}")
        for item in result["skipped"]:
            print(f"  = {item}")
        if result.get("updated"):
            print(f"Actualizados: {len(result['updated'])}")
            for item in result["updated"]:
                print(f"  ~ {item}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
