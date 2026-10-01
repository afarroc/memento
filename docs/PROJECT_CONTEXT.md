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
│   ├── AGENTE_TUTOR_CURSOS.md
│   ├── ARQUITECTURA_AGENTE_2026.md
│   ├── AUDITORIA_PROYECTO.md
│   ├── CLEAN_INSTALL_GUARANTEE.md
│   ├── CONTEXT_TREE.md
│   ├── FASE_1_REORGANIZACION.md
│   ├── FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md
│   ├── FASE_3_FLUJO_OPERATIVO.md
│   ├── FASE_3_INTEGRACION_M360.md
│   ├── FASE_3_M360_API_SPEC.md
│   ├── ITCSS_M360_LAYOUT_STANDARD.md
│   ├── PERSONALIDAD_AGENTE.md
│   ├── PROJECT_CONTEXT.md
│   ├── SESSION_CONTRACT.md
│   ├── STARTUP_OPTIMIZATION_PLAN.md
│   ├── tickets.md
│   └── guides
│       └── register-client.md
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
│   ├── mementobloom
│   │   ├── docs
│   │   │   ├── tickets.md
│   │   │   └── tareas_proyecto.md
│   ├── Management360
│   │   ├── docs
│   │   │   ├── guides
│   │   │   │   └── nomenclatura.md
│   │   │   ├── tareas_proyecto.md
│   │   │   ├── tareas_final.md
│   │   │   └── pending_tasks.md
│   ├── TaxiLima2026
│   │   ├── docs
│   │   └── handoffs
│   │       └── HANDOFF_2026-08-16_nomenclatura_tareas.md
│   ├── Carpinteria
│   │   ├── docs
│   │   │   ├── nomenclatura_tareas.md
│   │   │   └── tareas_proyecto.md
│   │   └── handoffs
│   │       └── HANDOFF_2026-08-25_ajuste_nomenclatura_tareas_m360.md
│   ├── perfil_personal
│   │   ├── docs
│   │   │   └── nomenclatura_tareas.md
│   │   └── handoffs
│   ├── poco_xiaomi
│   │   ├── docs
│   │   │   ├── nomenclatura_tareas.md
│   │   │   └── tareas_proyecto.md
│   │   └── handoffs
│   └── ...
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
| `CLEAN_INSTALL_GUARANTEE.md` | Garantía de amnesia limpia en instalaciones cliente |
| `STARTUP_OPTIMIZATION_PLAN.md` | Plan de optimización de arranque |
| `PROJECT_CONTEXT.md` | Este documento: índice maestro de contexto |
| `tickets.md` | Sistema de tickets de servicio |
| `guides/register-client.md` | Procedimiento de registro/migración de clientes |
| `informe_perfil_schedule_m360.md` | Informe de integración del tab Horario de perfil_personal con M360 |
| `nomenclatura_m360.md` | Nomenclatura oficial de tareas M360 por proyecto |

### Documentación de proyectos cliente

- `projects/Management360/docs/` — análisis, control de gestión, contexto de events, tareas pendientes/finales y mapa de reemplazo ITCSS de events. Nomenclatura: `M360-*`, `DIGIT-*`, `CV-REVIEW-*`, `TASK-BITACORA-*`.
- `projects/TaxiLima2026/docs/` — migración a M360 y optimización de arquitectura de simulación. Nomenclatura: `TAXI-*`.
- `projects/Carpinteria/docs/` — ecosistema software abierto para carpintería/bricolaje. Nomenclatura: `CARP-*`.
- `projects/perfil_personal/docs/` — dashboard personal Arturo. Nomenclatura: `PERFIL-*`.
- `projects/poco_xiaomi/docs/` — servidor Termux POCO X3 NFC. Nomenclatura: `POCO-*`.
  - Código fuente real: `/Volumes/Macintosh HD - Datos/projects/poco_xiaomi/`
  - Documentación de gestión memento: `mementobloom/projects/poco_xiaomi/`
- `projects/Administracion_UPN/docs/` — arquitectura de digitalización/linea de producción de microformatos, sílabos y material de ciclo.

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
| Corrección nomenclatura tickets | `HANDOFF_2026-08-31_correccion_nomenclatura_tickets.md` |
| Corrección nomenclatura tareas M360 | `HANDOFF_2026-08-31_correccion_nomenclatura_tareas_m360.md` |
| Ticket cámara POCO | `HANDOFF_2026-08-31_ticket_camara_poco_reconocimiento.md` |
| Fix timeouts Daphne API v1 tasks | `HANDOFF_2026-09-08_m360_daphne_timeout_fix.md` |

_El índice completo está en `memory/graph/memory_index.json` (528 entradas)._

---

## Estado sincronizado en Management360

- **Repositorio:** `/Volumes/Macintosh HD - Datos/projects/Management360`
- **Rama:** `main`
- **Último commit:** `7e40e075` (`m360(digitalizacion): add module README`)
- **Commits recientes (2026-09-25):**
  - `61d82616` `m360(digitalizacion): fix checksum pipeline and preprocessor validation`
  - `5159eab5` `m360(digitalizacion): renew quality and certification templates`
  - `c6e4cec5` `m360(digitalizacion): renew preparation, reception and navigation layouts`
  - `3dc922e3` `m360(digitalizacion): implement OCR/PDF/A, LLM assistant and websocket support`
  - `38e78139` `m360(cv): refactor curriculum templates, models and styles`
  - `d5fc9886` `m360(api): extend v1 API and task views`
  - `61ee906a` `m360(panel): update asgi settings and routing`
  - `111db3e8` `m360(global): unify styles and base layout`
  - `b97dab01` `m360(vision): add object detection module and utilities`
  - `5c4c61ed` `m360(infra): update dependencies, tooling and project docs`
  - `d643d7a5` `m360(accounts): unify login template and styles`
  - `f92c62e7` `m360(bitacora): remove crispy forms dependency from templates`
  - `7e40e075` `m360(digitalizacion): add module README`
