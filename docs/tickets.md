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
- `projects/mementobloom/HANDOFF_2026-08-16_tickets_servicio.md`
- `docs/CONTEXT_TREE.md` sección 9.
