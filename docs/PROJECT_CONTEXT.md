# Mapa de Contexto — MementoBloom

> Generado por consolidación de docs/ y memoria indexada
> Ruta: `/Volumes/Macintosh HD - Datos/mementobloom`

---

## Resumen de arquitectura

| Capa | Directorio | Descripción |
|------|------------|-------------|
| Core | `core/` | Módulos compartidos: paths, git, index, services, health |
| Tools | `tools/` | CLI tools: session_start, bootstrap_context, quick_scan, doctor, configure, m360_bridge, sync_sprint |

### Uso correcto de la API M360 (`/api/v1/`)

**Base URL:** `http://127.0.0.1:8000`  
**Auth:**  
- Lectura (`GET`): abierta.  
- Escritura (`POST`/`PATCH`/`PUT`/`DELETE`): requiere header `Authorization: Bearer <M360_API_KEY>`  
  - `M360_API_KEY` se carga desde `.env`  
  - Si no existe, la escritura es rechazada con `403`

**Cliente recomendado:** `tools/m360_bridge/client.py`  
- Carga automáticamente credenciales y API key desde `.env`  
- Inyecta el Bearer token solo en operaciones de escritura  
- Maneja CSRF/Session para endpoints que lo requieran

**Notas técnicas:**
- Para marcar una tarea como completada, usar `client.api_v1_update_task_status(id, "Completed")`  
  - Internamente envía `task_status_id=4` (campo writable en `TaskSerializer`)  
- El campo `done` es escribible en M360 v1 (`api/v1/serializers.py`) y alimenta `stats.tasks_completed`  
- No hardcodear `127.0.0.1` ni puertos; usar variables `M360_BASE_URL`, `SALA_HOST`, `PANEL_HOST`, `REDIS_HOST`

**Verificación rápida:**
```bash
python3 tools/m360_auth_test.py
python3 tools/project_status.py
```
| Panel | `panel_server.py` | Dashboard HTTP (8766) |
| Sala | `sala.py` | Sala de mensajes HTTP+Redis (8767) |
| Vault | `vault_*.py` | Gestión de credenciales |
| Models | `models/` | Modelos de dominio (grafo de memoria) |
| Memory | `memory/` | Índice compacto, seeds, sesiones |
| GTD | `gtd_memento/` | Origen de verdad de sprints, tareas, inbox y estado GTD |
| Config | `config/` | Configuración JSON de servicios |
| Docs | `docs/` | Documentación técnica permanente |
| Projects | `projects/` | Handoffs por proyecto |
| Archive | `archive/` | Backups y datos obsoletos |
| Agent | `.agent_context/` | Contexto, seeds, instrucciones del agente |
| Módulo | `memento/` | Paquete cliente para proyectos externos |

---

## Entry Points / CLI

```toml
[project.scripts]
memento-bootstrap = "tools.bootstrap_context:main"
memento-doctor = "tools.doctor:main"
memento-session-start = "tools.session_start:main"
memento-quick-scan = "tools.quick_scan:main"
```

_Wrappers bash en raíz:_ `memento-init`, `session_start`, `bootstrap_context`, `quick_scan`, `optimize_agent`, `optimize_memento`, `memento-clean`, `memento-export`

_Servicios:_ `panel_server.py` (8766), `sala.py` (8767)

---

## Dependencias

- Python >= 3.9
- Build: `setuptools`, `wheel`
- Runtime: stdlib-only (futuro: sentence-transformers, faiss-cpu)
- Redis: accesible (no requiere cliente Python; usa socket RAW)

---

## Estructura de directorios

