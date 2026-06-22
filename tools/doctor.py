#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.health import ensure_memory_manifest, startup_health
from core.paths import ROOT, rel


def format_startup(report: Dict[str, Any]) -> str:
    health = report.get("health", {})
    memory = report.get("memory", {})
    git = report.get("git", {})
    services = report.get("services", {})
    status = "OK" if report.get("ok") else "FAIL"
    lines = [
        "MementoBloom Doctor",
        f"Status: {status}",
        f"Project: {ROOT.name}",
        f"Working directory: {ROOT}",
        "",
        "Checks:",
    ]
    checks = [
        ("Project meta exists", health.get("project_meta_exists")),
        ("Project meta tracked", health.get("project_meta_tracked")),
        ("User context optional", health.get("user_context_optional")),
        ("Start context optional", health.get("start_context_optional")),
        ("Agent init exists", health.get("agent_init_exists")),
        ("Agent seed exists", health.get("agent_seed_exists")),
        ("Memory index exists", health.get("memory_index_exists")),
        ("Memory index empty (clean install)", health.get("memory_index_empty")),
    ]
    # Services are optional; only report if checked
    if health.get("services_checked") is True:
        checks.append(("Services checked", True))
    elif health.get("services_checked") is False:
        checks.append(("Services optional", True))
    for name, value in checks:
        if value is True:
            if name == "Memory index empty (clean install)":
                state = "OK (vacío)"
            else:
                state = "OK"
        elif value is False:
            if name == "Memory index empty (clean install)":
                state = "OK (con entradas)"
            else:
                state = "FAIL"
        else:
            state = "OPTIONAL"
        lines.append(f"  - {name}: {state}")

    latest = git.get("latest", {})
    git_status = git.get("status", {})
    lines.extend([
        "",
        "Git:",
        f"  - Commit: {latest.get('hash', '?')} {latest.get('message', '')}".strip(),
        f"  - Pending changes: {git_status.get('change_count', 0)}",
        "",
        "Memory:",
        f"  - Index: {memory.get('index_path', '?')}",
        f"  - Entries: {memory.get('entries', 0)}",
        f"  - By type: {json.dumps(memory.get('by_type', {}), ensure_ascii=False)}",
    ])

    if services.get("checked") is False:
        lines.append("  - Services: not checked")
    else:
        lines.extend([
            "",
            "Services:",
            f"  - Redis: {'OK' if services.get('redis', {}).get('ok') else 'NO'} at {services.get('redis', {}).get('host', '?')}:{services.get('redis', {}).get('port', '?')}",
            f"  - Sala: {'OK' if services.get('sala', {}).get('ok') else 'NO'} at {services.get('sala', {}).get('url', '?')}",
            f"  - Panel: {'OK' if services.get('panel', {}).get('ok') else 'NO'} at {services.get('panel', {}).get('url', '?')}",
            f"  - From cache: {services.get('from_cache', False)}",
        ])

    recommendations = []
    if not health.get("project_meta_exists"):
        recommendations.append("Crear .agent_context/PROJECT_META.md")
    if not health.get("project_meta_tracked"):
        recommendations.append("Quitar PROJECT_META.md de .gitignore")
    if not health.get("memory_index_exists"):
        recommendations.append("Crear índice inicial con python3 tools/quick_scan.py --index memory/graph/memory_index.json")
    if not health.get("agent_init_exists") or not health.get("agent_seed_exists"):
        recommendations.append("Ejecutar ./memento_start --prepare-seed")
    if not recommendations:
        recommendations.append("No hay bloqueantes de instalación limpia")

    lines.extend([
        "",
        "Recommendations:",
    ])
    for item in recommendations:
        lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico de instalación y arranque de MementoBloom")
    parser.add_argument("--startup", action="store_true", help="Ejecuta diagnóstico de instalación limpia")
    parser.add_argument("--json", action="store_true", help="Imprime reporte en JSON")
    parser.add_argument("--index", default=None, help="Ruta del índice de memoria")
    parser.add_argument("--no-services", action="store_true", help="No verificar servicios")
    parser.add_argument("--fresh-health", action="store_true", help="Forzar chequeo de servicios sin usar caché")
    parser.add_argument("--manifest", action="store_true", help="Actualizar index_manifest.json antes de diagnosticar")
    args = parser.parse_args(argv or sys.argv[1:])

    index_path = Path(args.index) if args.index else None
    if args.manifest:
        ensure_memory_manifest(index_path)
    report = startup_health(index_path=index_path, check_services=not args.no_services, fresh_health=args.fresh_health)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_startup(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
