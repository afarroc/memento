# Changelog

Todas los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Sin lanzamiento]

### Agregado
- Implementación completa de la arquitectura dual (`mementobloom` como paquete + cliente de memoria) (#4746eb1)
- `Bootstrap_context` mejorado y generación automática de `START_CONTEXT.md` en sesión (#05694bc)
- Backend de búsqueda en `context_retriever` y rutas de workspace cliente (#1456201)

### Cambiado
- `ALLOWED_HOSTS` saneado y rutas de IP hardcodeadas reemplazadas por `localhost` en `panel_server.py` (#0626740)
- Timeouts y configuración de Workspace Root (WS_ROOT) migrados a variables de entorno (#7a2e355)
- Namespacing unificado en Redis para `tools/optimize_agent.py` y `tools/restore_sala.py` usando `detect_project_name()` (#0626740)

### Corregido
- Rutas del wrapper de cliente en `memento_install` corregidas (#b2fc124)
- Citas de ruta workspace en sustitución `kilo --dir` (#e63c2c9)
- Rutas del agente de lanzamiento y scripts `memento-start` (#ddbafa9, #cc276ac)
- Detección de workspace, imports `session_start` y `doctor` (#7d22bc7, #0dbf9af, #231b358)
- Parseo de keywords como cadena separada por comas en `context_retriever` (#3949253)

### Eliminado
- Exclusión de `gtd_memento/` de versionado (dato local del usuario, no código core) (#0626740)
- Documentos obsoletos y rutas `.kilo/` de referencias (#7a2e355)

### Seguridad
- Credenciales y secretos saneados de configuración e IPs hardcodeadas (#0626740, #7a2e355)
- Documentación de políticas de limpieza no destructivas en agentes (#incluye instrucciones 30, 90)

### Documentación
- Actualización de `NEXT_SESSION.md` y `docs/PROJECT_CONTEXT.md` (#4778b3a)
- Especificación API genérica: `docs/FASE_3_M360_API_SPEC.md`

---

## [Unreleased]
### Pendiente
- Commit de cambios locales de Management360 pendientes de versionar

---

## 2026-06-27 — Integración M360 API v1
- API genérica `/api/v1/` implementada y verificada en Management360 (projects, tasks, events, reminders, inbox)
- Serializers extendidos con campos escribibles (`project_status_id`, `host_id`, `assigned_to_id`, `task_status_id`, `event_status_id`)
- Evolución de `tools/m360_bridge/client.py` con métodos API v1 (`_request_json`, `api_v1_*`)
- Evolución de `tools/sync_sprint.py` para consumir `/api/v1/` (project+tareas+eventos+recordatorios)
- Sincronización de sprint verificada: `ok=7 errors=0` (proyecto + 3 tareas + 2 eventos + recordatorio)
- Documentación actualizada en M360 (`docs/ESTADO_PROYECTO.md`) y handoff creado

## 2026-06-27 — `ed924ef`
docs: agregar CHANGELOG.md con historial de cambios versionados

## 2026-06-27 — `4778b3a`
docs: actualizar NEXT_SESSION.md con Sprint 0-1 completados y API M360 pendiente

## 2026-06-27 — `0626740`
chore: excluir gtd_memento/ y saneada config.yaml

## 2026-06-27 — `7a2e355`
feat(release): completar Sprint 0 y Sprint 1 con saneamiento de seguridad

## 2026-06-27 — `b2fc124`
fix: correct client wrapper paths in memento_install

## 2026-06-27 — `4746eb1`
feat: complete dual architecture support for mementobloom package
