#!/usr/bin/env python3
"""Prepare the MementoBloom agent progressively and launch Kilo."""

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "memory" / "graph" / "memory_index.json"
START_CONTEXT = ROOT / ".kilo" / "START_CONTEXT.md"
PROJECT_META = ROOT / ".kilo" / "PROJECT_META.md"
USER_CONTEXT = ROOT / ".kilo" / "secure" / "USER_CONTEXT.md"
SECURE_CONTEXT = ROOT / ".kilo" / "secure" / "SECURE.md"
AGENT_DIR = ROOT / ".kilo" / "agent"
AGENT_SEED = AGENT_DIR / "memento-curador.md"
AGENT_INIT = AGENT_DIR / "init.md"
AGENT_INCLUDE_DIR = AGENT_DIR / "instructions"
SECURE_DIR = ROOT / ".kilo" / "secure"
RUNTIME_DIR = ROOT / ".memento_runtime"
LOG_DIR = RUNTIME_DIR / "logs"
PID_DIR = RUNTIME_DIR / "pids"
DEFAULT_AGENT = "memento-curador"
DEFAULT_MODEL = "kilo/kilo-auto/free"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost" if os.environ.get("REDIS_DISABLE") else "192.168.18.59")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
START_TIMEOUT = float(os.environ.get("MEMENTO_START_TIMEOUT", "12"))
AGENT_VERSION = "progressive-agent-v1"
AGENT_GITIGNORE_PATHS = [
    ".kilo/agent/memento-curador.md",
    ".kilo/START_CONTEXT.md",
    ".kilo/USER_CONTEXT.md",
    ".kilo/secure/*",
    "memory/graph/*.json",
]
INCLUDE_RE = re.compile(r"^#(?:include|load)\s+(.+)$", re.MULTILINE)

INIT_TEMPLATE = """# Semilla inicial del agente MementoBloom

Objetivo: construir progresivamente un agente de memoria histórica para MementoBloom.

Flujo obligatorio:
1. Leer esta semilla inicial.
2. Cargar las instrucciones progresivas listadas abajo.
3. Leer `.kilo/START_CONTEXT.md` si existe, pero no lo trackees.
4. Usar `memory/graph/memory_index.json` como memoria compacta local.
5. Priorizar HANDOFF recientes de `projects/mementobloom`, `projects/Management360` y `projects/Ventas_Porta`.
6. Continuar desde el último handoff relevante sin pedir información ya registrada.
7. No destruir memoria, Redis ni handoffs salvo instrucción explícita.

# Instrucciones progresivas
#include instructions/00-core.md
#include instructions/10-context.md
#include instructions/20-memory.md
#include instructions/30-redis-panel.md
#include instructions/40-projects.md
#include instructions/90-safety.md
"""

