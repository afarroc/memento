# Sistema de tickets de servicio — mementobloom

## 1. Objetivo
Los tickets son el **punto de entrada formal** al trabajo de mementobloom. Cada ticket representa una unidad de trabajo gestionada por el asistente de turno, con trazabilidad opcional hacia objetos de Management360.

## 2. Modelo
Archivo: `core/tickets.py`

Campos principales:
- `id`: identificador único `TICK-XXXX`.
- `title`: título del ticket.
- `description`: detalle del ticket.
- `status`: `open`, `in_progress`, `resolved`, `closed`.
- `priority`: `low`, `medium`, `high`, `critical`.
- `created_at`, `updated_at`: timestamps.
- `created_by`: quién creó el ticket.
- `assigned_to`: asistente o rol asignado.
- `tags`: etiquetas libres.
- `source`: `manual`, `assistant`, `bridge`.
- `m360_links`: vínculos a objetos M360.
- `context`: metadata de sesión o contexto adicional.
- `resolution`: texto de cierre/resolución.

## 3. Storage
- Primario: `.memento_runtime/tickets.json`.
- Cache opcional: Redis key `memento_tickets`.

## 4. Panel web
Rutas en `panel_server.py`:
- `GET /tickets`: listado.
- `GET /tickets/new`: formulario de creación.
- `GET /tickets/<id>`: detalle.
- `GET /api/tickets`: listado JSON.
- `POST /api/tickets`: crear ticket.
- `GET/PUT/DELETE /api/tickets/<id>`: leer/actualizar/eliminar.
- `POST /api/tickets/<id>/close`: cerrar ticket.
- `POST /api/tickets/<id>/resolve`: marcar como resuelto.
- `POST /api/tickets/<id>/link-m360`: vincular objetos M360.
- `GET /api/tickets/stats`: estadísticas.

## 5. CLI
Archivo: `tools/ticket.py`

Comandos:
- `create`
- `update`
- `show`
- `delete`
- `list`
- `stats`
- `resolve`
- `close`
- `link-m360`

## 6. Bridge M360
Helpers en `tools/m360_bridge/client.py`:
- `m360_link_ticket(...)`: vincula proyecto/tarea/evento/recordatorio/inbox a un ticket.
- `m360_create_ticket_from_task(...)`: crea un ticket desde una tarea M360.
- `m360_sync_tickets_for_project(...)`: sincroniza tickets para un proyecto M360.

## 7. Flujo recomendado
1. Sesión iniciada con `python3 tools/bootstrap_context.py --print`.
2. Si corresponde, crear ticket de sesión con `tools/ticket.py create`.
3. Gestionar ticket desde panel `/tickets` o CLI.
4. Vincular a objetos M360 con `/api/tickets/<id>/link-m360` o `tools/ticket.py link-m360`.
5. Al cerrar sesión, actualizar estados y registrar handoff.

## 8. Referencias
- `core/tickets.py`
- `panel_server.py`
- `tools/ticket.py`
- `tools/m360_bridge/client.py`
- `projects/mementobloom/HANDOFF_2026-08-31_actualizacion_contexto_documentacion.md`
- `projects/mementobloom/HANDOFF_2026-09-08_m360_daphne_timeout_fix.md`
- `projects/mementobloom/HANDOFF_2026-09-10_tickets_crm_normalizacion.md`
- `projects/mementobloom/HANDOFF_2026-09-10_cierre_TICK-0090.md`
- `docs/CONTEXT_TREE.md` sección 10.

## 9. Estado actual (2026-09-25)
- Tickets abiertos relevantes: TICK-0053 (Management360 bitácora).
- Tickets cerrados/recientes: TICK-0091 (revisión `/digitalizacion` completada), TICK-0092 (`DIGIT-LLM-001` asistente LLM digitalizacion), TICK-0093 (gestión digitalización M360).
- TICK-0091: revisar estilos y funciones de la vista `/digitalizacion` en M360. Completado.
- TICK-0092: `DIGIT-LLM-001` implementado. Backend `llm_service.py` contra POCO `192.168.18.59:18080`. Template `asistente_documento.html`. Botón Asistente en dashboard. Tarea M360 387 creada.
- TICK-0093: gestión general digitalización M360. Completado.
- Management360 commits recientes (2026-09-25): 13 commits locales en `main`, working tree limpio.
  - `61d82616` pipeline checksum fix
  - `5159eab5` quality/certification templates
  - `c6e4cec5` preparation/reception/navigation layouts
  - `3dc922e3` OCR/PDF/A, LLM, websocket
  - `38e78139` cv refactor
  - `d5fc9886` api v1 extension
  - `61ee906a` panel update
  - `111db3e8` global styles
  - `b97dab01` vision module
  - `5c4c61ed` infra/docs
  - `d643d7a5` accounts login unify
  - `f92c62e7` bitacora crispy forms removal
  - `7e40e075` digitalizacion README
- **METADATOS-OCR-FIX (2026-09-24)**: Tarea M360 #399 creada y completada. Fix crítico en `metadatos.html`: `updatePreview()` se ejecutaba después de `updateMicroformatPanel()` y sobrescribía el `structuredContent` con OCR del servidor con datos del formulario (sin OCR). Solución: condicionar `updatePreview()` solo cuando NO hay `structured_content` del servidor. Validado con Selenium (ALL TESTS PASSED): microformatPreview muestra structuredContent con 1 página, 1967 chars OCR, confidence 0.83.
