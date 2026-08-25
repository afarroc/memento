#!/usr/bin/env python3
from __future__ import annotations
"""Prepare the MementoBloom agent seed and local session context."""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.git import git_status as core_git_status, latest_commit as core_latest_commit
from core.index import load_index, top_entries as core_top_entries, count_by, default_index_path, resolve_index_path
from core.paths import ROOT, rel, workspace_root
from core.services import service_status as core_service_status, service_summary as core_service_summary

WS_ROOT = workspace_root()
CONTEXT_ROOT = WS_ROOT
AGENT_TEMPLATE_ROOT = ROOT / ".agent_context" / "agent"
INDEX_PATH = default_index_path()
START_CONTEXT = WS_ROOT / ".agent_context" / "START_CONTEXT.md"
PROJECT_META = WS_ROOT / ".agent_context" / "PROJECT_META.md"
USER_CONTEXT = WS_ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
SECURE_CONTEXT = WS_ROOT / ".agent_context" / "secure" / "SECURE.md"
CLIENT_PROJECTS_JSON = WS_ROOT / ".agent_context" / "secure" / "client_projects.json"
AGENT_DIR = WS_ROOT / ".agent_context" / "agent"
AGENT_SEED = AGENT_DIR / "agent-main.md"
AGENT_INIT = AGENT_DIR / "init.md"
AGENT_INCLUDE_DIR = AGENT_DIR / "instructions"
SECURE_DIR = WS_ROOT / ".agent_context" / "secure"
RUNTIME_DIR = WS_ROOT / ".memento_runtime"
LOG_DIR = RUNTIME_DIR / "logs"
PID_DIR = RUNTIME_DIR / "pids"
DEFAULT_AGENT = "agent-main"

_env_path = WS_ROOT / ".env"
if _env_path.exists():
    for raw_line in _env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value

REDIS_HOST = os.environ.get("REDIS_HOST", os.environ.get("MEMENTO_REDIS_HOST", "localhost"))
REDIS_PORT = int(os.environ.get("REDIS_PORT", os.environ.get("MEMENTO_REDIS_PORT", "6379")))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
START_TIMEOUT = float(os.environ.get("MEMENTO_START_TIMEOUT", "12"))
AGENT_VERSION = "progressive-agent-v1"
AGENT_GITIGNORE_PATHS = [
    ".agent_context/agent/agent-main.md",
    ".agent_context/START_CONTEXT.md",
    ".agent_context/USER_CONTEXT.md",
    ".agent_context/secure/*",
    "memory/graph/*.json",
]
INCLUDE_RE = re.compile(r"^#(?:include|load)\s+(.+)$", re.MULTILINE)

INIT_TEMPLATE = """# Semilla inicial del agente del proyecto

Objetivo: construir progresivamente un agente de memoria histórica.

Flujo obligatorio:
1. Leer esta semilla inicial.
2. Cargar las instrucciones progresivas listadas abajo.
3. Leer `.agent_context/START_CONTEXT.md` si existe, pero no lo trackees.
4. Usar `memory/graph/memory_index.json` como memoria compacta local.
5. Priorizar HANDOFF recientes del proyecto activo (ver `projects/` o `USER_CONTEXT.md`).
6. Continuar desde el último handoff relevante sin pedir información ya registrada.
7. No destruir memoria, Redis ni handoffs salvo instrucción explícita.

# Instrucciones progresivas
#include instructions/00-core.md
#include instructions/10-context.md
#include instructions/10-personality.md
#include instructions/20-memory.md
#include instructions/30-redis-panel.md
#include instructions/40-projects.md
#include instructions/50-user-meta.md
#include instructions/90-safety.md
"""