- **Working tree:** limpio
- **Proyecto M360:** ID `22` — `Management360`
- **Proyectos registrados:**
  - `perfil_personal` ID `24` — `55` tareas, `6` completadas
  - `TaxiLima2026` ID `23` — `75` tareas, `20` completadas
  - `Carpinteria` ID `25` — `15` tareas
  - `poco_xiaomi` ID `26` — `11` tareas
  - `Management360` ID `22` — `86` tareas, `2` completadas
  - `Memento` ID `21` — `31` tareas
- **Auth:** Bearer `M360_API_KEY` activo para escritura en `/api/v1/`
- **Cliente:** `tools/m360_bridge/client.py` actualizado para usar `task_status_id` en updates
- **Bitácora API v1:** expuesta en `/api/v1/bitacora/` y `/api/v1/bitacora/attachments/`
  - `BitacoraEntrySerializer` + `BitacoraEntryViewSet` en `api/v1/serializers.py` y `api/v1/views.py`
  - Filtros: `categoria`, `mood`, `project_id`, `task_id`, `event_id`, `is_public`
  - `BitacoraAttachmentViewSet` en `/api/v1/bitacora/attachments/`
- **Optimizaciones aplicadas (2026-09-08):**
  - `TaskViewSet.queryset` incluye `prefetch_related("dependencies", "reminder_set")`
  - Vistas de tareas reemplazan N+1 en `taskstate_set` por `Prefetch` precomputado
  - `TaskSerializer` calcula `dependencies`, `events_linked` y `reminders_linked` solo con `?include=...`
  - Tiempos de respuesta medidos entre `~5.2s` y `~6.4s` para `limit=20` en listados por proyecto
- **Digitalización:**
  - Pipeline: Recepcion → Preparacion → Digitalizacion → CC1 → Preprocesamiento → Metadatos/OCR → QC2 → Auditoria → Certificacion
  - Checksum pipeline fix: `SHA-256`/`MD5` calculados en preprocesamiento/metadatos antes de QC2
  - Preprocesamiento DPI default: `300`, detección de `original_dpi`, advertencia si `< 300`
  - QC2 manual approve respetado; vista no fuerza rechazo automático
  - Auditoría renovada: layout `audit-layout`, preview OCR, timeline pipeline
  - LLM assistant: `llm_service.py` contra POCO, template `asistente_documento.html`
  - WebSockets: `consumers.py`, `routing.py`
  - Documentación: `digitalizacion/docs/**`, `digitalizacion/tests/**`
  - Vision: módulo `vision/**`, utilities `src/vision_api_service.py`
- **Handoffs M360 recientes:**
  - `HANDOFF_2026-09-25_qc2_checksum_pipeline_fix.md`
  - `HANDOFF_2026-09-25_auditoria_vista_renovada.md`
  - `HANDOFF_2026-09-25_auditoria_template_recreado.md`
  - `HANDOFF_2026-09-25_preprocesamiento_dpi_default_advertencia.md`
  - `HANDOFF_2026-09-25_preprocessor_binarization_fix.md`
  - `HANDOFF_2026-09-25_qc2_aprobacion_manual_advertencias.md`
  - `HANDOFF_2026-09-25_anotador_optimizacion_init.md`
  - `HANDOFF_2026-09-25_preprocesamiento_comparison_metadata_zoom.md`

---

## Clientes registrados

| Cliente | M360 ID | Nomenclatura tareas | Estado |
|---------|---------|---------------------|--------|
| perfil_personal | 24 | `PERFIL-*` | Activo |
| TaxiLima2026 | 23 | `TAXI-*` | Activo |
| Carpinteria | 25 | `CARP-*` | Activo |
| poco_xiaomi | 26 | `POCO-*` | Activo |
| Management360 | 22 | `M360-*`, `DIGIT-*`, `CV-REVIEW-*`, `TASK-BITACORA-*` | Activo |
| Ventas_Porta | — | — | Registrado |
| Administracion_UPN | — | — | Registrado |
| jewelry_catalog | — | — | Registrado |
| LaMarca | — | — | Registrado |
| miui_termux | — | — | Registrado |
| novela_bl | — | — | Registrado |
| adherence_test | — | — | Registrado |
| banca_telefonica | — | — | Registrado |
| civilizaciones | — | — | Registrado |

---

## Servicios

| Servicio | Estado |
|----------|--------|
| Redis | OK (cloud: redis-11059.c81.us-east-1-2.ec2.cloud.redislabs.com:11059) |
| Sala | STARTED (http://127.0.0.1:8767) |
| Panel | STARTED (http://127.0.0.1:8766) |
| M360 backend | OK (http://127.0.0.1:8000) |
| perfil_personal frontend | OK (http://127.0.0.1:8080) |
| perfil_personal chat | OK |

---

## Próximos pasos globales

1. Aplicar el mismo patrón de `Prefetch` en vistas HTML que iteran `taskstate_set`.
2. Evaluar cache Redis para listados de tareas por proyecto.
3. Revisar timeouts de Daphne/ASGI si persiste lentitud en picos de carga.
4. Sincronizar tickets bridge con el estado actual de M360 cuando se requiera.
5. Verificar persistencia del servicio LLM en `poco_xiaomi` tras reinicio.