INSTRUCTION_TEMPLATES = {
    "00-core.md": """# 00 Core

Eres el agente principal de MementoBloom.

Comportamiento:
- Actúa como curador de memoria histórica y contexto operativo.
- Inicia cada sesión leyendo la semilla del agente y el contexto inicial.
- Resume el estado del proyecto antes de proponer acciones.
- Confirma el objetivo del usuario usando memoria registrada, sin pedir datos ya disponibles.
- Continúa desde el último handoff relevante.
- Propón próximos pasos concretos y ejecutables.
""",
     "10-context.md": """# 10 Contexto

Contexto inicial:
- Lee primero `.kilo/START_CONTEXT.md` si existe, pero no lo trackees.
- Si el usuario pide contexto, ejecuta `python3 tools/context_builder.py --limit 20`.
- Si el usuario pide iniciar una nueva sesión con contexto, ejecuta `python3 tools/memento_kilo_start.py --print`.
- Para arranque rápido, ejecuta `python3 tools/memento_kilo_start.py --quick`.
- Usa `.kilo/START_CONTEXT.md` solo como contexto local regenerable.
- Usa `memory/graph/memory_index.json` como índice compacto de memoria.
- Si existe contexto seguro en `.kilo/secure/SECURE.md`, léelo solo como referencia local y no lo expongas.
- El contexto de usuario puede residir en `.kilo/secure/USER_CONTEXT.md` y no se expone.

Reglas de arranque:
- Resume el estado del proyecto.
- Identifica el objetivo del usuario.
- Continúa desde el último handoff relevante.
- No repitas instrucciones ya registradas salvo que sea necesario para ejecutar una tarea.
""",
    "20-memory.md": """# 20 Memoria

Memoria operativa:
- Prioriza HANDOFF recientes.
- Usa `python3 tools/quick_scan.py <HANDOFF_PATH>` para indexar handoffs nuevos.
- Usa `python3 tools/context_builder.py --limit N` para obtener contexto ranked.
- Mantén trazabilidad entre seed → instrucciones → contexto → handoff → acción.
- Si una tarea modifica memoria, handoffs o índices, valida que el cambio sea intencional.

No borrar:
- No borres memoria.
- No borres Redis.
- No borres handoffs.
- No elimines índices salvo instrucción explícita.
""",
    "30-redis-panel.md": """# 30 Redis y panel

Redis de sala:
- Remoto: `192.168.18.59:6379`
- Cola: `memento_panel_items`
- Local: `http://127.0.0.1:8767/messages`
- Sala local: `python3 tools/sala.py`

Reglas:
- No ejecutes `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- Si necesitas levantar la sala, usa `python3 tools/sala.py` o `python3 tools/memento_kilo_start.py --services`.
- Verifica `/stats` y `/messages` cuando el usuario pregunte por el panel.
""",
    "40-projects.md": """# 40 Proyectos prioritarios

Prioriza estos proyectos cuando haya ambigüedad:
1. `projects/mementobloom`
2. `projects/Management360`
3. `projects/Ventas_Porta`

Para MementoBloom:
- La semilla del agente está en `.kilo/agent/init.md`.
- El agente generado está en `.kilo/agent/memento-curador.md`.
- El contexto de arranque puede regenerarse localmente en `.kilo/START_CONTEXT.md`, pero no debe trackearse.

Para Management360 y Ventas_Porta:
- Usa sus HANDOFF recientes para reconstruir estado.
- No asumas que servicios remotos están activos; verifica antes de operar.
""",
     "50-user-meta.md": """# 50 Usuario y meta del proyecto

Contexto de usuario:
- Lee `.kilo/PROJECT_META.md` si existe.
- Si existe `.kilo/secure/USER_CONTEXT.md`, úsalo como preferencias, objetivos, infraestructura y reglas operativas locales.
- No pidas información ya registrada en `.kilo/secure/USER_CONTEXT.md`, handoffs o memoria compacta.
- Actualiza `.kilo/secure/USER_CONTEXT.md` solo cuando el usuario revele preferencias, objetivos, restricciones, infraestructura o decisiones relevantes.

Meta del proyecto:
- Cada sesión debe poder continuar sin depender de un modelo específico.
- El contexto debe ser modelo-agnóstico y legible desde archivos locales.
- Prioriza continuidad sobre dependencias de una UI o modelo concreto.
- Python Portable: `.kilo/USER_CONTEXT.md` debe poder ejecutarse desde cualquier carpeta con `python3 <path>` sin rutas absolutas.
- Python Portable: Usa `Path(__file__).resolve().parent` para crear rutas relativas seguras dentro del proyecto.
- Python Portable: No uses rutas absolutas hardcodeadas como `/Users/...`, `/Volumes/...`, ni referencias a carpetas externas al repo.
- Python Portable: Asegura que el código de herramientas pueda clonarse en `/home/usuario/mementobloom` o `/mnt/c/Users/.../mementobloom` y seguir funcionando.
- Python Portable: Cualquier ruta dentro del proyecto debe crearse relativa al archivo `tools/` o al root del repo, no desde la ubicación actual del usuario.

Arranque recomendado:
- Ejecuta `python3 tools/bootstrap_context.py --print` cuando necesites reconstruir contexto para cualquier modelo.
- Ejecuta `python3 tools/optimize_agent.py --context` cuando necesites auditoría operativa.
- Ejecuta `python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8` para arranque rápido Kilo.

Seguridad:
- No expongas secretos ni contenido de vault.
- No trackees `.kilo/START_CONTEXT.md`, `.kilo/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, `.kilo/secure/*` ni handoffs.
- No ejecutes operaciones destructivas sobre Redis, memoria o handoffs salvo instrucción explícita.
""",
     "90-safety.md": """# 90 Seguridad

Seguridad operativa:
- No expongas credenciales, secretos ni contenido de vault salvo que sea estrictamente necesario.
- No hagas commits, pushes o force pushes salvo solicitud explícita.
- No borres archivos, memoria, Redis, handoffs o índices salvo solicitud explícita.
- Si una operación puede ser destructiva, explícala antes de ejecutarla.
- Mantén compatibilidad con la configuración Kilo en `.kilo/kilo.json`.
- Usa rutas relativas y portable-friendly; no dependas de `/Users/...` ni `/Volumes/...`.
""",
}


