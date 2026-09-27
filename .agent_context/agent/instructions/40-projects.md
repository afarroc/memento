# 40 Proyectos activos

No hay prioridades fijas en este archivo.

## Regla operativa
- Lee `.agent_context/secure/USER_CONTEXT.md` para prioridades contextuales del usuario; no lo vuelvas a pedir.
- Si no hay contexto de usuario, prioriza el proyecto activo detectado desde el directorio de trabajo o desde `USER_CONTEXT.md`.
- Para proyectos distintos al activo, usa sus HANDOFF recientes solo cuando el usuario o el contexto lo indiquen.
- No asumas que servicios remotos están activos; verifica antes de operar.

## Nomenclatura M360 por proyecto

Al crear o actualizar tareas/eventos/recordatorios en M360 via `tools/m360_bridge/client.py`, aplicar el prefijo documentado del proyecto:

| Proyecto | Prefijo(s) | Documento oficial |
|----------|------------|-------------------|
| `Management360` | `M360-*`, `DIGIT-*`, `CV-REVIEW-*`, `TASK-BITACORA-*` | `projects/Management360/docs/guides/nomenclatura.md` |
| `TaxiLima2026` | `TAXI-*` | `projects/TaxiLima2026/handoffs/HANDOFF_2026-08-16_nomenclatura_tareas.md` |
| `Carpinteria` | `CARP-*` | `projects/Carpinteria/docs/nomenclatura_tareas.md` |
| `perfil_personal` | `PERFIL-*` | `projects/perfil_personal/docs/nomenclatura_tareas.md` |
| `poco_xiaomi` | `POCO-*` | `projects/poco_xiaomi/docs/nomenclatura_tareas.md` |
| Otros clientes | — | Sin prefijo documentado; usar título descriptivo real |

Reglas:
- Si el proyecto tiene documento de nomenclatura, el título del item en M360 DEBE comenzar con el prefijo documentado.
- Si no existe documento de nomenclatura, NO inventar prefijos; usar el título descriptivo real del trabajo.
- Al crear tickets mementobloom, reflejar el mismo título/código usado en M360 para mantener trazabilidad.
