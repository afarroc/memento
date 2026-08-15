# Tareas pendientes — Management360

**Fuente:** docs/CONTROL_GESTION_M360.md, docs/FASE_3_INTEGRACION_M360.md, docs/FASE_3_M360_API_SPEC.md, SESSION.md, SESSION_REPORT.md, handoffs  
**Generado:** 2026-08-15  
**Última actualización de estado:** 2026-08-15 (post fix alert-dismiss)

---

## 1. Code review pendiente (2026-08-14)

> **Estado:** Pendiente. No hay handoffs posteriores al 2026-08-14 que indiquen resolución. Siguen activos según SESSION.md y SESSION_REPORT.md.

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
| M360-EVENTS-VERIFY-CONSOLE | Verificar consola real de `/events/inbox/process/8/` post unificación | Pendiente. No resuelto en handoffs posteriores. |
| M360-Redis-Dev-Fix-2026-08-07 | Reiniciar runserver para confirmar ausencia de `FileBasedCache` tras cambio de Redis | Pendiente. HANDOFF 2026-08-07 indica que quedó como paso post-reinicio. |

---

## 3. Digitalización / app `digitalizacion`

| ID | Descripción | Estado |
|----|-------------|--------|
| DIGIT-OCR-2 | Ejecutar OCR Tesseract sobre los 9 documentos UPN del lote 1 | Pendiente. Sin handoffs de resolución. |
| DIGIT-PDFA-1 | Completar PDF/A-2b estricto con validación veraPDF | Pendiente. |
| DIGIT-META-1 | Completar MetadataService Dublin Core + PREMIS y validar microformatos JSON | Pendiente. |
| DIGIT-FED-1 | Implementar FedatacionService para documentos con valor legal | Pendiente. |
| DIGIT-ITCSS-1 | Completar migración ITCSS de templates restantes de digitalizacion (~25 templates) | Pendiente. HANDOFF 2026-07-21 indica migración parcial; faltan ~25 templates. |
| DIGIT-SEC-1 | Validar acceso seguro PDFs en producción y verificar ausencia de paths locales expuestos | Pendiente. |
| DIGIT-E2E-1 | Ejecutar suite de regresión Playwright end-to-end sobre pipeline digitalización completo | Pendiente. |
| DIGIT-FAVICON-1 | Agregar favicon para eliminar 404 de `/favicon.ico` en M360 | Pendiente. |
| DIGIT-DOCS-2 | Sincronizar documentación app digitalizacion M360 tras refactor ITCSS (`ARQUITECTURA.md`, `README.md`, `SYNC.md`) | Pendiente. |

---

## 4. Integración M360 → MementoBloom

| ID | Descripción | Estado |
|----|-------------|--------|
| M360-1 | Implementar `/api/v1/health/` y `/api/v1/projects/` en M360 | Pendiente. docs/FASE_3_M360_API_SPEC.md marca Sprint 2 como objetivo pendiente. |
| M360-2 | Implementar endpoints de tareas (list, detail, status) | Pendiente. |
| M360-3 | Implementar endpoints de eventos, recordatorios e inbox | Pendiente. |
| M360-4 | Implementar `/api/v1/kanban/` | Pendiente. |
| MB-1 | Evolucionar `tools/m360_bridge/client.py` para consumir `/api/v1/` | Pendiente. |
| MB-2 | Actualizar `tools/sync_sprint.py` para leer estado real vía API | Pendiente. |
| I1 | Implementar `m360_bridge.py` con autenticación y métodos CRUD básicos | Pendiente. docs/FASE_3_INTEGRACION_M360.md indica como próxima acción crear `tools/m360_bridge/`. |
| I2 | Implementar `sync_sprint.py` que lee `SPRINT_N_PLAN.md` y dispara operaciones M360 | Pendiente. |
| I3 | Agregar hook en `session_start.py` o comando `memento-sync` para ejecutar sync automáticamente | Pendiente. |
| I4 | Implementar `pull_m360.py` para traer kanban/estados actualizados desde M360 | Pendiente. |
| I5 | Agregar validación en `doctor.py` para verificar conectividad con M360 | Pendiente. |

---

## 5. Sincronización de sprints

| ID | Descripción | Estado |
|----|-------------|--------|
| SPRINT_1 | Sincronizar SPRINT_1 en M360 | Pendiente. CONTROL_GESTION_M360.md lo marca como pendiente. |
| SPRINT_2 | Sincronizar SPRINT_2 en M360 | Pendiente. |
| SPRINT_3 | Sincronizar SPRINT_3 en M360 | Pendiente. |
| SPRINT_4 | Sincronizar SPRINT_4 en M360 | Pendiente. |
| SPRINT_5 | Sincronizar SPRINT_5 en M360 | Pendiente. |

