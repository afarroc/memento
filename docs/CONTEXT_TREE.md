# Convención Context Tree de memento

El `memory/graph/memory_index.json` se organiza como un **Context Tree jerárquico** (Domain > Tema > Entry), inspirado en ByteRover (arxiv 2604.01599) y GAM (ACL 2026). Cada entry es un nodo hoja con relaciones y provenance.

## 1. Dominios (Domain = campo `project`)
Cada entrada pertenece a un dominio. Dominios actuales:

| Dominio | Significado |
|---------|-------------|
| `mementobloom` | El proyecto memento en sí (agente, tools, infra) |
| `m360` | Cliente M360 (Management360, trabajo directo sobre su repo) |
| `Management360` | Gestión de proyectos M360 (vía bridge API) |
| `Administracion_UPN` | Proyecto UPN (sílabos, cursos, digitalización) |
| `jewelry_catalog` | Cliente jewelry_catalog |
| `Ventas_Porta` | Cliente Ventas_Porta |
| `Carpinteria` | Cliente Carpinteria (carpintería/bricolaje digital) |
| `docs` | Documentación permanente del proyecto mementobloom |
| `analyst` | Análisis / investigación |
| `adherence_test` | Proyecto de prueba |
| `tickets` | Tickets de servicio de mementobloom |

## 2. Temas (Tema = campo `type` + `tags`)
Dentro de un dominio, las entries se agrupan por tipo y etiquetas:

- `type`: HANDOFF, CONTEXT, SOURCE, COMPONENT, NOTE, COMMIT, handoff.
- `tags`: palabras clave (ej. `silabo`, `curso`, `itcss`, `termux`, `vault`, `ssh`).

## 3. Entry (hoja)
Cada nodo hoja tiene: `id`, `type`, `project` (Domain), `ts`, `path`, `summary`, `tags`, `score`, `external`. El `path` es la fuente (handoff/doc/git) — es el *provenance*.

## 4. Relaciones
Las relaciones entre entries se expresan vía `tags` compartidos y referencias en `summary`. Para relaciones cruzadas explícitas se usa la convención `@dominio/tema/entry` en `tags` o notas.

## 5. Ambient awareness (sin volcar contenido)
Para dar al agente conciencia de qué existe sin saturar contexto, usar:
```bash
python3 tools/memory_tree.py          # árbol Domain > Tema > nº entries
python3 tools/memory_tree.py --domain Administracion_UPN   # temas de un dominio
```
Esto lista la estructura (nombres + conteos), no el contenido de las entries.

## 6. Regla de curación
Toda nueva memoria se indexa con `python3 tools/quick_scan.py <HANDOFF>` y queda como entry bajo su Domain/Tema. Al cerrar sesión se consolida (ver `00-core.md` y `docs/ARQUITECTURA_AGENTE_2026.md` §6).

## 7. Documentación por proyecto
- `docs/` → documentación permanente de **mementobloom**.
- `projects/Management360/docs/` → documentación del cliente Management360.
- `projects/TaxiLima2026/docs/` → documentación del cliente TaxiLima2026.
- `projects/Administracion_UPN/docs/` → documentación del cliente Administracion_UPN.
- En general: `projects/<cliente>/docs/` es la ruta de documentación específica de cada proyecto cliente.

## 8. Actualización de estructura de clientes
- La migración de estructura se realiza con `python3 tools/register_client.py --migrate-all`.
- Es conservadora: agrega directorios y archivos faltantes, no borra contenido existente.
- `PROJECT_CONTEXT.md` solo se actualiza si falta o con `--force` explícito.
- La memoria indexada y los handoffs no se tocan durante la migración.
- El dominio de memoria por cliente se define en `PROJECT_CONTEXT.md` y se respeta en el Context Tree.

## 8. Regla de `description` / detalle en M360
- En Management360, `description` es el campo de detalle de proyectos, tareas, eventos, inbox, cursos, módulos, lecciones, evaluaciones y bibliografía.
- Todo item creado o modificado por `tools/m360_bridge/client.py` debe incluir `description` con contenido real.
- Si falta detalle completo, usar al menos: fuente + criterio + nota de completado posterior.
- Correcciones históricas: actualizar `description` antes de cambiar estados o cerrar items.
- Referencia: `projects/Management360/docs/guides/bridge-usage.md` sección 5.

## 9. Sistema de tickets de servicio
- Dominio de memoria: `tickets`.
- Storage primario: `.memento_runtime/tickets.json`.
- Storage opcional: Redis key `memento_tickets`.
- Modelo: `core/tickets.py` con `Ticket` y `M360Link`.
- Panel: `panel_server.py` expone `/tickets`, `/tickets/new`, `/tickets/<id>`, `/api/tickets`, `/api/tickets/<id>/close`, `/api/tickets/<id>/resolve`, `/api/tickets/<id>/link-m360`, `/api/tickets/stats`.
- CLI: `tools/ticket.py` con comandos `create`, `update`, `show`, `delete`, `list`, `stats`, `resolve`, `close`, `link-m360`.
- Bridge M360: `tools/m360_bridge/client.py` incluye helpers `m360_link_ticket(...)`, `m360_create_ticket_from_task(...)`, `m360_sync_tickets_for_project(...)`.
- Regla: todo ticket debe poder vincularse a objetos M360: `project_id`, `task_id`, `event_id`, `reminder_id`, `inbox_item_id`.
- Handoff referencia: `projects/mementobloom/HANDOFF_2026-08-16_tickets_servicio.md`.