def load_index():
    if not INDEX_PATH.exists():
        return {}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def file_fingerprint(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def ensure_agent_files():
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    if not AGENT_INIT.exists():
        AGENT_INIT.write_text(INIT_TEMPLATE, encoding="utf-8")
    AGENT_INCLUDE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in INSTRUCTION_TEMPLATES.items():
        path = AGENT_INCLUDE_DIR / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def resolve_include(raw: str) -> Path:
    include = raw.strip().strip('"').strip("'")
    if not include:
        return AGENT_DIR / "missing.md"
    path = Path(include)
    if path.is_absolute():
        return path
    if str(path).startswith("instructions/"):
        return (AGENT_DIR / path).resolve()
    return (AGENT_DIR / path).resolve()


def load_progressive_instructions() -> list[tuple[Path, str, bool]]:
    init = AGENT_INIT.read_text(encoding="utf-8", errors="replace") if AGENT_INIT.exists() else ""
    includes = []
    for match in INCLUDE_RE.finditer(init):
        includes.append(resolve_include(match.group(1)))

    loaded = []
    for path in includes:
        if path.exists():
            loaded.append((path, path.read_text(encoding="utf-8", errors="replace"), True))
        else:
            loaded.append((path, f"# MISSING {path}\n", False))
    return loaded


def top_memory_entries(limit: int = 14, project: str | None = None) -> list[dict]:
    index = load_index()
    entries = list(index.values())
    if project:
        entries = [e for e in entries if e.get("project") == project]
    entries.sort(key=lambda e: entry_sort_key(e, project), reverse=True)
    return entries[:limit]


def entry_sort_key(entry: dict, project: str | None = None):
    ts = str(entry.get("ts", ""))
    parsed = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(ts[:19], fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        parsed = datetime.min
    project_boost = 1 if project and entry.get("project") == project else 0
    type_boost = 1 if entry.get("type") == "HANDOFF" else 0
    return (parsed, project_boost, type_boost, str(entry.get("id", "")))


def agent_source_signature(project: str | None = None) -> str:
    parts = [AGENT_VERSION]
    if AGENT_INIT.exists():
        parts.append(AGENT_INIT.read_text(encoding="utf-8", errors="replace"))
    for path, content, ok in load_progressive_instructions():
        parts.append(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path))
        parts.append("OK" if ok else "MISSING")
        parts.append(content)
    for entry in top_memory_entries(limit=14, project=project):
        parts.append(str(entry.get("id")))
        parts.append(str(entry.get("ts")))
        parts.append(str(entry.get("path")))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def user_context_short(limit: int = 4) -> list[str]:
    candidates = [USER_CONTEXT, SECURE_CONTEXT]
    for path in candidates:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace").splitlines()
            lines = []
            for line in text:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                lines.append(stripped)
                if len(lines) >= limit:
                    break
            return lines if lines else ["(vacío)"]
    return ["(sin contexto de usuario local)"]


def build_agent_content(project: str | None = None) -> tuple[str, str]:
    signature = agent_source_signature(project=project)
    init = AGENT_INIT.read_text(encoding="utf-8", errors="replace") if AGENT_INIT.exists() else ""
    loaded = load_progressive_instructions()
    memory = top_memory_entries(limit=14, project=project)
    enriched_memory = []
    for entry in memory:
        item = dict(entry)
        raw_path = item.get("path", "")
        if raw_path:
            lower = str(raw_path).lower()
            if ("/users/" in lower) or lower.startswith("/volumes/") or ("mementobloom/" in lower and len(parts := str(raw_path).split("/")) > 4):
                item["path"] = ROOT.name
        enriched_memory.append(item)

    lines = [
        "---",
        "description: Curador de memoria histórica para MementoBloom",
        "mode: primary",
        "model: kilo/kilo-auto/free",
        "steps: 25",
        "---",
        f"<!-- generated-hash: {signature} -->",
        "",
        "# MementoBloom Agent Seed",
        "",
        "Agente construido progresivamente desde `.kilo/agent/init.md`.",
        "La semilla inicial carga instrucciones adicionales y memoria compacta hasta formar un agente robusto.",
        "",
        "Accesos recomendados:",
        "- Configuración pública del proyecto: `.kilo/PROJECT_META.md`.",
        "- Contexto local sensible (no compartir): `.kilo/secure/USER_CONTEXT.md`.",
        "",
        "## Semilla inicial",
        init.strip(),
        "",
        "## Instrucciones progresivas cargadas",
    ]

    for path, content, ok in loaded:
        label = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        lines.extend([
            "",
            f"### {label} {'OK' if ok else 'MISSING'}",
            content.strip(),
        ])

    lines.extend([
        "",
        "## Memoria compacta actual",
        "",
        f"- Index entries: {len(load_index())}",
    ])
    for entry in enriched_memory:
        summary = " ".join(str(entry.get("summary", "")).split())[:220]
        lines.append(
            f"- [{entry.get('id', '?')}] {entry.get('type', '?')} "
            f"project={entry.get('project', '?')} ts={entry.get('ts', '?')} "
            f"path={entry.get('path', '?')} — {summary}"
        )

    lines.extend([
        "",
        "## Reglas operativas robustas",
        "- No borres memoria, Redis ni handoffs salvo instrucción explícita.",
        "- No ejecutes FLUSHALL ni operaciones destructivas sobre Redis salvo instrucción explícita.",
        "- Usa `Path(__file__).resolve().parent.parent` para rutas base del repo.",
        "- No uses rutas absolutas hardcodeadas.",
        f"- Entorno limpio: {(rel(SECURE_CONTEXT) if SECURE_CONTEXT.exists() else '.kilo/secure/SECURE.md')} define preferencias locales.",
    ])
    lines.extend(user_context_short(limit=4))
    return "\n".join(lines), signature


def ensure_agent_seed(force: bool = False, project: str | None = None) -> dict:
    ensure_agent_files()
    content, signature = build_agent_content(project=project)
    if AGENT_SEED.exists() and not force and f"generated-hash: {signature}" in AGENT_SEED.read_text(encoding="utf-8", errors="replace"):
        return {
            "status": "ready",
            "changed": False,
            "path": str(AGENT_SEED),
            "hash": signature,
        }
    AGENT_SEED.write_text(content, encoding="utf-8")
    return {
        "status": "updated" if AGENT_SEED.exists() else "created",
        "changed": True,
        "path": str(AGENT_SEED),
        "hash": signature,
    }


def build_context(limit: int, project: str | None = None, agent_result: dict | None = None):
    index = load_index()
    entries = list(index.values())
    if project:
        entries = [e for e in entries if e.get("project") == project]
    entries.sort(key=lambda e: entry_sort_key(e, project), reverse=True)
    selected = entries[:limit]
    agent = agent_result or {"status": "skipped", "path": str(AGENT_SEED), "hash": "?"}
    lines = [
        "# MEMENTO Kilo Startup Context",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Workspace: {ROOT.parent}",
        f"Project: {ROOT.name}",
        f"Index entries: {len(index)}",
        "",
        "## Startup instruction",
        "Prepara la semilla progresiva del agente, lee el contexto inicial y continúa desde el último handoff relevante sin pedir información ya registrada.",
        "",
    ]
    lines.extend(local_context_summary(PROJECT_META, "Project meta"))
    lines.extend(local_context_summary(USER_CONTEXT, "User context"))
    lines.extend([
        "## Top recent memory",
    ])
    for entry in selected:
        summary = " ".join(str(entry.get("summary", "")).split())[:500]
        lines.append(
            "- "
            f"{entry.get('id', '?')} | {entry.get('type', '?')} | "
            f"project={entry.get('project', '?')} | ts={entry.get('ts', '?')} | "
            f"path={entry.get('path', '?')}\n  {summary}"
        )
    lines.extend([
        "",
        "## Commands",
        "- `python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8` arranque rápido local sin regenerar contexto trackeado.",
        "- `python3 tools/memento_kilo_start.py --print --project=mementobloom --limit 14` prepara agente, imprime contexto local y sale.",
        "- `python3 tools/memento_kilo_start.py --services` prepara el agente, regenera el contexto y levanta servicios locales antes de abrir Kilo.",
        "- `python3 tools/memento_kilo_start.py --services-only` levanta servicios locales sin abrir Kilo.",
        "- `python3 tools/bootstrap_context.py --print` imprime contexto universal para cualquier modelo.",
        "- `python3 tools/optimize_agent.py --context` audita y resume el entorno operativo.",
        "- `python3 tools/context_builder.py --limit 20` muestra contexto ranked.",
        "- `python3 tools/quick_scan.py <HANDOFF_PATH>` indexa un handoff nuevo.",
        "- `python3 tools/sala.py` inicia solo la sala local en `http://127.0.0.1:8767`.",
        "",
        "## Redis sala",
        "- Remoto: `192.168.18.59:6379`",
        "- Cola: `memento_panel_items`",
        "- Local: `http://127.0.0.1:8767/messages`",
    ])
    return "\n".join(lines) + "\n"


def write_context(text: str):
    START_CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    START_CONTEXT.write_text(text, encoding="utf-8")


def local_context_summary(path: Path, title: str) -> list[str]:
    if not path.exists():
        return [f"## {title}", f"- `{path}` no existe todavía.", ""]
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [f"## {title}", f"- Path: `{path}`", "- Estado: local/contextual"]
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(f"- {stripped}")
        if len(lines) >= 12:
            break
    lines.append("")
    return lines


def kilo_path():
    candidates = [
        Path.home() / ".local" / "bin" / "kilo",
        Path(sys.executable).parent / "kilo",
        shutil.which("kilo"),
    ]
    for candidate in candidates:
        if candidate and Path(str(candidate)).exists():
            return str(candidate)
    return "kilo"


def tcp_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_ok(url: str, timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def redis_ping(timeout: float = 1.0) -> dict:
    try:
        with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=timeout) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(64).decode(errors="replace")
        return {"ok": "PONG" in data, "detail": data.strip()}
    except OSError as exc:
        return {"ok": False, "detail": str(exc)}


def write_pid(name: str, pid: int):
    PID_DIR.mkdir(parents=True, exist_ok=True)
    (PID_DIR / f"{name}.pid").write_text(str(pid), encoding="utf-8")


def start_service(name: str, cmd: list[str], port: int | None = None, health_url: str | None = None) -> dict:
    if port and tcp_open("127.0.0.1", port):
        return {"name": name, "status": "already_running", "port": port}
    if health_url and http_ok(health_url):
        return {"name": name, "status": "already_running", "url": health_url}

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}.log"
    log_file = log_path.open("ab")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    write_pid(name, proc.pid)
    log_file.close()

    deadline = time.time() + START_TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            return {
                "name": name,
                "status": "failed",
                "pid": proc.pid,
                "exit_code": proc.returncode,
                "log": str(log_path),
            }
        if port and tcp_open("127.0.0.1", port):
            return {"name": name, "status": "started", "pid": proc.pid, "port": port, "log": str(log_path)}
        if health_url and http_ok(health_url):
            return {"name": name, "status": "started", "pid": proc.pid, "url": health_url, "log": str(log_path)}
        time.sleep(0.25)

    return {
        "name": name,
        "status": "timeout",
        "pid": proc.pid,
        "port": port,
        "url": health_url,
        "log": str(log_path),
    }


