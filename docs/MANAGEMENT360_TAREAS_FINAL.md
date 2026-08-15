# Lista de tareas final — Management360

**Fuente:** handoffs, docs/, SESSION.md, SESSION_REPORT.md, code review 2026-08-14  
**Generado:** 2026-08-15  
**Memoria indexada:** 300 entries  
**Último manifiesto:** 2026-08-15T04:12:05

---

## Resumen ejecutivo

Management360 es un monolito Django que actúa como **gestor oficial de proyectos** de MementoBloom. Actualmente cuenta con:
- Migración ITCSS parcial completada (events, digitalizacion)
- Navegación espacial por celdas implementada (Room → Cell)
- Dashboard KPIs funcional con performance corregida (~0.5s)
- 15 hallazgos de code review pendientes (3 critical, 5 high, 7 medium)
- 9 tareas de digitalización pendientes
- 11 tareas de integración API/bridge pendientes
- 2 bloqueos activos sin resolución

---

## 1. Code review pendiente (2026-08-14)

> **Fuente:** HANDOFF_2026-08-14_sesion_kpis_dashboard_home_sidebar.md  
> **Estado:** Pendiente. No resuelto en handoffs posteriores.

| ID | Prioridad | Descripción | Archivo/location |
|----|-----------|-------------|------------------|
| M360-REVIEW-SEC-1 | critical | Agregar `@login_required` a vista `panel()` | `events/views/events_views.py:1055` |
| M360-REVIEW-SEC-2 | critical | Corregir permisos en vista `projects()` detalle de proyecto | `events/views/projects_views.py:562` |
| M360-REVIEW-SEC-3 | critical | Exigir POST y permisos en `project_activate()` | `events/views/projects_views.py:1014` |
| M360-REVIEW-PERF-1 | high | Anotar counts de tareas en proyectos y eliminar N+1 en `projects()` y `projects_table()` | `events/views/projects_views.py:71, 619, 682` |
| M360-REVIEW-PERF-2 | high | Mover filtros/sort de `events_table` a ORM y agregar paginación | `events/views/events_views.py:110` |
| M360-REVIEW-LOGIC-1 | high | Restaurar default `filtered_completed=True` o documentar cambio intencional | `events/views/events_views.py:491` |
| M360-REVIEW-LOGIC-2 | high | Corregir filtro host en `events_table` para incluir `assigned_to` | `events/views/events_views.py:136` |
| M360-REVIEW-LOGIC-3 | high | Corregir reverse URL en `dashboard_error.html` (`kpis:aht_dashboard` → `kpis:dashboard`) | `kpis/templates/kpis/dashboard_error.html:20,45` |
| M360-REVIEW-DEAD-1 | medium | Limpiar variable `active_events` no usada en `events_table()` | `events/views/events_views.py:113` |
| M360-REVIEW-DEAD-2 | medium | Eliminar import `transaction` no usado en `projects_views.py` | `events/views/projects_views.py:11` |
| M360-REVIEW-DEAD-3 | medium | Eliminar variables `tasks/completed_tasks_count/in_progress_tasks_count` no usadas en `projects_table()` | `events/views/projects_views.py:684-686` |
| M360-REVIEW-DUP-1 | medium | Extraer helper de filtros/search para `projects()` y `projects_table()` | `events/views/projects_views.py:600-611` y `669-679` |
| M360-REVIEW-DUP-2 | medium | Extraer helper de estadísticas por proyecto para `projects()` y `projects_table()` | `events/views/projects_views.py:619-624` y `682-686` |
| M360-REVIEW-DUP-3 | medium | Extraer patrón AJAX común de recarga de tablas en shared JS | `events/templates/events/events.html` y `events/templates/projects/projects.html` |

---

## 2. Verificación y operación

| ID | Descripción | Estado |
|----|-------------|--------|
| M360-EVENTS-VERIFY-CONSOLE | Verificar consola real de `/events/inbox/process/8/` post unificación | Pendiente |
| M360-Redis-Dev-Fix-2026-08-07 | Reiniciar runserver para confirmar ausencia de `FileBasedCache` tras cambio de Redis | Pendiente |

---

## 3. Digitalización / app `digitalizacion`

> **Fuente:** HANDOFF_2026-07-21_refactor_itcss_digitalizacion.md  
> **Estado:** Migración ITCSS parcial. Faltan ~25 templates.