INSTRUCTION_TEMPLATES = {
    "00-core.md": """# 00 Core

Eres el agente principal de **memento** (proyecto mementobloom): un **Agent-Native Memory Curator** de tipo *single-agent*.

> Narrativa 2026 (ByteRover, MAGMA, GAM, Memanto, Claude Code subagents): la memoria es agent-native — el mismo agente que razona CURA y RECUPERA la memoria, no un pipeline externo. memento ya opera así: sus herramientas (`tools/*`) son del agente, no un servicio aparte.

## Arquitectura del agente (declarada)

- **Single-agent, router-first.** No eres un orquestador multi-agente. Resuelves en tu propio contexto; solo delegas a un subagente aislado cuando el trabajo es ruidoso (≥3 archivos, research, o creación masiva). El único subagente hoy es `tutor-cursos/` (ver `agent-main.md`).
- **Working vs Crystallized (split de contexto):**
  - *Working (fluid):* `SESSION.md` + `.memento_runtime/session_canonical.json` + `.agent_context/START_CONTEXT.md` → estado vivo de la sesión.
  - *Crystallized (knowledge graph):* `memory/graph/memory_index.json` → memoria compacta persistente, versionable, portable (markdown/human-readable).
- **Context Tree jerárquico:** la memoria se organiza como Dominio (`mementobloom` / `m360` / `Administracion_UPN` / `jewelry_catalog` / ...) > Tema > Entry, con relaciones explícitas y provenance. Cada entry apunta a su fuente (handoff, doc, git).
- **Retrieval progresivo por tiers** (resuelve la mayoría SIN LLM extra):
  - Tier 0: ¿está en `SESSION.md` / `START_CONTEXT.md`? → úsalo directo.
  - Tier 1: ¿router por nombre de dominio/tema? → `python3 tools/memory_tree.py [--domain X --tags Y]` para ubicar, luego lee el archivo directo (sin subagente). Ver `.agent_context/agent/MAPA_MEMORIA.md`.
  - Tier 2: `python3 tools/context_builder.py --limit N` para decidir por ranking.
  - Tier 3: lectura profunda de handoffs / `context/`.
  - Tier 4: subagente aislado solo si trabajo ruidoso (≥3 archivos / research / creación masiva).

## Comportamiento

- Actúa como curador de memoria histórica y contexto operativo.
- Inicia cada sesión con el flujo completo de arranque: `python3 tools/bootstrap_context.py --print`.
  - Esto verifica los 10 pasos de `PROJECT_META.md`, incluye personalidad, checklist y últimos handoffs.
- Si el usuario pide explícitamente arranque rápido, usa `python3 tools/bootstrap_context.py --fast`.
- Resume el estado del proyecto antes de proponer acciones.
- Confirma el objetivo del usuario usando memoria registrada, sin pedir datos ya disponibles.
- Continúa desde el último handoff relevante.
- Propón próximos pasos concretos y ejecutables.
- **Curación activa (cristalización):** al cerrar sesión, consolida el working→crystallized con este checklist obligatorio:
   1. `python3 tools/quick_scan.py` → escanear todos los proyectos y regenerar el índice.
       - `python3 tools/quick_scan.py <HANDOFF_PATH>` → indexar solo ese handoff o archivo `*_CONTEXT.md`.
  2. Actualizar `memory/graph/memory_index.json`.
  3. Escribir/actualizar `SESSION.md` y `.memento_runtime/session_canonical.json`.
  4. Redactar resumen en sala/panel solo si el usuario lo pide.
  5. Handoff en `projects/mementobloom/HANDOFF_*.md`.
  Ver `docs/ARQUITECTURA_AGENTE_2026.md` §6 para detalle.

## Reglas de enrutamiento (router vs subagent)

- Tarea pequeña/secuencial → resuélvela inline leyendo archivos (Tier 1). NO invoques subagente.
- Tarea ruidosa (≥3 archivos, research, crear 17 lecciones, migrar curso) → delega al subagente aislado `tutor-cursos/`; recibe solo un resumen corto.
- Nunca pierdas la propiedad de la respuesta final: el subagente devuelve resumen, tú sintetizas.
""",
     "10-context.md": """# 10 Contexto

Contexto inicial:
- Lee primero `.agent_context/START_CONTEXT.md` si existe, pero no lo trackees.
- Si el usuario pide contexto, ejecuta `python3 tools/context_builder.py --limit 20`.
- Por defecto, inicia cada sesión con el flujo completo: `python3 tools/bootstrap_context.py --print`.
  - Este modo ejecuta y verifica los 10 pasos de arranque de `PROJECT_META.md` e incluye el checklist y la personalidad del usuario en el output.
- Si el usuario pide explícitamente arranque rápido, usa `python3 tools/bootstrap_context.py --fast`.
  - Omite el checklist detallado y la lectura de `memory/personality/user_personality.md`.
- Usa `.agent_context/START_CONTEXT.md` solo como contexto local regenerable.
- Usa `memory/graph/memory_index.json` como índice compacto de memoria.

Reglas de arranque:
- Por defecto, sigue los 10 pasos listados en `.agent_context/PROJECT_META.md`.
- Resume el estado del proyecto después del bootstrap.
- Identifica el objetivo del usuario.
- Continúa desde el último handoff relevante.
- No repitas instrucciones ya registradas salvo que sea necesario para ejecutar una tarea.

Ubicación de archivos:
- `.agent_context/` → solo contexto del agente (semillas, instrucciones, START_CONTEXT regenerable, secure/).
- `projects/*/HANDOFF_*.md` → registros de gestión, cierres, conciliaciones, auditorías.
- `docs/` → documentación permanente del proyecto.
- Nunca pongas documentación de gestión en `.agent_context/` (rompe el propósito del proyecto).
""",
     "10-personality.md": """# 10 Personalidad

Personalidad operativa:
- Tono: directo, técnico, sin relleno, orientado a ejecución.
- Valores: claridad, trazabilidad, acción, respeto por lo existente.
- Estilo: frases cortas, bullets, resultados verificables. Evita conversational filler y disclaimers.
- Identidad: Kilo — curador de memoria y ejecutor del proyecto.
- Calibración: lee `memory/personality/user_personality.md` para calibrar tono con el usuario.
""",
     "20-memory.md": """# 20 Memoria

Memoria operativa:
- Prioriza HANDOFF recientes.
- Usa `python3 tools/quick_scan.py` para escanear todos los proyectos y regenerar el índice.
- Usa `python3 tools/quick_scan.py <HANDOFF_PATH>` para indexar un handoff o archivo `*_CONTEXT.md` específico.
- Usa `python3 tools/context_builder.py --limit N` para obtener contexto ranked.
- Mantén trazabilidad entre seed → instrucciones → contexto → handoff → acción.
- Si una tarea modifica memoria, handoffs o índices, valida que el cambio sea intencional.

Fuentes de verdad (en orden de prioridad):
1. `SESSION.md` — estado canónico de sesión.
2. `.memento_runtime/session_canonical.json` — backup canónico local inmutable (NO depende de Git).
3. `projects/*/HANDOFF_*.md` — registros de gestión y cierres.
4. `docs/` — documentación permanente del proyecto.
5. Git — último recurso extremo. No confiar en él como fuente primaria entre sesiones (puede reescribirse, force-pushear, o clonarse sin historial).

No borrar:
- No borres memoria.
- No borres Redis.
- No borres handoffs.
- No elimines índices salvo instrucción explícita.

Lecciones aprendidas (2026-06-28):
- Git NO es fuente de verdad confiable entre sesiones. Usar `.memento_runtime/session_canonical.json`.
- `.agent_context/` es para contexto del agente (semillas, instrucciones, START_CONTEXT regenerable). NUNCA poner documentación permanente ni registros de gestión ahí.
- Los registros de gestión (conciliaciones, auditorías, cierres) van en `projects/mementobloom/HANDOFF_*.md` o `docs/`.
- `START_CONTEXT.md` es regenerable y no se trackea. Si aparece en `git status`, revisar si está en el índice (no debería).

Arquitectura de proyectos:
- **Propio:** solo `mementobloom` (se desarrolla a sí mismo)
- **Clientes:** `Management360`, `Administracion_UPN`, `Ventas_Porta` (proyectos independientes desarrollados CON mementobloom)
- **Herramienta propia:** `tools/m360_bridge/` (bridge hacia M360, propiedad de mementobloom)
- No confundir clientes con proyectos propios en `SESSION.md` o `client_projects`
""",
     "30-redis-panel.md": """# 30 Redis y panel

Redis de sala:
- Ver `.agent_context/secure/USER_CONTEXT.md` o `.agent_context/secure/SECURE.md` para configuración de host/puerto.
- Sala local: `python3 tools/sala.py`

Reglas:
- No ejecutes `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- Si necesitas levantar la sala, usa `python3 tools/sala.py`.
- Verifica `/stats` y `/messages` cuando el usuario pregunte por el panel.
""",
     "40-projects.md": """# 40 Proyectos activos

No hay prioridades fijas en este archivo.

Regla operativa:
- Leer `.agent_context/secure/USER_CONTEXT.md` si existe para obtener prioridades contextuales del usuario.
- Si no hay contexto de usuario, priorizar el proyecto activo detectado desde el directorio de trabajo o desde `USER_CONTEXT.md`.
- Para proyectos distintos al activo, usar sus HANDOFF recientes solo cuando el usuario o el contexto lo indiquen.
- No asumir que servicios remotos están activos; verificar antes de operar.
""",
     "50-user-meta.md": """# 50 Usuario y meta del proyecto

Contexto de usuario:
- Lee `.agent_context/PROJECT_META.md` si existe.
- Lee `.agent_context/secure/USER_CONTEXT.md` si existe y úsalo como preferencias, objetivos, infraestructura y reglas operativas del usuario.
- No pidas información ya registrada en `.agent_context/secure/USER_CONTEXT.md`, handoffs o memoria compacta.
- Actualiza `.agent_context/secure/USER_CONTEXT.md` solo cuando el usuario revele preferencias, objetivos, restricciones, infraestructura o decisiones relevantes.

Meta del proyecto:
- Cada sesión debe poder continuar sin depender de un modelo específico.
- El contexto debe ser modelo-agnóstico y legible desde archivos locales.
- Prioriza continuidad sobre dependencias de una UI o modelo concreto.

Arranque recomendado:
- Ejecuta `python3 tools/bootstrap_context.py --print` cuando necesites reconstruir contexto para cualquier modelo.
- Ejecuta `python3 tools/context_builder.py --limit 20` cuando necesites contexto ranked.
- Ejecuta `python3 tools/quick_scan.py` para escanear todos los proyectos cuando quieras refrescar el índice completo.
- Ejecuta `python3 tools/quick_scan.py <HANDOFF_PATH>` cuando aparezca un handoff nuevo y quieras indexar solo ese archivo.

Seguridad:
- No expongas secretos ni contenido de vault.
- No trackees `.agent_context/START_CONTEXT.md`, `.agent_context/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni handoffs.
- No ejecutes operaciones destructivas sobre Redis, memoria o handoffs salvo instrucción explícita.
""",
       "90-safety.md": """# 90 Seguridad

Seguridad operativa:
- No expongas credenciales, secretos ni contenido de vault salvo que sea estrictamente necesario.
- No hagas commits, pushes o force pushes salvo solicitud explícita.
- No borres archivos, memoria, Redis, handoffs ni índices salvo solicitud explícita.
- Si una operación puede ser destructiva, explícala antes de ejecutarla.
- Mantén compatibilidad con la configuración local en `.agent_context/agent_config.json` cuando esa herramienta esté en uso.
- No subas `.agent_context/START_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni datos de sesión.

Prohibiciones operativas:
- No ejecutes limpiezas agresivas con `lsof/xargs kill -9` para cerrar puertos, procesos o servicios del sistema.
  **Caso crítico**: `lsof -ti:8000 | xargs kill -9` detiene el navegador y todos sus procesos asociados al puerto 8000, no solo el servidor Django.
  **Alternativa segura**: usar el PID del proceso específico (`ps aux | grep manage.py`) o `kill -HUP <pid>` para recargar sin matar procesos relacionados.
- Nunca uses comandos de eliminación genérica (kill, flush, delete) sobre servicios compartidos o aplicaciones activas.
- Si existe un servicio activo relevante (web, base de datos, chat, agentes), evita terminarlo sin una instrucción explícita del usuario.
- Antes de realizar cualquier operación potencialmente destructiva, expresa el impacto y espera confirmación.
""",
 }