def ensure_services() -> list[dict]:
    results = []
    results.append({"name": "redis", "status": "ok" if redis_ping()["ok"] else "unavailable", "host": REDIS_HOST, "port": REDIS_PORT})

    sala = ROOT / "tools" / "sala.py"
    if sala.exists():
        results.append(start_service(
            "sala",
            [sys.executable, str(sala)],
            port=SALA_PORT,
            health_url=f"http://127.0.0.1:{SALA_PORT}/stats",
        ))
    else:
        results.append({"name": "sala", "status": "skipped", "reason": f"{sala} not found"})

    panel = ROOT / "panel_server.py"
    if panel.exists():
        results.append(start_service(
            "panel",
            [sys.executable, str(panel), str(PANEL_PORT)],
            port=PANEL_PORT,
            health_url=f"http://127.0.0.1:{PANEL_PORT}/",
        ))
    else:
        results.append({"name": "panel", "status": "skipped", "reason": f"{panel} not found"})

    return results


def agent_seed_status() -> dict:
    if not AGENT_SEED.exists():
        return {"status": "missing", "hash": "?", "path": str(AGENT_SEED)}
    text = AGENT_SEED.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"generated-hash:\s*([0-9a-f]+)", text)
    return {
        "status": "ready",
        "hash": match.group(1) if match else "?",
        "path": str(AGENT_SEED),
    }