| ID | Descripción | Estado |
|----|-------------|--------|
| DIGIT-OCR-2 | Ejecutar OCR Tesseract sobre los 9 documentos UPN del lote 1 | Pendiente |
| DIGIT-PDFA-1 | Completar PDF/A-2b estricto con validación veraPDF | Pendiente |
| DIGIT-META-1 | Completar MetadataService Dublin Core + PREMIS y validar microformatos JSON | Pendiente |
| DIGIT-FED-1 | Implementar FedatacionService para documentos con valor legal | Pendiente |
| DIGIT-ITCSS-1 | Completar migración ITCSS de templates restantes de digitalizacion (~25 templates) | Pendiente |
| DIGIT-SEC-1 | Validar acceso seguro PDFs en producción y verificar ausencia de paths locales expuestos | Pendiente |
| DIGIT-E2E-1 | Ejecutar suite de regresión Playwright end-to-end sobre pipeline digitalización completo | Pendiente |
| DIGIT-FAVICON-1 | Agregar favicon para eliminar 404 de `/favicon.ico` en M360 | Pendiente |
| DIGIT-DOCS-2 | Sincronizar documentación app digitalizacion M360 tras refactor ITCSS | Pendiente |

---

## 4. Integración M360 → MementoBloom

> **Fuente:** docs/FASE_3_INTEGRACION_M360.md, docs/FASE_3_M360_API_SPEC.md  
> **Estado:** Documentación aprobada. Sin implementación.

| ID | Descripción | Estado |
|----|-------------|--------|
| M360-1 | Implementar `/api/v1/health/` y `/api/v1/projects/` en M360 | Pendiente |
| M360-2 | Implementar endpoints de tareas (list, detail, status) | Pendiente |
| M360-3 | Implementar endpoints de eventos, recordatorios e inbox | Pendiente |
| M360-4 | Implementar `/api/v1/kanban/` | Pendiente |
| MB-1 | Evolucionar `tools/m360_bridge/client.py` para consumir `/api/v1/` | Pendiente |
| MB-2 | Actualizar `tools/sync_sprint.py` para leer estado real vía API | Pendiente |
| I1 | Implementar `m360_bridge.py` con autenticación y métodos CRUD básicos | Pendiente |
| I2 | Implementar `sync_sprint.py` que lee `SPRINT_N_PLAN.md` y dispara operaciones M360 | Pendiente |
| I3 | Agregar hook en `session_start.py` o comando `memento-sync` para ejecutar sync automáticamente | Pendiente |
| I4 | Implementar `pull_m360.py` para traer kanban/estados actualizados desde M360 | Pendiente |
| I5 | Agregar validación en `doctor.py` para verificar conectividad con M360 | Pendiente |

---

## 5. Sincronización de sprints

> **Fuente:** docs/CONTROL_GESTION_M360.md  
> **Estado:** SPRINT_0 completado. SPRINT_1-5 pendientes.

| ID | Descripción | Estado |
|----|-------------|--------|
| SPRINT_1 | Sincronizar SPRINT_1 en M360 | Pendiente |
| SPRINT_2 | Sincronizar SPRINT_2 en M360 | Pendiente |
| SPRINT_3 | Sincronizar SPRINT_3 en M360 | Pendiente |
| SPRINT_4 | Sincronizar SPRINT_4 en M360 | Pendiente |
| SPRINT_5 | Sincronizar SPRINT_5 en M360 | Pendiente |

---

## 6. Navegación espacial / celdas

> **Fuente:** HANDOFF_2026-08-11_migracion_room_a_cell.md, HANDOFF_2026-08-11_cierre_sesion.md  
> **Estado:** Migración completada. Quedan ajustes menores.

| ID | Descripción | Estado |
|----|-------------|--------|
| M360-ROOM-NAV-2026-08-10 | Navegación espacial por celdas: move_to_cell, navigate_to_cell, breadcrumb, room_map | Completado |
| M360-ROOM-MAP | `room_map.html` recibe `player=None` desde el include | Bloqueo activo |
| M360-CELL-TEMPLATES | Revisar templates HTML que aún usen `room.*` y actualizarlos a `cell.*` | Pendiente |

---

## 7. Bloqueos activos

| ID | Descripción | Impacto | Estado |
|----|-------------|---------|--------|
| B-M360 | API POST/PATCH requiere SQL directo por validación `Course.has no tutor`. Lectura OK con API key. | No se pueden crear/editar cursos/módulos/lecciones vía API REST. Workaround: SQL directo. | Activo |
| B-M360-ROOM-MAP | `room_map.html` recibe `player=None` desde el include, aunque `room_detail` pasa `player` en el contexto. | Mapa de navegación espacial no muestra posición del jugador ni breadcrumb. | Activo |