---

## 6. Bloqueos activos

| ID | Descripción | Impacto | Estado |
|----|-------------|---------|--------|
| B-M360 | API POST/PATCH requiere SQL directo por validación `Course.has no tutor`. Lectura OK con API key. | No se pueden crear/editar cursos/módulos/lecciones vía API REST. Workaround: SQL directo. | Activo. Sin handoffs de resolución. |
| B-M360-ROOM-MAP | `room_map.html` recibe `player=None` desde el include, aunque `room_detail` pasa `player` en el contexto. | Mapa de navegación espacial no muestra posición del jugador ni breadcrumb. | Activo. Sin handoffs de resolución. |

---

## 7. Tareas generales pendientes (no exclusivas de M360)

| ID | Descripción | Estado |
|----|-------------|--------|
| T2.1 | Portabilidad `memento_install` (sed macOS/Linux) | Pendiente en SESSION.md. |
| T2.2 | Declarar dependencias mínimas en `requirements.txt` | Pendiente. |
| T2.3 | Dockerfile + `docker-compose.yml` de referencia | Pendiente. |
| T2.4 | Lockfiles y procedimiento de reproducible build | Pendiente. |

---

## 8. Completados recientes

| ID | Descripción | Fecha |
|----|-------------|-------|
| M360-FIX-ALERT-DISMISS-2026-08-15 | Fix botón alert-dismiss en tasks.html: eliminar handler inline onclick, confiar en listener delegado | 2026-08-15 |
| M360-LOBBY-ACTIONS-2026-08-11 | Navbar de acciones en lobby y secciones de universos/mundos/áreas | 2026-08-11 |
| M360-CELL-VIEWS-2026-08-11 | Vistas genéricas de celda: universe_list/create/detail/join, container_detail, item_detail, cell_detail redirect | 2026-08-11 |
| M360-ROOM-NAV-2026-08-10 | Navegación espacial por celdas: move_to_cell, navigate_to_cell, breadcrumb, room_map, migración 0004-0006 | 2026-08-11 |
| M360-Redis-Dev-Fix-2026-08-07 | Corregir Redis local Management360: apuntar .env a redis-11059:11059 con password desde vault | 2026-08-07 |
| M360-ProcessInbox-Kanban-2026-08-07 | Unificar process inbox y kanban en main.js/main.css | 2026-08-07 |
| M360-ITCSS-Events-2026-07-25 | Migrar app events a ITCSS M360 | 2026-07-25 |
| M360-Admin-Reverse-Fix-2026-07-25 | Corregir reverse('admin:auth_user_change') por admin:accounts_user_change | 2026-07-25 |
| M360-UPN-Complementos-Proyecto-2026-07-25 | Crear proyecto M360 y corregir API para que cree Evento + ProjectState automáticamente | 2026-07-25 |
| M360-UPN-Complementos-Curso-2026-07-25 | Crear curso M360 Complementos de Matemática desde sílabo UPN Ciclo 01 | 2026-07-25 |
| M360-Schedules-Refactor-2026-07-25 | Refactor TaskSchedule: eliminar get_next_occurrences duplicado, agregar interval_days, implementar custom | 2026-07-25 |
| M360-ITCSS-Reorganizacion-2026-07-27 | Reorganizar static/m360/css a convención ITCSS | 2026-07-27 |
| M360-IconTags-2026-07-27 | Crear templatetag icon_tags, migrar home/nav/header a inline SVGs | 2026-07-27 |
| M360-BaseMockRefactor-2026-08-03 | Recrear base_mock.html desde mockupv2.html con estilos y scripts en archivos estáticos separados | 2026-08-03 |
| M360-MockupV2-2026-08-02 | Reemplazar estilos y scripts de base_mock.html y componentes mock por versión de mockupv2.html | 2026-08-02 |
| M360-Sidebar-WidgetRail-2026-08-01 | Integrar widget rail en base_mock.html, agregar tooltips collapsed sidebar | 2026-08-01 |

---

## Resumen de evaluación

- **Code review 2026-08-14:** 15 items pendientes (3 critical, 5 high, 7 medium). Ninguno resuelto en handoffs posteriores.
- **Digitalización:** 9 items pendientes. Último progreso registrado en HANDOFF_2026-07-21 (migración ITCSS parcial).
- **Integración API/bridge:** 11 items pendientes. Documentación aprobada pero sin implementación.
- **Sincronización sprints:** 5 sprints pendientes de sincronizar.
- **Bloqueos activos:** 2 sin resolución registrada.
- **Tareas generales:** 4 pendientes de Fase 2.
