#!/usr/bin/env python3
"""Reporte consolidado del estado del proyecto MementoBloom.

Genera un snapshot único con:
- Git (rama, commits, pendientes)
- Memoria (índice, manifiesto)
- Servicios (sala, panel, Redis)
- Backups locales
- Proyectos externos
- Próximos pasos sugeridos

Uso:
    python3 tools/project_status.py
    python3 tools/project_status.py --format json
    python3 tools/project_status.py --format markdown
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

WS = Path(__file__).resolve().parent.parent


def _run(cmd: str, cwd: Path = WS, timeout: int = 20) -> str:
    try:
        out = subprocess.check_output(
            cmd, shell=True, cwd=str(cwd), stderr=subprocess.STDOUT, timeout=timeout
        )
        return out.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def _git_info() -> Dict[str, Any]:
    branch = _run("git branch --show-current")
    status = _run("git status --short")
    log_raw = _run("git log --oneline -3 --date=short")
    commits = []
    if not log_raw.startswith("ERROR:"):
        for line in log_raw.splitlines():
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            if len(parts) >= 2:
                commits.append({"hash": parts[0], "subject": parts[1]})
    ahead_raw = _run("git rev-list --count origin/master..HEAD")
    ahead = 0
    if not ahead_raw.startswith("ERROR:") and ahead_raw.strip().isdigit():
        ahead = int(ahead_raw.strip())
    return {
        "branch": branch if not branch.startswith("ERROR:") else "unknown",
        "pending": [line for line in status.splitlines() if line.strip()] if not status.startswith("ERROR:") else [],
        "commits": commits,
        "ahead": ahead,
    }


def _memory_info() -> Dict[str, Any]:
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


def _services_info() -> Dict[str, Any]:
    doctor = _run("python3 tools/doctor.py --startup")
    services = {"redis": "NO", "sala": "NO", "panel": "NO"}
    # Parse doctor output using case-insensitive matching for each service marker
    for line in doctor.splitlines():
        low = line.lower()
        if "redis:" in low:
            # Extract the status word after "redis:"
            parts = line.split(":", 1)
            if len(parts) > 1:
                status = parts[1].strip().split()[0].upper()
                if status in {"OK", "PONG"}:
                    services["redis"] = "OK"
                else:
                    services["redis"] = "NO"
        if "sala:" in low:
            status = line.split(":", 1)[1].strip().split()[0].upper()
            services["sala"] = "OK" if status == "OK" else "NO"
        if "panel:" in low:
            status = line.split(":", 1)[1].strip().split()[0].upper()
            services["panel"] = "OK" if status == "OK" else "NO"
    return services


def _backup_info() -> Dict[str, Any]:
    backups_dir = WS / ".backups"
    if not backups_dir.exists():
        return {"count": 0, "latest": None}
    items = sorted([p for p in backups_dir.iterdir() if p.is_dir()], reverse=True)
    latest = items[0].name if items else None
    return {"count": len(items), "latest": latest}


def _projects_info() -> Dict[str, Any]:
    base = WS / "projects"
    projects = {}
    if not base.exists():
        return projects
    for child in base.iterdir():
        if not child.is_dir():
            continue
        handoffs = list(child.glob("HANDOFF_*.md"))
        projects[child.name] = {"path": str(child.relative_to(WS)), "handoffs": len(handoffs)}
    return projects


def _next_steps(services: Dict[str, Any], backups: Dict[str, Any]) -> list:
    steps = []
    if services.get("redis") == "NO":
        steps.append("Resolver disponibilidad de Redis para panel/sala")
    if backups.get("count", 0) == 0:
        steps.append("Ejecutar backup inicial: python3 tools/backup_local.py backup")
    steps.append("Avanzar Sprint 2 (T2.1-T2.4): portabilidad, dependencias, Docker")
    steps.append("Definir estrategia de auth para escritura en /api/v1/ (POST/PATCH)")
    return steps


def build_report() -> Dict[str, Any]:
    git = _git_info()
    memory = _memory_info()
    services = _services_info()
    backups = _backup_info()
    projects = _projects_info()
    return {
        "generated_at": datetime.now().isoformat(),
        "git": git,
        "memory": memory,
        "services": services,
        "backups": backups,
        "projects": projects,
        "next_steps": _next_steps(services, backups),
    }


def render_text(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Estado del Proyecto MementoBloom")
    lines.append(f"Generado: {report['generated_at']}")
    lines.append(f"Rama: {report['git']['branch']}")
    lines.append(f"Commits: {', '.join(c['hash'] for c in report['git']['commits'])}\n")

    lines.append("## Pendientes")
    for p in report["git"]["pending"]:
        lines.append(f"- {p}")

    lines.append("\n## Memoria")
    lines.append(f"- Entradas indexadas: {report['memory']['indexed_entries']}")
    lines.append(f"- Manifest: {report['memory']['manifest_ts']}")

    lines.append("\n## Servicios")
    for k, v in report["services"].items():
        lines.append(f"- {k}: {v}")

    lines.append("\n## Backups")
    lines.append(f"- Count: {report['backups']['count']}")
    if report["backups"]["latest"]:
        lines.append(f"- Latest: {report['backups']['latest']}")

    lines.append("\n## Proyectos externos")
    for name, meta in report["projects"].items():
        lines.append(f"- {name}: {meta['path']} ({meta['handoffs']} handoffs)")

    lines.append("\n## Próximos pasos")
    for s in report["next_steps"]:
        lines.append(f"- {s}")
    return "\n".join(lines)


def render_markdown(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("| Campo | Valor |")
    lines.append("|-------|-------|")
    lines.append(f"| Generado | {report['generated_at']} |")
    lines.append(f"| Rama | {report['git']['branch']} |")
    if report["git"]["commits"]:
        lines.append(f"| Último commit | {report['git']['commits'][0]['hash']} — {report['git']['commits'][0]['subject']} |")
    lines.append(f"| Memoria | {report['memory']['indexed_entries']} entradas |")
    lines.append(f"| Backups | {report['backups']['count']} (latest: {report['backups']['latest']}) |")
    services = report["services"]
    lines.append(f"| Sala | {services.get('sala','?')} |")
    lines.append(f"| Panel | {services.get('panel','?')} |")
    lines.append(f"| Redis | {services.get('redis','?')} |")
    return "\n".join(lines)


def render_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reporte de estado del proyecto MementoBloom")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("--output", type=Path, help="Guardar reporte en archivo")
    args = parser.parse_args()

    report = build_report()
    if args.format == "json":
        out = render_json(report)
    elif args.format == "markdown":
        out = render_markdown(report)
    else:
        out = render_text(report)

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"Reporte guardado en: {args.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