def git_status_summary() -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--short"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip()
    except Exception as exc:
        return f"unknown ({exc})"
    if not out:
        return "clean"
    lines = out.splitlines()
    return f"{len(lines)} cambio(s): " + ", ".join(lines[:5]) + (" ..." if len(lines) > 5 else "")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def quick_startup_report(limit: int = 8, project: str | None = None) -> str:
    index = load_index()
    entries = list(index.values())
    if project:
        entries = [e for e in entries if e.get("project") == project]
    entries.sort(key=lambda e: entry_sort_key(e, project), reverse=True)
    selected = entries[:limit]
    seed = agent_seed_status()
    redis = redis_ping(timeout=0.4)
    sala = {"ok": http_ok(f"http://127.0.0.1:{SALA_PORT}/stats", timeout=0.4)}
    lines = [
        "# MEMENTO Quick Startup",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Workspace: {rel(ROOT.parent)}",
        f"Project: {ROOT.name}",
        f"Context file: {rel(START_CONTEXT)}",
        f"User context: {rel(USER_CONTEXT) if USER_CONTEXT.exists() else '.kilo/secure/USER_CONTEXT.md (no existe)'}",
        f"Project meta: {rel(PROJECT_META)}",
        f"Agent seed: {seed['status']} hash={seed['hash']}",
        f"Memory index: {len(index)} entries",
        f"Git: {git_status_summary()}",
        "",
        "## Top recent memory ids",
    ]
    for entry in selected:
        lines.append(
            f"- {entry.get('id', '?')} | {entry.get('type', '?')} "
            f"project={entry.get('project', '?')} ts={entry.get('ts', '?')}"
        )
    lines.extend([
        "",
        "## Services",
        f"- Redis sala: {'OK' if redis.get('ok') else 'UNAVAILABLE'} at {REDIS_HOST}:{REDIS_PORT}",
        f"- Sala local: {'OK' if sala.get('ok') else 'UNAVAILABLE'} at http://127.0.0.1:{SALA_PORT}",
        "",
        "## Safe next-session commands",
        "- `python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8`",
        "- `python3 tools/bootstrap_context.py --print` imprime contexto universal para cualquier modelo.",
        "- `python3 tools/optimize_agent.py --context` audita y resume el entorno operativo.",
        "- `python3 tools/memento_kilo_start.py --services-only`",
    ])
    return "\n".join(lines) + "\n"