```
mementobloom/
├── .agent_context
│   ├── agent
│   │   ├── instructions
│   │   │   ├── 00-core.md
│   │   │   ├── 10-context.md
│   │   │   ├── 20-memory.md
│   │   │   ├── 30-redis-panel.md
│   │   │   ├── 40-projects.md
│   │   │   ├── 50-user-meta.md
│   │   │   └── 90-safety.md
│   │   ├── agent-main.md
│   │   ├── agent-onboarding.md
│   │   ├── init.md
│   │   └── ...
│   ├── secure
│   │   ├── SECURE.md
│   │   ├── USER_CONTEXT.md
│   │   └── VAULT.md
│   ├── PROJECT_META.md
│   └── START_CONTEXT.md
├── .memento_runtime
│   ├── logs
│   ├── pids
│   └── health_cache.json
├── archive
│   ├── backups
│   │   └── memory_graph
│   └── generated
├── config
│   └── services.json
├── core
│   ├── __init__.py
│   ├── git.py
│   ├── health.py
│   ├── index.py
│   ├── paths.py
│   └── services.py
├── docs
│   ├── ANALISIS_M360_INTEGRACION.md
│   ├── CLEAN_INSTALL_GUARANTEE.md
│   ├── CONTROL_GESTION_M360.md
│   ├── FASE_1_REORGANIZACION.md
│   ├── FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md
│   ├── FASE_3_FLUJO_OPERATIVO.md
│   ├── FASE_3_INTEGRACION_M360.md
│   ├── PROJECT_CONTEXT.md
│   └── STARTUP_OPTIMIZATION_PLAN.md
├── memory
│   └── graph
│       ├── graph.json
│       ├── index_manifest.json
│       ├── memory_index.json
│       └── optimization_stats.json
├── models
│   ├── __init__.py
│   └── memory_graph.py
├── projects
│   ├── Ventas_Porta
│   │   ├── .agent_context
│   │   ├── .memento_runtime
│   │   └── HANDOFF_*.md
│   └── mementobloom
│       ├── HANDOFF_*.md
│       └── ...
├── tools
│   ├── m360_bridge/
│   ├── projects/
│   ├── configure.py
│   ├── sync_sprint.py
│   ├── bootstrap_context.py
│   ├── doctor.py
│   ├── quick_scan.py
│   ├── session_start.py
│   └── ...
├── uploads
├── NEXT_SESSION.md
├── README.md
├── handoff_gen.py
├── memento_cli.py
├── panel_server.py
├── pyproject.toml
├── requirements.txt
├── sala.py
└── vault_*.py
```

---

## Documentación técnica (`docs/`)

| Documento | Propósito |
|-----------|-----------|
| `FASE_1_REORGANIZACION.md` | Histórico de Fase 1 |
| `FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md` | Arquitectura, requisitos y protocolos de Fase 3 |
| `FASE_3_FLUJO_OPERATIVO.md` | Metodología de sprints y flujo de trabajo |
| `FASE_3_INTEGRACION_M360.md` | Especificación técnica de integración con M360 |
| `ANALISIS_M360_INTEGRACION.md` | Análisis exhaustivo de M360 (proyecto externo) |
| `CONTROL_GESTION_M360.md` | Protocolo de operación de M360 como gestor de proyectos |
| `CLEAN_INSTALL_GUARANTEE.md` | Garantía de amnesia limpia en instalaciones cliente |
| `STARTUP_OPTIMIZATION_PLAN.md` | Plan de optimización de arranque |
| `PROJECT_CONTEXT.md` | Este documento: índice maestro de contexto |

---

## Memoria de sesión (`projects/mementobloom/`)

Handoffs relevantes por tema:

| Tema | Handoff |
|------|---------|
| Fase 3 / Arquitectura | `HANDOFF_2026-06-25_transicion_ejecucion.md` |
| Fase 3 / Memoria | `HANDOFF_2026-06-25_memoria_sesion_fase3.md` |
| Integración M360 | `HANDOFF_2026-06-26_cierre_integracion_m360.md` |
| Verificación / Proyecto 60 | `HANDOFF_2026-06-26_verificacion_recreacion.md` |
| Sprint 0 | `HANDOFF_2026-06-26_cierre_sprint0.md` |
| Sprint 1 | `HANDOFF_2026-06-26_cierre_sprint1.md` |
| Estado real M360 | `HANDOFF_2026-06-26_correccion_estado_real_m360.md` |
| Cierre sesión | `HANDOFF_2026-06-26_cierre_sesion.md` |
| Auth M360 v1 | `projects/Management360/handoffs/HANDOFF_2026-06-27_174500_mb_auth_strategy.md` |
| Cierre sesión 2026-06-27 | `projects/mementobloom/HANDOFF_2026-06-27_183500_cierre_sesion.md` |

_El índice completo está en `memory/graph/memory_index.json` (162 entradas)._

---

## Estado sincronizado en Management360

- **Proyecto M360:** ID `78` — `MementoBloom - S-27-06`
- **Tareas Sprint 0:** IDs `278`–`280` → `Completed` + `done=True`
- **Tareas Sprint 2:** IDs `285`–`288` → `To Do` (T2.1–T2.4)
- **Auth:** Bearer `M360_API_KEY` activo para escritura en `/api/v1/`
- **Cliente:** `tools/m360_bridge/client.py` actualizado para usar `task_status_id` en updates

---

## Cliente Ventas_Porta (`projects/Ventas_Porta/`)

| Componente | Estado |
|------------|--------|
| `.agent_context/` | Instalado |
| `memory/graph/memory_index.json` | Inicializado (vacío) |
| `selftest` | OK |
| `doctor --startup` | OK |

---

## Servicios

| Servicio | Estado |
|----------|--------|
| Redis | NO (sin servidor local) |
| Sala | OK en http://127.0.0.1:8767 |
| Panel | OK en http://127.0.0.1:8766 |
