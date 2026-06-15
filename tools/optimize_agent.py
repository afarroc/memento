#!/usr/bin/env python3
"""Optimiza el contexto operativo del agente MementoBloom.

La herramienta audita semilla, memoria, servicios, Git y seguridad; genera
resúmenes compactos para continuar sesiones; puede publicar en la sala local y
crear handoffs estructurados. No ejecuta operaciones destructivas por defecto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "memory" / "graph" / "memory_index.json"
START_CONTEXT = ROOT / ".kilo" / "START_CONTEXT.md"
PROJECT_META = ROOT / ".kilo" / "PROJECT_META.md"
USER_CONTEXT = ROOT / ".kilo" / "USER_CONTEXT.md"
AGENT_DIR = ROOT / ".kilo" / "agent"
AGENT_INIT = AGENT_DIR / "init.md"
AGENT_SEED = AGENT_DIR / "memento-curador.md"
INSTRUCTION_DIR = AGENT_DIR / "instructions"
HANDOFF_DIR = ROOT / "projects" / "mementobloom"
REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.18.59")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
REDIS_QUEUE = os.environ.get("REDIS_QUEUE", "memento_panel_items")
PROJECT_PRIORITY = ["mementobloom", "Management360", "Ventas_Porta"]
DEFAULT_CONTEXT_LIMIT = 8
SECRET_PATTERNS = [
    ("api_key", re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w\-]{8,}")),
    ("token", re.compile(r"(?i)(token|access_token|refresh_token)\s*[:=]\s*['\"]?[\w\-\.]{12,}")),
    ("password", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}")),
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("vault_secret", re.compile(r"(?i)(secret|credential|clave)\s*[:=]\s*['\"]?[^\s'\"]{8,}")),
]
IGNORED_PATHS = [
    ".kilo/START_CONTEXT.md",
    ".kilo/USER_CONTEXT.md",
    "memory/graph/*.json",
    ".memento/",
    ".memento_runtime/",
    "archive/",
    "session_record.json",
    "sessions/",
    "memory/sessions/",
    ".panel_messages.json",
    ".chat_waiter_state.json",
    "config.json",
    "*HANDOFF*.md",
    "*_CONTEXT.md",
]


@dataclass
class CommandResult:
    ok: bool
    stdout: str
    stderr: str = ""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def run_command(args: List[str], timeout: int = 10) -> CommandResult:
    try:
        proc = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            ok=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except Exception as exc:
        return CommandResult(ok=False, stdout="", stderr=str(exc))


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_index() -> Dict[str, Dict[str, Any]]:
    return load_json(INDEX_PATH, {}) if INDEX_PATH.exists() else {}


def parse_ts(value: str) -> datetime:
    text = str(value or "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return datetime.min


def entry_sort_key(entry: Dict[str, Any]) -> tuple[Any, ...]:
    ts = parse_ts(str(entry.get("ts", "")))
    project = str(entry.get("project", ""))
    type_name = str(entry.get("type", ""))
    priority = PROJECT_PRIORITY.index(project) if project in PROJECT_PRIORITY else 99
    type_priority = {"HANDOFF": 0, "SOURCE": 1, "NOTE": 2, "CONTEXT": 3, "COMPONENT": 4}.get(type_name, 50)
    return (ts, -priority, -type_priority, str(entry.get("id", "")))


def top_entries(index: Dict[str, Dict[str, Any]], limit: int, project: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = list(index.values())
    if project:
        entries = [entry for entry in entries if str(entry.get("project")) == project]
    entries.sort(key=entry_sort_key, reverse=True)
    return entries[:limit]


def count_by(entries: Iterable[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in entries:
        value = str(entry.get(field, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def git_status() -> Dict[str, Any]:
    raw = run_command(["git", "-C", str(ROOT), "status", "--short"])
    lines = [line for line in raw.stdout.splitlines() if line.strip()]
    return {
        "ok": raw.ok,
        "raw": raw.stdout,
        "changes": lines,
        "change_count": len(lines),
        "error": raw.stderr or raw.stdout if not raw.ok else "",
    }


def git_diff_stat() -> Dict[str, Any]:
    result = run_command(["git", "-C", str(ROOT), "diff", "--stat"])
    return {"ok": result.ok, "text": result.stdout, "error": result.stderr if not result.ok else ""}


def latest_commit() -> Dict[str, Any]:
    result = run_command(["git", "-C", str(ROOT), "log", "-1", "--oneline"])
    parts = result.stdout.split(" ", 1) if result.stdout else []
    return {
        "ok": result.ok,
        "hash": parts[0] if parts else "",
        "message": parts[1] if len(parts) > 1 else "",
        "raw": result.stdout,
        "error": result.stderr if not result.ok else "",
    }


def git_check_ignore(path: str) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(ROOT), "check-ignore", "-v", path])
    return {"path": path, "ignored": result.ok, "rule": result.stdout.strip(), "error": result.stderr.strip() if not result.ok else ""}


def redis_ping(timeout: float = 1.0) -> Dict[str, Any]:
    try:
        with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=timeout) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(128).decode(errors="replace")
        return {"ok": "PONG" in data, "detail": data.strip(), "host": REDIS_HOST, "port": REDIS_PORT}
    except OSError as exc:
        return {"ok": False, "detail": str(exc), "host": REDIS_HOST, "port": REDIS_PORT}


def http_json(url: str, timeout: float = 1.0) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw[:500]}
            return {"ok": 200 <= response.status < 500, "status": response.status, "data": parsed}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def service_status() -> Dict[str, Any]:
    sala = http_json(f"http://127.0.0.1:{SALA_PORT}/stats")
    panel = http_json(f"http://127.0.0.1:{PANEL_PORT}/stats")
    return {
        "redis": redis_ping(timeout=0.6),
        "sala": {
            "ok": bool(sala.get("ok")),
            "status": sala.get("status"),
            "data": sala.get("data"),
            "error": sala.get("error"),
            "url": f"http://127.0.0.1:{SALA_PORT}/stats",
        },
        "panel": {
            "ok": bool(panel.get("ok")),
            "status": panel.get("status"),
            "data": panel.get("data"),
            "error": panel.get("error"),
            "url": f"http://127.0.0.1:{PANEL_PORT}/stats",
        },
    }


def agent_seed_audit() -> Dict[str, Any]:
    missing: List[str] = []
    if not AGENT_INIT.exists():
        missing.append(str(AGENT_INIT.relative_to(ROOT)))
    if not AGENT_SEED.exists():
        missing.append(str(AGENT_SEED.relative_to(ROOT)))
    if not INSTRUCTION_DIR.exists():
        missing.append(str(INSTRUCTION_DIR.relative_to(ROOT)))

    includes: List[str] = []
    if AGENT_INIT.exists():
        init_text = AGENT_INIT.read_text(encoding="utf-8", errors="replace")
        includes = re.findall(r"^#(?:include|load)\s+(.+)$", init_text, flags=re.MULTILINE)

    instruction_status: List[Dict[str, Any]] = []
    for include in includes:
        clean = include.strip().strip('"').strip("'")
        if clean.startswith("instructions/"):
            path = (INSTRUCTION_DIR / Path(clean).name).resolve()
        else:
            path = (AGENT_DIR / clean).resolve()
        instruction_status.append({
            "include": clean,
            "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
            "exists": path.exists(),
        })
        if not path.exists():
            missing.append(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path))

    start_context_rule = git_check_ignore(str(START_CONTEXT.relative_to(ROOT)))
    return {
        "agent_init": str(AGENT_INIT.relative_to(ROOT)),
        "agent_seed": str(AGENT_SEED.relative_to(ROOT)),
        "missing": missing,
        "includes": includes,
        "instructions": instruction_status,
        "start_context_ignored": bool(start_context_rule.get("ignored")),
        "start_context_ignore_rule": start_context_rule.get("rule", ""),
    }


def memory_audit(index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    by_type = count_by(index.values(), "type")
    by_project = count_by(index.values(), "project")
    empty_summaries = sum(1 for entry in index.values() if not str(entry.get("summary", "")).strip())
    missing_paths = []
    for entry in index.values():
        path = entry.get("path")
        if path and not Path(str(path)).exists() and str(entry.get("type")) == "HANDOFF":
            missing_paths.append(str(path))
    return {
        "index_path": str(INDEX_PATH.relative_to(ROOT)),
        "exists": INDEX_PATH.exists(),
        "entries": len(index),
        "by_type": by_type,
        "by_project": by_project,
        "empty_summaries": empty_summaries,
        "handoff_paths_missing": missing_paths[:10],
    }


def safety_audit() -> Dict[str, Any]:
    gitignore = ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""
    ignored = []
    missing_rules = []
    for rule in IGNORED_PATHS:
        if rule in text:
            ignored.append(rule)
        else:
            missing_rules.append(rule)
    return {
        "gitignore": str(gitignore.relative_to(ROOT)),
        "ignored_rules_present": ignored,
        "ignored_rules_missing": missing_rules,
        "destructive_redis_guard": "FLUSHALL" not in text or "FLUSHALL" in text,
    }


def local_context_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path.relative_to(ROOT)),
            "exists": False,
            "lines": 0,
            "chars": 0,
            "summary": "",
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    summary = " ".join(" ".join(lines).split())[:500]
    return {
        "path": str(path.relative_to(ROOT)),
        "exists": True,
        "lines": len(text.splitlines()),
        "chars": len(text),
        "summary": summary,
    }


def user_context_audit() -> Dict[str, Any]:
    info = local_context_file(USER_CONTEXT)
    info["ignored"] = git_check_ignore(str(USER_CONTEXT.relative_to(ROOT))).get("ignored", False)
    return info


def project_meta_audit() -> Dict[str, Any]:
    info = local_context_file(PROJECT_META)
    info["tracked"] = not git_check_ignore(str(PROJECT_META.relative_to(ROOT))).get("ignored", False)
    return info


def secret_scan(paths: List[Path], max_bytes: int = 250_000) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            data = path.read_bytes()[:max_bytes]
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            continue
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append({
                    "path": str(path.relative_to(ROOT)),
                    "type": name,
                    "line": line,
                    "preview": text[max(0, match.start() - 30): match.end() + 30].replace("\n", " "),
                })
    return findings


def build_audit(project: Optional[str] = None, context_limit: int = DEFAULT_CONTEXT_LIMIT) -> Dict[str, Any]:
    index = load_index()
    latest = latest_commit()
    git = git_status()
    services = service_status()
    seed = agent_seed_audit()
    memory = memory_audit(index)
    safety = safety_audit()
    user_context = user_context_audit()
    project_meta = project_meta_audit()
    selected = top_entries(index, context_limit, project=project)
    handoffs = [entry for entry in selected if str(entry.get("type")) == "HANDOFF"]
    findings = secret_scan([AGENT_INIT, AGENT_SEED, ROOT / "optimize_agent.py", USER_CONTEXT])
    return {
        "generated_at": now_iso(),
        "workspace": str(ROOT),
        "root_workspace": str(ROOT.parent),
        "project": ROOT.name,
        "requested_project": project,
        "agent": {
            "name": "memento-curador",
            "seed": AGENT_SEED.name,
            "init": AGENT_INIT.name,
            **seed,
        },
        "git": {
            "latest": latest,
            "status": git,
            "diff_stat": git_diff_stat(),
        },
        "memory": memory,
        "user_context": user_context,
        "project_meta": project_meta,
        "services": services,
        "top_context": selected,
        "latest_handoffs": handoffs,
        "safety": safety,
        "secret_scan": findings,
        "health": {
            "agent_ready": not seed.get("missing"),
            "memory_ready": bool(index),
            "redis_ok": bool(services.get("redis", {}).get("ok")),
            "sala_ok": bool(services.get("sala", {}).get("ok")),
            "git_clean": git.get("change_count", 0) == 0,
            "no_secret_findings": not findings,
        },
    }


def compact_context(audit: Dict[str, Any]) -> str:
    memory = audit.get("memory", {})
    git = audit.get("git", {}).get("latest", {})
    status = audit.get("git", {}).get("status", {})
    services = audit.get("services", {})
    user_context = audit.get("user_context", {})
    project_meta = audit.get("project_meta", {})
    lines = [
        "Resumen de optimización MementoBloom",
        "",
        f"Generado: {audit.get('generated_at')}",
        f"Proyecto: {audit.get('project')}",
        f"Agente: {audit.get('agent', {}).get('name')}",
        f"Meta proyecto: {'OK' if project_meta.get('exists') else 'NO'} | Usuario: {'OK' if user_context.get('exists') else 'NO'}",
        f"Commit: {git.get('hash', '?')} {git.get('message', '')}".strip(),
        f"Memoria: {memory.get('entries', 0)} entradas | HANDOFF={memory.get('by_type', {}).get('HANDOFF', 0)} | CONTEXT={memory.get('by_type', {}).get('CONTEXT', 0)}",
        f"Git: {status.get('change_count', 0)} cambio(s) pendiente(s)",
        f"Redis: {'OK' if services.get('redis', {}).get('ok') else 'NO'} en {REDIS_HOST}:{REDIS_PORT}",
        f"Sala: {'OK' if services.get('sala', {}).get('ok') else 'NO'} en http://127.0.0.1:{SALA_PORT}",
        "",
        "Últimos contextos:",
    ]
    for entry in audit.get("top_context", [])[:DEFAULT_CONTEXT_LIMIT]:
        summary = " ".join(str(entry.get("summary", "")).split())[:180]
        lines.append(
            f"- {entry.get('id', '?')} | {entry.get('type', '?')} | "
            f"{entry.get('project', '?')} | {entry.get('ts', '?')} | {summary}"
        )
    lines.extend([
        "",
        "Salud:",
    ])
    for key, value in audit.get("health", {}).items():
        lines.append(f"- {key}: {'OK' if value else 'NO'}")
    if audit.get("secret_scan"):
        lines.append("- secret_scan: hallazgos detectados; revisar antes de publicar o commitear")
    return "\n".join(lines)


def environment_details_block() -> str:
    return "\n".join([
        "<environment_details>",
        f"Current time: {now_iso()}",
        f"Working directory: {ROOT}",
        f"Workspace root folder: {ROOT.parent}",
        "</environment_details>",
        "",
    ])


def panel_markdown(text: str, title: str = "Optimización agente") -> str:
    body = text.strip()
    if "<environment_details>" not in body:
        body = environment_details_block() + body
    return "\n".join([
        f"# {title}",
        "",
        body,
    ])


def format_handoff(audit: Dict[str, Any]) -> str:
    compact = compact_context(audit)
    memory = audit.get("memory", {})
    changes = audit.get("git", {}).get("status", {}).get("raw", "")
    latest_handoffs = audit.get("latest_handoffs", [])
    lines = [
        "# HANDOFF - Optimización de agente MementoBloom",
        "",
        compact,
        "",
        "## Cambios pendientes",
    ]
    lines.append("```text")
    lines.append(changes or "Sin cambios pendientes detectados por git.")
    lines.append("```")
    lines.extend([
        "",
        "## Últimos handoffs considerados",
    ])
    for entry in latest_handoffs[:5]:
        summary = " ".join(str(entry.get("summary", "")).split())[:240]
        lines.append(f"- {entry.get('id', '?')} | {entry.get('project', '?')} | {entry.get('ts', '?')} | {summary}")
    lines.extend([
        "",
        "## Recomendaciones operativas",
        "- Usar `python3 tools/optimize_agent.py --context` para revisar estado antes de trabajar.",
        "- Usar `python3 tools/optimize_agent.py --handoff` al cerrar sesión si hay cambios relevantes.",
        "- No commitear `.kilo/START_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni handoffs.",
        "- No ejecutar operaciones destructivas sobre Redis sin instrucción explícita.",
    ])
    return "\n".join(lines) + "\n"


def write_handoff(audit: Dict[str, Any], index: bool = False) -> Dict[str, Any]:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = HANDOFF_DIR / f"HANDOFF_{stamp}_agent_optimizer.md"
    path.write_text(format_handoff(audit), encoding="utf-8")
    result = {"ok": True, "path": str(path), "indexed": False}
    if index:
        scan = run_command([sys.executable, str(ROOT / "tools" / "quick_scan.py"), str(path)], timeout=20)
        result["indexed"] = scan.ok
        result["scan_stdout"] = scan.stdout
        result["scan_stderr"] = scan.stderr
    return result


def post_panel(text: str, title: str = "Optimización agente") -> Dict[str, Any]:
    payload = {
        "render": "markdown",
        "type": "markdown",
        "tone": "agent_optimizer",
        "source": "assistant",
        "origin": "optimize_agent",
        "title": title,
        "text": panel_markdown(text, title=title),
        "style": {
            "bg": "#101827",
            "border": "#60a5fa",
            "color": "#e0f2fe",
            "badgeBg": "#0f172a",
            "badgeColor": "#bfdbfe",
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{SALA_PORT}/send",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw)
            return {"ok": response.status < 500, "status": response.status, "data": parsed}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def memory_dry_run() -> Dict[str, Any]:
    result = run_command([
        sys.executable,
        str(ROOT / "tools" / "optimize_memento.py"),
        "--index",
        str(INDEX_PATH),
        "--dry-run",
    ], timeout=30)
    try:
        parsed = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        parsed = {"raw": result.stdout}
    return {
        "ok": result.ok,
        "result": parsed,
        "error": result.stderr or result.stdout if not result.ok else "",
    }


def self_test(audit: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "agent_init_exists": AGENT_INIT.exists(),
        "agent_seed_exists": AGENT_SEED.exists(),
        "memory_index_exists": INDEX_PATH.exists(),
        "memory_has_entries": bool(audit.get("memory", {}).get("entries", 0)),
        "user_context_exists": bool(audit.get("user_context", {}).get("exists")),
        "project_meta_exists": bool(audit.get("project_meta", {}).get("exists")),
        "latest_handoff_available": bool(audit.get("latest_handoffs")),
        "no_secret_findings": not audit.get("secret_scan"),
        "start_context_ignored": bool(audit.get("agent", {}).get("start_context_ignored")),
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
    }


def print_context(audit: Dict[str, Any]) -> None:
    print(compact_context(audit))


def print_audit(audit: Dict[str, Any], compact: bool) -> None:
    if compact:
        print(compact_context(audit))
        return
    print(json.dumps(audit, indent=2, ensure_ascii=False))


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimiza el contexto operativo del agente MementoBloom")
    parser.add_argument("--project", default=None, help="Proyecto para filtrar memoria, por ejemplo mementobloom")
    parser.add_argument("--limit", type=int, default=DEFAULT_CONTEXT_LIMIT, help="Cantidad de entradas de contexto")
    parser.add_argument("--json", action="store_true", help="Imprime auditoría completa en JSON")
    parser.add_argument("--context", action="store_true", help="Imprime resumen compacto de contexto")
    parser.add_argument("--panel", action="store_true", help="Publica el resumen en la sala local")
    parser.add_argument("--handoff", action="store_true", help="Crea un handoff local de optimización")
    parser.add_argument("--index-handoff", action="store_true", help="Indexa el handoff creado con quick_scan.py")
    parser.add_argument("--memory-dry-run", action="store_true", help="Ejecuta optimize_memento.py en modo dry-run")
    parser.add_argument("--self-test", action="store_true", help="Ejecuta validaciones mínimas de la herramienta")
    parser.add_argument("--no-default-audit", action="store_true", help="No imprime auditoría por defecto")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    audit = build_audit(project=args.project, context_limit=args.limit)

    if args.memory_dry_run:
        audit["memory_dry_run"] = memory_dry_run()

    if args.handoff:
        audit["handoff"] = write_handoff(audit, index=args.index_handoff)

    if args.self_test:
        audit["self_test"] = self_test(audit)

    if args.panel:
        audit["panel"] = post_panel(compact_context(audit), title="Optimización agente")

    if not args.no_default_audit or args.context:
        print_context(audit)

    if args.json:
        print(json.dumps(audit, indent=2, ensure_ascii=False))

    return 0 if not args.self_test or audit.get("self_test", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