def print_agent_seed(result: dict):
    status = result.get("status")
    if status == "created":
        print(f"\nAgent seed: CREATED hash={result.get('hash')}")
    elif status == "updated":
        print(f"\nAgent seed: UPDATED hash={result.get('hash')}")
    elif status == "ready":
        print(f"\nAgent seed: READY hash={result.get('hash')}")
    else:
        print(f"\nAgent seed: {status} hash={result.get('hash')}")


def print_services(results: list[dict]):
    print("\nMementoBloom services")
    for item in results:
        name = item.get("name", "?")
        status = item.get("status", "?")
        if status == "ok":
            print(f"  - {name}: OK at {item.get('host')}:{item.get('port')}")
        elif status == "unavailable":
            print(f"  - {name}: UNAVAILABLE at {item.get('host')}:{item.get('port')}")
        elif status == "already_running":
            print(f"  - {name}: ALREADY RUNNING")
        elif status == "started":
            print(f"  - {name}: STARTED pid={item.get('pid')}")
        elif status == "timeout":
            print(f"  - {name}: TIMEOUT pid={item.get('pid')} log={item.get('log')}")
        elif status == "failed":
            print(f"  - {name}: FAILED exit={item.get('exit_code')} log={item.get('log')}")
        else:
            print(f"  - {name}: {status} {item.get('reason', '')}".strip())