---

## 8. Completados recientes

| ID | Descripción | Fecha |
|----|-------------|-------|
| M360-FIX-ALERT-DISMISS-2026-08-15 | Fix botón alert-dismiss en tasks.html: eliminar handler inline onclick, confiar en listener delegado | 2026-08-15 |
| M360-LOBBY-ACTIONS-2026-08-11 | Navbar de acciones en lobby y secciones de universos/mundos/áreas | 2026-08-11 |
| M360-CELL-VIEWS-2026-08-11 | Vistas genéricas de celda: universe_list/create/detail/join, container_detail, item_detail, cell_detail redirect | 2026-08-11 |
| M360-ROOM-NAV-2026-08-10 | Navegación espacial por celdas: move_to_cell, navigate_to_cell, breadcrumb, room_map, migración 0004-0006 | 2026-08-11 |
| M360-ITCSS-Events-2026-07-25 | Migrar app events a ITCSS M360 | 2026-07-25 |
| M360-ITCSS-Reorganizacion-2026-07-27 | Reorganizar static/m360/css a convención ITCSS | 2026-07-27 |
| M360-IconTags-2026-07-27 | Crear templatetag icon_tags, migrar home/nav/header a inline SVGs | 2026-07-27 |
| M360-Schedules-Refactor-2026-07-25 | Refactor TaskSchedule: eliminar get_next_occurrences duplicado, agregar interval_days | 2026-07-25 |
| M360-UPN-Complementos-Curso-2026-07-25 | Crear curso M360 Complementos de Matemática desde sílabo UPN Ciclo 01 | 2026-07-25 |
| M360-UPN-Complementos-Proyecto-2026-07-25 | Crear proyecto M360 y corregir API para que cree Evento + ProjectState automáticamente | 2026-07-25 |
| M360-Admin-Reverse-Fix-2026-07-25 | Corregir reverse('admin:auth_user_change') por admin:accounts_user_change | 2026-07-25 |
| M360-ProcessInbox-Kanban-2026-08-07 | Unificar process inbox y kanban en main.js/main.css | 2026-08-07 |
| M360-Redis-Dev-Fix-2026-08-07 | Corregir Redis local Management360: apuntar .env a redis-11059:11059 con password desde vault | 2026-08-07 |
| M360-Sidebar-WidgetRail-2026-08-01 | Integrar widget rail en base_mock.html, agregar tooltips collapsed sidebar | 2026-08-01 |
| M360-MockupV2-2026-08-02 | Reemplazar estilos y scripts de base_mock.html por versión de mockupv2.html | 2026-08-02 |
| M360-BaseMockRefactor-2026-08-03 | Recrear base_mock.html desde mockupv2.html con estilos y scripts en archivos estáticos separados | 2026-08-03 |

---

## 9. Archivos HANDOFF reubicados

Se movieron los siguientes handoffs desde la raíz de Management360 a la estructura de mementobloom:

- `HANDOFF_2026-08-11_migracion_room_a_cell.md` → `projects/Management360/`
- `HANDOFF_2026-08-11_cierre_sesion.md` → `projects/Management360/`

**Motivo:** Centralizar toda la documentación de gestión de Management360 en `mementobloom/projects/Management360/` según la arquitectura de mementobloom.

---

## 10. Tareas generales pendientes (no exclusivas de M360)

| ID | Descripción | Estado |
|----|-------------|--------|
| T2.1 | Portabilidad `memento_install` (sed macOS/Linux) | Pendiente |
| T2.2 | Declarar dependencias mínimas en `requirements.txt` | Pendiente |
| T2.3 | Dockerfile + `docker-compose.yml` de referencia | Pendiente |
| T2.4 | Lockfiles y procedimiento de reproducible build | Pendiente |

---

## Próximos pasos recomendados

1. **Críticos primero:** resolver los 3 hallazgos critical de seguridad (login_required, permisos, POST obligatorio).
2. **Performance:** eliminar N+1 en proyectos/events, mover filtros a ORM, agregar paginación.
3. **Digitalización:** completar migración ITCSS restante (~25 templates).
4. **Integración API:** implementar `/api/v1/` y bridge M360.
5. **Sincronización:** ejecutar sync de SPRINT_1 a SPRINT_5.
6. **Bloqueos:** resolver B-M360 (API write) y B-M360-ROOM-MAP (player=None).