def file_fingerprint(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def ensure_agent_files():
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_INCLUDE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copy templates from mementobloom if in client mode
    if WS_ROOT != ROOT and (ROOT / ".agent_context" / "agent").exists():
        import shutil
        src_agent = ROOT / ".agent_context" / "agent"
        for f in src_agent.glob("*.md"):
            if not (AGENT_DIR / f.name).exists():
                shutil.copy2(f, AGENT_DIR / f.name)
        for subdir in ["instructions"]:
            src_dir = src_agent / subdir
            if src_dir.exists():
                dst_dir = AGENT_INCLUDE_DIR
                for f in src_dir.glob("*.md"):
                    if not (dst_dir / f.name).exists():
                        shutil.copy2(f, dst_dir / f.name)
    
    # Always sync AGENT_INIT with current INIT_TEMPLATE to ensure all progressive instructions are included
    AGENT_INIT.write_text(INIT_TEMPLATE, encoding="utf-8")
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
    entries = [e for e in index.values() if isinstance(e, dict)]
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


def client_project_paths() -> list[str]:
    """Lee .agent_context/secure/client_projects.json y devuelve líneas de contexto cliente."""
    path = CLIENT_PROJECTS_JSON
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    lines = []
    for name, meta in data.items():
        if not isinstance(meta, dict):
            continue
        lines.append(f"- **{name}**")
        for key in ("source", "venv", "repo", "branch", "production", "memento_docs"):
            value = meta.get(key)
            if value:
                label = {
                    "source": "Fuente local",
                    "venv": "venv",
                    "repo": "Repo GitHub",
                    "branch": "rama",
                    "production": "Producción",
                    "memento_docs": "Documentación Memento",
                }.get(key, key)
                lines.append(f"- {label}: {value}")
    return lines


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

    active_project = project or WS_ROOT.name
    lines = [
        "---",
        "description: Curador de memoria histórica del proyecto",
        f"project: {active_project}",
        "mode: primary",
        "model: kilo/kilo-auto/free",
        "steps: 25",
        "---",
        f"<!-- generated-hash: {signature} -->",
        "",
    ]

    for path, content, ok in loaded:
        label = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        instruction_content = content.strip()
        if path.name == "00-core.md":
            instruction_content = instruction_content.replace(
                "Eres el agente principal del proyecto.",
                f"Eres el agente principal del proyecto **{active_project}**."
            )
        lines.extend([
            "",
            f"### {label} {'OK' if ok else 'MISSING'}",
            instruction_content,
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
        f"- Entorno limpio: {(rel(SECURE_CONTEXT) if SECURE_CONTEXT.exists() else '.agent_context/secure/SECURE.md')} define preferencias locales.",
        f"- Aislamiento estricto: este agente pertenece exclusivamente al proyecto **{active_project}**. No mezcles contexto de otros proyectos.",
    ])
    lines.extend(user_context_short(limit=4))
    paths = client_project_paths()
    if paths:
        lines.extend([
            "",
            "## Rutas de proyectos cliente",
        ])
        lines.extend(paths)
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
    entries = [e for e in index.values() if isinstance(e, dict)]
    if project:
        entries = [e for e in entries if e.get("project") == project]
    entries.sort(key=lambda e: entry_sort_key(e, project), reverse=True)
    selected = entries[:limit]
    agent = agent_result or {"status": "skipped", "path": str(AGENT_SEED), "hash": "?"}
    lines = [
        "# MementoBloom Startup Context",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Workspace: {rel(WS_ROOT)}",
        f"Project: {project}",
        f"Index entries: {len(index)}",
        "",
        "## Startup instruction",
        "Prepara la semilla progresiva del agente, lee el contexto inicial y continúa desde el último handoff relevante sin pedir información ya registrada.",
        "",
        "## Agent instructions (MAIN AGENT ONLY)",
        f"Path: `.agent_context/agent/instructions/`",
        "Estado: OBLIGATORIO para agente main y agentes generados desde memento",
        "Archivos:",
    ]
    for name in sorted(INSTRUCTION_TEMPLATES.keys()):
        lines.append(f"- {name}")
    lines.extend([
        "Regla: El agente main DEBE cargar todas estas instrucciones. No hay excepción. Solo agentes externos no-memento pueden reconstruir desde PROJECT_META.md.",
        "",
    ])
    lines.extend(local_context_summary(PROJECT_META, "Project meta"))
    lines.extend(local_context_summary(USER_CONTEXT, "User context"))
    paths = client_project_paths()
    if paths:
        lines.append("## Rutas de proyectos cliente")
        lines.extend([f"- {line}" for line in paths])
        lines.append("")
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
        "## Git state",
        f"- {git_status_summary()}",
        "",
        "## Memory scan",
    ])
    try:
        scan = subprocess.run(
            ["python3", "tools/quick_scan.py"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(WS_ROOT),
        )
        if scan.returncode == 0:
            for line in scan.stdout.splitlines():
                if line.strip():
                    lines.append(f"- {line.strip()}")
        else:
            lines.append(f"- Quick scan: error ({scan.stderr.strip()[:100]})")
    except Exception as exc:
        lines.append(f"- Quick scan: error ({exc})")
    lines.extend([
        "",
        "## Services",
    ])
    try:
        services_data = core_service_status(fresh=False)
        lines.append(core_service_summary(services_data))
    except Exception as exc:
        lines.append(f"- Services: error ({exc})")
    lines.extend([
        "",
        "## Health check",
    ])
    try:
        health = subprocess.run(
            ["python3", "tools/doctor.py", "--startup", "--no-services"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(WS_ROOT),
        )
        if health.returncode == 0:
            for line in health.stdout.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("MementoBloom Doctor") and not stripped.startswith("Status:") and not stripped.startswith("Project:") and not stripped.startswith("Working") and stripped != "Checks:":
                    lines.append(f"- {stripped}")
        else:
            lines.append(f"- Doctor: error ({health.stderr.strip()[:100]})")
    except Exception as exc:
        lines.append(f"- Doctor: error ({exc})")
    lines.extend([
        "",
        "## Bootstrap context",
    ])
    try:
        bootstrap_proc = subprocess.run(
            ["python3", "tools/bootstrap_context.py", "--print", "--no-services", "--limit", str(limit or 8), "--fast"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(WS_ROOT),
        )
        if bootstrap_proc.returncode == 0:
            lines.append(bootstrap_proc.stdout.strip())
        else:
            lines.append(f"- Bootstrap context: error ({bootstrap_proc.stderr.strip()[:200]})")
    except Exception as exc:
        lines.append(f"- Bootstrap context: error ({exc})")
    lines.extend([
        "",
        "## Safe next-session commands",
    ])
    return "\n".join(lines) + "\n"


def write_context(text: str):
    START_CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = WS_ROOT / ".memento_runtime" / "backups"
    if START_CONTEXT.exists():
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"start_context_{ts}.md"
            backup_path.write_text(START_CONTEXT.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    tmp_fd, tmp_path = tempfile.mkstemp(dir=START_CONTEXT.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, START_CONTEXT)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def local_context_summary(path: Path, title: str) -> list[str]:
    if not path.exists():
        return [f"## {title}", f"- `{path}` no existe todavía.", ""]
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [f"## {title}", f"- Path: `{rel(path)}`", "- Estado: local/contextual"]
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(f"- {stripped}")
        if len(lines) >= 12:
            break
    lines.append("")
    return lines


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
    password = os.environ.get("REDIS_PASSWORD")
    try:
        with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=timeout) as sock:
            if password:
                sock.sendall(f"*2\r\n$4\r\nAUTH\r\n${len(password)}\r\n{password}\r\n".encode("utf-8"))
                auth_resp = sock.recv(128).decode(errors="replace")
                if not auth_resp.startswith("+OK"):
                    return {"ok": False, "detail": "AUTH failed"}
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
        cwd=str(WS_ROOT),
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


def _sync_kilo_agent() -> None:
    """Sync the generated agent seed to .kilo/agents/ so Kilo CLI can consume it."""
    try:
        kilo_agent_dir = WS_ROOT / ".kilo" / "agents"
        kilo_agent_dir.mkdir(parents=True, exist_ok=True)
        dest_path = kilo_agent_dir / "agent-main.md"
        if AGENT_SEED.exists():
            dest_path.write_text(AGENT_SEED.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as exc:
        # Non-fatal: Kilo fallback agents remain available if sync fails.
        print(f"[session_start] Warning: failed to sync agent seed to .kilo/agents/: {exc}")


def git_status_summary() -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(WS_ROOT), "status", "--short"],
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
        return str(path.relative_to(WS_ROOT))
    except ValueError:
        return str(path)


def quick_startup_report(limit: int = 8, project: str | None = None) -> str:
    index = load_index(resolve_index_path(workspace=WS_ROOT))
    entries = [e for e in index.values() if isinstance(e, dict)]
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
        f"Workspace: {rel(WS_ROOT)}",
        f"Project: {project}",
        f"Context file: {rel(START_CONTEXT)}",
        f"User context: {rel(USER_CONTEXT) if USER_CONTEXT.exists() else '.agent_context/secure/USER_CONTEXT.md (no existe)'}",
        f"Project meta: {rel(PROJECT_META)}",
        f"Agent seed: {seed['status']} hash={seed['hash']}",
        f"Memory index: {len(index)} entries",
        f"Git: {git_status_summary()}",
        "",
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
        f"- `python3 tools/session_start.py --quick --limit 8` (proyecto por defecto: {WS_ROOT.name})",
        "- `python3 tools/bootstrap_context.py --print` imprime contexto universal para cualquier modelo.",
        "- `python3 tools/optimize_agent.py --context` audita y resume el entorno operativo.",
        "- `python3 tools/session_start.py --services-only`",
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


ALLOWED_AGENT_CLIS = {
    "kilo": ["run"],
    "claude": ["run"],
    "code": [""],
    "memento_start": [],
}


def _split_command(command: str) -> list[str] | None:
    """Safely split a command string into argv list.

    Rejects empty commands and commands with null bytes.
    Returns None if the command looks unsafe for direct execution.
    """
    if not command or not command.strip():
        return None
    if "\x00" in command:
        return None
    try:
        import shlex
        return shlex.split(command)
    except ValueError:
        return None


def _validate_command(argv: list[str]) -> tuple[bool, str]:
    """Validate command argv against known safe CLI patterns.

    Returns (is_safe, reason).
    """
    if not argv:
        return False, "empty command"
    cli = Path(argv[0]).name
    if cli not in ALLOWED_AGENT_CLIS:
        return False, f"unknown CLI '{cli}'"
    allowed = ALLOWED_AGENT_CLIS[cli]
    if allowed and (len(argv) < 2 or argv[1] not in allowed):
        return False, f"'{cli}' requires one of {allowed} as subcommand"
    return True, "ok"


def _run_command_safe(command: str) -> int:
    """Execute command with safety checks, avoiding shell=True when possible."""
    argv = _split_command(command)
    if argv is None:
        print(f"WARN: unsafe/null command, skipping: {command!r}")
        return 1
    safe, reason = _validate_command(argv)
    if not safe:
        print(f"WARN: command rejected ({reason}): {command!r}")
        return 1
    try:
        env = os.environ.copy()
        env.setdefault("MEMENTO_WORKSPACE", str(workspace_root()))
        result = subprocess.run(argv, cwd=str(workspace_root()), check=False, env=env)
        return result.returncode
    except FileNotFoundError:
        print(f"ERROR: CLI not found: {argv[0]}")
        return 1


def launch_external_agent(command: str | None = None) -> int:
    agent_command = command or os.environ.get("MEMENTO_AGENT_CMD")
    if not agent_command:
        print("\nNo external agent command configured.")
        print("Set MEMENTO_AGENT_CMD or pass --agent-command to start an agent/CLI.")
        print("Example: MEMENTO_AGENT_CMD='<agent-cli> run --dir .' python3 tools/session_start.py --print --launch-agent")
        return 0

    ws = workspace_root()
    if "kilo run" in agent_command:
        if "--dir ." in agent_command:
            agent_command = agent_command.replace("--dir .", f'--dir "{ws}"')
        elif "--dir" not in agent_command:
            agent_command = agent_command.replace("kilo run", f'kilo run --dir "{ws}"')

    print("\nLaunching external agent:")
    print(f"  {agent_command}")
    sys.stdout.flush()
    return_code = _run_command_safe(agent_command)
    if "agent-onboarding" in agent_command and return_code == 0:
        marker = WS_ROOT / ".agent_context" / "secure" / "ONBOARDED"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=True)
        print("\nOnboarding marked as completed: .agent_context/secure/ONBOARDED")
    return return_code


def normalize_argv(argv: list[str]) -> list[str]:
    # Con default=None en argparse, ya no necesitamos forzar valor por defecto aquí
    return argv


def main():
    parser = argparse.ArgumentParser(description="Prepare the progressive agent seed and local context")
    parser.add_argument("--limit", type=int, default=14)
    parser.add_argument("--project", default=None)  # Por defecto usa el directorio actual
    parser.add_argument("--print", action="store_true", help="Print context (read-only by default; use --prepare-seed/--write-start-context to mutate)")
    parser.add_argument("--quick", action="store_true", help="Print a lightweight local-only startup report and exit")
    parser.add_argument("--services", action="store_true", help="Start optional local services after agent/context preparation")
    parser.add_argument("--services-only", action="store_true", help="Start local services and exit")
    parser.add_argument("--no-services", action="store_true", help="Do not start optional local services")
    parser.add_argument("--no-agent-seed", action="store_true", help="Do not prepare the progressive agent seed before building context")
    parser.add_argument("--no-write-context", action="store_true", help="Do not write .agent_context/START_CONTEXT.md")
    parser.add_argument("--prepare-seed", action="store_true", help="Explicitly regenerate the progressive agent seed before building context")
    parser.add_argument("--write-start-context", action="store_true", help="Explicitly write .agent_context/START_CONTEXT.md")
    parser.add_argument("--force-seed", action="store_true", help="Force progressive agent seed regeneration")
    parser.add_argument("--launch-agent", action="store_true", help="Launch external agent command after context preparation")
    parser.add_argument("--agent-command", default=None, help="External agent/CLI command to launch when --launch-agent is used")
    args = parser.parse_args(normalize_argv(sys.argv[1:]))
    project = args.project or WS_ROOT.name  # Use workspace name for default project

    if args.quick:
        print(quick_startup_report(limit=args.limit, project=project), end="")
        return 0

    if args.services_only:
        print_services(ensure_services())
        return 0

    if args.no_agent_seed:
        agent_result = {"status": "skipped", "path": str(AGENT_SEED), "hash": "?"}
    else:
        agent_result = ensure_agent_seed(force=args.force_seed or args.prepare_seed, project=project)
        _sync_kilo_agent()

    context = build_context(limit=args.limit, project=project, agent_result=agent_result)
    if not args.no_write_context:
        write_context(context)

    # T3.5: Expandir con contexto universal de bootstrap en el flujo único
    bootstrap_context_text = ""
    if args.print and not args.no_write_context:
        bootstrap_proc = subprocess.run(
            ["python3", "tools/bootstrap_context.py", "--print", "--no-services", "--fast"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(WS_ROOT)
        )
        if bootstrap_proc.returncode == 0:
            bootstrap_context_text = bootstrap_proc.stdout.strip()
        else:
            bootstrap_context_text = f"\n[bootstrap] Warning: bootstrap failed (exit={bootstrap_proc.returncode})\n"
    
    # Imprimir contexto completo unificado
    print(context, end="")
    if bootstrap_context_text:
        print("\n" + bootstrap_context_text)
    print_agent_seed(agent_result)
    sys.stdout.flush()

    if args.services or args.services_only:
        print_services(ensure_services())

    if args.launch_agent:
        return launch_external_agent(args.agent_command)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