def run_kilo(args: argparse.Namespace) -> int:
    if args.no_kilo:
        return 0
    cmd = [
        kilo_path(),
        "run",
        "--agent",
        args.agent,
        "--model",
        args.model,
        "--dir",
        str(ROOT),
        "-i",
        "# MEMENTO Kilo Startup\n\n"
        f"Prepara la semilla progresiva del agente desde `{AGENT_INIT}`. "
        "Si existe `.kilo/START_CONTEXT.md`, úsalo solo como contexto local no trackeado. "
        "Resume el estado del proyecto, confirma el objetivo del usuario y continúa desde el último handoff relevante.",
    ]
    print("\nLaunching Kilo:")
    print("  " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def normalize_argv(argv: list[str]) -> list[str]:
    out = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--project":
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                out.extend([arg, argv[i + 1]])
                i += 2
            else:
                out.extend([arg, "mementobloom"])
                i += 1
        else:
            out.append(arg)
            i += 1
    return out


def main():
    parser = argparse.ArgumentParser(description="Prepare the MementoBloom progressive agent seed and launch Kilo")
    parser.add_argument("--limit", type=int, default=14)
    parser.add_argument("--project", default="mementobloom")
    parser.add_argument("--agent", default=DEFAULT_AGENT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--print", action="store_true", help="Print context and exit without preparing services")
    parser.add_argument("--quick", action="store_true", help="Print a lightweight local-only startup report and exit")
    parser.add_argument("--services", action="store_true", help="Start optional local services after agent/context preparation")
    parser.add_argument("--services-only", action="store_true", help="Start local services and exit")
    parser.add_argument("--no-services", action="store_true", help="Do not start optional local services")
    parser.add_argument("--no-agent-seed", action="store_true", help="Do not prepare the progressive agent seed before building context")
    parser.add_argument("--force-seed", action="store_true", help="Force progressive agent seed regeneration")
    parser.add_argument("--no-kilo", action="store_true", help="Do not launch Kilo after agent/context preparation")
    args = parser.parse_args(normalize_argv(sys.argv[1:]))

    if args.quick:
        print(quick_startup_report(limit=args.limit, project=args.project), end="")
        return 0

    agent_result = {"status": "skipped", "path": str(AGENT_SEED), "hash": "?"} if args.no_agent_seed else ensure_agent_seed(force=args.force_seed, project=args.project)
    context = build_context(limit=args.limit, project=args.project, agent_result=agent_result)
    write_context(context)
    print(context, end="")
    print_agent_seed(agent_result)

    if args.services or args.services_only:
        print_services(ensure_services())

    if args.services_only or args.no_kilo:
        return 0

    return run_kilo(args)


if __name__ == "__main__":
    raise SystemExit(main())
