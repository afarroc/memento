# Mapeo de reemplazo Bootstrap → ITCSS M360 — App Events

**Proyecto:** Management360 / events  
**Objetivo:** eliminar Bootstrap CSS, Bootstrap JS, NiceAdmin y dependencias no-MIT de la app `events` migrando a ITCSS M360.  
**Estado:** Paso 1 completado — base ITCSS creada + auditoría de clases Bootstrap.

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Templates en `events/` | 84 |
| Clases Bootstrap únicas encontradas | **327** |
| Atributos `style=""` inline | 96 |
| Bloques `<style>` en templates | 32 |
| Usos de Bootstrap JS (`data-bs-*`, `bootstrap.*`) | 48 total en M360; concentrados en events, panel, core |
| Librerías vendor no-MIT en M360 | TinyMCE (GPL), Boxicons (sin licencia), RemixIcon (Apache 2.0) |

**Conclusión:** La migración es viable pero no trivial. Se recomienda migración por fases por template, empezando por los más aislados (schedules, reminders) y terminando por los más integrados (inbox, kanban, event_create).

---

## 2. Arquitectura objetivo

```
events/templates/events/base_itcss.html  → nueva base sin Bootstrap
events/templates/events/components/_site_header.html  → header ITCSS
events/templates/events/components/_site_footer.html  → footer ITCSS
static/m360/css/_index.css               → design system existente
static/m360/css/sections/_events.css      → nuevo: estilos específicos de events
static/m360/css/components/_events-*.css  → nuevos: componentes específicos
```

**Reglas:**
- Cero `bootstrap.min.css`, `bootstrap.bundle.min.js`, `style.css` (NiceAdmin), `main.js` (NiceAdmin).
- Cero clases Bootstrap en templates de events.
- Cero `data-bs-toggle/target/dismiss` en templates de events.
- Todo JS necesario se escribe en vanilla JS o se reutiliza `events/js/*.js` refactorizado.
- Tokens M360 con prefijo `--m360-*` y clases con prefijo `m360-`.

---

## 3. Mapa de reemplazo por categoría

### 3.1 Layout (`row`, `col-*`, `container-fluid`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `container-fluid` | `m360-container` o wrapper nativo | `m360-container` ya existe en `_grid.css` |
| `row` | `m360-row` | Flex wrap con gap |
| `col-12`, `col-md-6`, `col-lg-3`, `col-xl-4` | `m360-col` + media queries | M360 usa flex/grid nativo; para columnas específicas usar `m360-grid-2/3` o CSS custom en `_events.css` |
| `g-2`, `g-3`, `gx-*`, `gy-*` | `gap: var(--m360-space-*)` en el contenedor | Los gaps de Bootstrap son 4-step; mapear a tokens M360 |
| `mb-4`, `mt-3`, `p-3`, `px-4`, `py-2` | `m360-space-*` / custom padding | M360 tiene escala 4px base; algunos valores necesitan CSS custom |
| `justify-content-between` | `justify-content: space-between` | Helper nativo; agregar a `_events.css` si se repite |
| `align-items-center` | `align-items: center` | Helper nativo |
| `flex-wrap` | `flex-wrap: wrap` | Helper nativo |
| `d-flex` | `display: flex` | Helper nativo; o agregar `.m360-d-flex` |
| `w-100` | `width: 100%` | Helper nativo |
| `text-center` | `text-align: center` | Helper nativo |

**Componentes nuevos necesarios en `_events.css`:**
- `.events-col-12`, `.events-col-md-6`, `.events-col-lg-3`, `.events-col-xl-4` — grid responsive específico de events.

### 3.2 Cards (`card`, `card-header`, `card-body`, `card-footer`, `card-title`, `card-text`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `card` | `m360-card` | Ya existe en `_cards.css` |
| `card-header` | `m360-card-header` | Con `background` por inline style → mover a clases semánticas |
| `card-body` | `m360-card-body` | |
| `card-footer` | `m360-card-footer` | Necesita crearse en `_cards.css` |
| `card-title` | `m360-card-title` | Necesita crearse en `_cards.css` |
| `card-text` | `m360-card-text` | Necesita crearse en `_cards.css` |
| `shadow-sm` | `box-shadow: var(--m360-shadow-sm)` | Ya en tokens |
| `border-0` | `border: none` | |
| `border-left-*` | `border-left: 3px solid var(--m360-color-*)` | Crear `.m360-border-left-primary/success/warning` |
| `h-100` | `height: 100%` | Helper nativo |

**Componentes nuevos necesarios:**
- `.m360-card-footer` — padding/fondo gris claro/borde superior.
- `.m360-card-title` — tamaño/peso tipográfico.
- `.m360-card-text` — color secundario.

### 3.3 Botones (`btn`, `btn-group`, `btn-close`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `btn` | `m360-btn` | |
| `btn-primary` | `m360-btn-primary` | |
| `btn-success` | `m360-btn-success` | |
| `btn-warning` | `m360-btn-warning` | |
| `btn-danger` | `m360-btn-danger` | |
| `btn-secondary` | `m360-btn-outline-secondary` | M360 no tiene `btn-secondary` sólido aún; agregar o mapear |
| `btn-outline-primary` | `m360-btn-outline-primary` | **Falta** en M360; agregar |
| `btn-outline-success` | `m360-btn-outline-success` | **Falta** en M360; agregar |
| `btn-outline-warning` | `m360-btn-outline-warning` | **Falta** en M360; agregar |
| `btn-outline-danger` | `m360-btn-outline-danger` | **Falta** en M360; agregar |
| `btn-outline-info` | `m360-btn-outline-info` | **Falta** en M360; agregar |
| `btn-outline-secondary` | `m360-btn-outline-secondary` | Existe |
| `btn-sm` | `m360-btn-sm` | |
| `btn-lg` | `m360-btn-lg` | **Falta** en M360; agregar |
| `btn-light` | custom class | **Falta** en M360; agregar |
| `btn-group` | `m360-btn-group` | **Falta** en M360; agregar (flex + gap) |
| `btn-close` | `m360-close-modal` | Ya existe en `_modal.css` |
| `dropdown-toggle` | ver sección dropdowns | |

**Componentes nuevos necesarios en `_buttons.css`:**
- `.m360-btn-outline-primary/success/warning/danger/info`
- `.m360-btn-lg`
- `.m360-btn-light`
- `.m360-btn-group`

### 3.4 Alertas (`alert`, `alert-dismissible`, `alert-heading`, `btn-close`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `alert` | `m360-alert` | |
| `alert-info` | `m360-alert-info` | |
| `alert-success` | `m360-alert-success` | |
| `alert-warning` | `m360-alert-warning` | |
| `alert-danger` | `m360-alert-danger` | |
| `alert-dismissible` | nativo | M360 no implementa dismiss automático; se hace con JS custom |
| `alert-heading` | nativo | Tipografía custom en `_events.css` |
| `btn-close` | `m360-close-modal` | |

**Nota:** El `base.html` actual usa `data-bs-dismiss="alert"` y auto-dismiss con JS. En ITCSS, se implementa en `base_itcss.html` con vanilla JS.

### 3.5 Modales (`modal`, `modal-dialog`, `modal-content`, `modal-header`, `modal-body`, `modal-footer`, `modal-title`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `modal fade` | `m360-modal` | Ya existe en `_modal.css` |
| `modal-dialog` | implícito en `m360-modal-content` | |
| `modal-content` | `m360-modal-content` | |
| `modal-header` | `m360-modal-header` | |
| `modal-body` | `m360-modal-body` | |
| `modal-footer` | `m360-modal-footer` | |
| `modal-title` | nativo | Tipografía en `_events.css` |
| `data-bs-toggle="modal"` | `data-m360-open="modal-id"` | Requiere JS custom |
| `data-bs-target="#modalId"` | `data-m360-open="modalId"` | |
| `data-bs-dismiss="modal"` | `data-m360-close="modal"` | |

**JS necesario:** `m360-modal.js` vanilla para abrir/cerrar modales con `data-m360-open` y `data-m360-close`. Ya hay estructura CSS lista.

### 3.6 Dropdowns (`dropdown`, `dropdown-toggle`, `dropdown-menu`, `dropdown-item`, `dropdown-divider`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `dropdown` | `m360-dropdown` | |
| `dropdown-toggle` | nativo | Botón con `data-m360-toggle="dropdown"` |
| `dropdown-menu` | `m360-dropdown-menu` | |
| `dropdown-item` | `m360-dropdown-item` | |
| `dropdown-divider` | `m360-dropdown-sep` | |
| `data-bs-toggle="dropdown"` | `data-m360-toggle="dropdown"` | JS custom requerido |

**JS necesario:** `m360-dropdown.js` vanilla para toggle de dropdowns.

### 3.7 Navegación (`nav`, `nav-tabs`, `tab-content`, `tab-pane`, `breadcrumb`, `breadcrumb-item`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `nav` | nativo | Layout flex en `_events.css` |
| `nav-tabs` | `m360-tabs` | |
| `nav-link` | `m360-tab` | |
| `tab-content` | wrapper nativo | |
| `tab-pane` | `m360-tab-pane` | |
| `breadcrumb` | nativo | Layout flex |
| `breadcrumb-item` | nativo | |
| `active` | `m360-active` | |

### 3.8 Formularios (`form-control`, `form-select`, `form-check`, `form-check-input`, `form-check-label`, `form-label`, `form-text`, `input-group`, `input-group-text`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `form-control` | `m360-form-control` | |
| `form-select` | `m360-form-control` (select) | |
| `form-label` | `m360-form-label` | |
| `form-text` | `m360-form-hint` | |
| `form-check` | `m360-form-check` | |
| `form-check-input` | `m360-form-check-input` | |
| `form-check-label` | `m360-form-check-label` | |
| `input-group` | nativo | Flex wrapper en `_events.css` |
| `input-group-text` | nativo | |
| `mb-3` | `m360-space-4` | |
| `form-floating` | nativo | No hay equivalente directo; usar label posicionado |

### 3.9 Tablas (`table`, `table-responsive`, `table-hover`, `table-borderless`, `table-sm`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `table-responsive` | `m360-table-responsive` | |
| `table` | `m360-table` | |
| `table-hover` | `m360-table tbody tr:hover td` | Ya en `_tables.css` |
| `table-borderless` | `m360-table` sin borde | Clase custom |
| `table-sm` | `m360-table-sm` | |

### 3.10 Badges (`badge`, `badge-pill`, `bg-*`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `badge` | `m360-badge` | |
| `badge bg-primary` | `m360-badge-info` | |
| `badge bg-success` | `m360-badge-success` | |
| `badge bg-warning` | `m360-badge-warning` | |
| `badge bg-danger` | `m360-badge-danger` | |
| `badge bg-info` | `m360-badge-info` | |
| `badge bg-secondary` | custom | Necesita variante gris |
| `badge bg-light text-dark` | `m360-badge` custom | |
| `badge-pill` | implícito | `m360-badge-radius` ya es pill |

### 3.11 Progress (`progress`, `progress-bar`)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `progress` | `m360-progress` | |
| `progress-bar` | `m360-progress-fill` | |
| `style="width: X%"` | `style="width: X%"` | Se mantiene inline por ser dinámico |

### 3.12 Utilidades (helpers)

| Bootstrap | Reemplazo M360 | Notas |
|---|---|---|
| `d-flex` | `m360-d-flex` (nuevo) | O usar helper nativo |
| `justify-content-between` | `m360-justify-between` (nuevo) | |
| `justify-content-end` | `m360-justify-end` (nuevo) | |
| `justify-content-center` | `m360-justify-center` (nuevo) | |
| `align-items-center` | `m360-align-center` (nuevo) | |
| `align-items-start` | `m360-align-start` (nuevo) | |
| `align-self-center` | `m360-self-center` (nuevo) | |
| `flex-wrap` | `m360-flex-wrap` (nuevo) | |
| `flex-column` | `m360-flex-col` (nuevo) | |
| `flex-grow-1` | `m360-flex-grow` (nuevo) | |
| `gap-2` | `gap: var(--m360-space-2)` | |
| `gap-3` | `gap: var(--m360-space-3)` | |
| `text-center` | `m360-text-center` (nuevo) | |
| `text-start` | `m360-text-start` (nuevo) | |
| `text-end` | `m360-text-end` (nuevo) | |
| `text-muted` | `m360-text-muted` | |
| `text-primary` | `m360-text-primary` (nuevo) | |
| `text-success` | `m360-text-success` (nuevo) | |
| `text-warning` | `m360-text-warning` (nuevo) | |
| `text-danger` | `m360-text-danger` (nuevo) | |
| `text-info` | `m360-text-info` (nuevo) | |
| `fw-bold` | `m360-fw-bold` (nuevo) | |
| `fs-4` | `m360-text-xl` | |
| `fs-5` | `m360-text-lg` | |
| `mb-0` | `m360-mb-0` (nuevo) | |
| `mb-1` | `m360-mb-1` (nuevo) | |
| `mb-2` | `m360-mb-2` (nuevo) | |
| `mb-3` | `m360-mb-3` (nuevo) | |
| `mb-4` | `m360-mb-4` (nuevo) | |
| `mt-2` | `m360-mt-2` (nuevo) | |
| `mt-3` | `m360-mt-3` (nuevo) | |
| `mt-4` | `m360-mt-4` (nuevo) | |
| `p-2` | `m360-p-2` (nuevo) | |
| `p-3` | `m360-p-3` (nuevo) | |
| `p-4` | `m360-p-4` (nuevo) | |
| `p-5` | `m360-p-5` (nuevo) | |
| `pt-3` | `m360-pt-3` (nuevo) | |
| `pb-3` | `m360-pb-3` (nuevo) | |
| `px-2` | `m360-px-2` (nuevo) | |
| `py-1` | `m360-py-1` (nuevo) | |
| `w-100` | `m360-w-100` (nuevo) | |
| `h-100` | `m360-h-100` (nuevo) | |
| `shadow-sm` | `m360-shadow-sm` | |
| `border` | `m360-border` (nuevo) | |
| `border-top` | `m360-border-top` (nuevo) | |
| `border-start` | `m360-border-start` (nuevo) | |
| `rounded` | `m360-rounded` (nuevo) | |
| `rounded-circle` | `m360-rounded-circle` (nuevo) | |
| `opacity-75` | `m360-opacity-75` (nuevo) | |
| `visible` | nativo | |
| `invisible` | nativo | |
| `display-1` | `m360-display-1` (nuevo) | |
| `small` | `m360-text-sm` | |
| `sr-only` | nativo | |

**Recomendación:** Crear archivo `static/m360/css/utilities/_events-utilities.css` con las utilities más usadas en events, o expandir `_helpers.css` existente.

---

## 4. Reemplazo de JavaScript Bootstrap

| Característica Bootstrap | Reemplazo M360 | Implementación |
|---|---|---|
| `bootstrap.Modal` | `m360-modal.js` vanilla | Ya hay CSS; falta JS para `data-m360-open` / `data-m360-close` |
| `bootstrap.Dropdown` | `m360-dropdown.js` vanilla | Ya hay CSS; falta JS para `data-m360-toggle` |
| `bootstrap.Toast` | `m360-toast.js` vanilla | Ya hay CSS en `_notifications.css` |
| `bootstrap.Tooltip` | `data-m360-tooltip` (CSS) | Ya implementado en `_tooltip.css` |
| `bootstrap.Tab` | `m360-tabs` (CSS) + JS custom | Tabs nativos en `_tabs.css` |
| `data-bs-dismiss="alert"` | vanilla JS en `base_itcss.html` | Auto-dismiss + botón cerrar |
| `data-bs-toggle="modal"` | `data-m360-open="modalId"` | |
| `data-bs-target="#modalId"` | integrado en `data-m360-open` | |
| `data-bs-dismiss="modal"` | `data-m360-close="modal"` | |
| `data-bs-toggle="dropdown"` | `data-m360-toggle="dropdown"` | |

**JS existente en events que NO depende de Bootstrap:**
- `events/js/inbox.js` — lógica GTD, filtros, captura rápida.
- `events/js/components.js` — componentes específicos.
- `events/js/task-panel.js` — panel de tareas.

**JS que SÍ usa Bootstrap y debe reescribirse:**
- `events/js/process_inbox_item.js` — verificar usos de `bootstrap.Modal`.
- Templates con `data-bs-toggle="modal"` (inbox, kanban, event_create, task_schedules, etc.).
- Templates con `data-bs-toggle="dropdown"` (task_schedules).
- Templates con `data-bs-dismiss="alert"` (base.html, event_create).

---

## 5. Estrategia de migración por template

Orden recomendado (de menor a mayor acoplamiento):

### Fase A — Templates aislados (sin modales/dropdowns complejos)
1. `task_schedule_detail.html`
2. `task_schedule_preview.html`
3. `delete_task_schedule.html`
4. `delete_reminder.html`
5. `delete_project_template.html`
6. `edit_reminder.html`
7. `create_reminder.html`
8. `task_dependencies_list.html`
9. `task_dependencies.html`
10. `create_task_dependency.html`
11. `delete_task_dependency.html`
12. `task_dependency_graph.html`
13. `event_history.html`
14. `event_detail.html`
15. `event_assign.html`

### Fase B — Templates con modales/dropdowns simples
16. `reminders_dashboard.html` — modales inline
17. `schedule_admin_dashboard.html`
18. `user_schedules_panel.html`
19. `task_schedule_preview.html`
20. `event_list.html`
21. `event_edit.html`
22. `project_templates.html`
23. `project_template_detail.html`

### Fase C — Templates complejos (kanban, inbox, event_create)
24. `task_schedules.html` — dropdown + modales
25. `event_create.html` — modales + validación JS
26. `kanban.html` — modales + tema + drag & drop
27. `inbox.html` — modales + IA assistant
28. `kanban_enhanced.html`
29. `kanban_board.html`
30. `kanban_board_modern.html`
31. `unified_dashboard.html`
32. `inbox_panel.html`
33. `inbox_management_panel.html`
34. `inbox_mailbox.html`
35. `inbox_link_checker.html`
36. `inbox_item_detail_admin.html`
37. `inbox_admin_dashboard.html`
38. `process_inbox_item.html`
39. `eisenhower_matrix.html`
40. `event_panel.html`
41. `events.html`
42. `task_programs_calendar.html`
43. `edit_task_schedule.html`
44. `edit_task_schedule_enhanced.html`
45. `create_task_schedule.html`
46. `generate_schedule_occurrences.html`
47. `root.html`
48. `message_container.html`
49. `control/frame.html`
50. `control/control.html`

---

## 6. Nuevos componentes CSS necesarios

Agregar a `static/m360/css/`:

### `components/_cards.css` (extender)
- `.m360-card-footer`
- `.m360-card-title`
- `.m360-card-text`

### `components/_buttons.css` (extender)
- `.m360-btn-outline-primary`
- `.m360-btn-outline-success`
- `.m360-btn-outline-warning`
- `.m360-btn-outline-danger`
- `.m360-btn-outline-info`
- `.m360-btn-lg`
- `.m360-btn-light`
- `.m360-btn-group`

### `components/_badges.css` (extender)
- `.m360-badge-secondary` (gris)

### `sections/_events.css` (nuevo)
- Grid responsive específico: `.events-col-12`, `.events-col-md-6`, `.events-col-lg-3`, `.events-col-xl-4`
- Utilities events: `.events-d-flex`, `.events-justify-between`, `.events-text-center`, `.events-mb-0/1/2/3/4`, `.events-mt-2/3/4`, `.events-p-2/3/4/5`, `.events-pt-3`, `.events-pb-3`, `.events-px-2`, `.events-py-1`, `.events-w-100`, `.events-h-100`, `.events-border-top`, `.events-border-start`, `.events-rounded`, `.events-rounded-circle`, `.events-opacity-75`, `.events-display-1`, `.events-fw-bold`, `.events-text-primary/success/warning/danger/info/muted`
- Variantes de card con bordes izquierdos: `.events-border-left-primary/success/warning/danger/secondary`
- Estilos específicos de inbox, kanban, schedules que no caben en componentes genéricos.

### `utilities/_helpers.css` (extender)
- Agregar utilities de flex, spacing, text si se vuelven globales.

---

## 7. Checklist de migración por template

Para cada template:
1. Cambiar `{% extends 'layouts/base.html' %}` por `{% extends 'events/base_itcss.html' %}`.
2. Reemplazar clases Bootstrap por clases M360 o utilities custom.
3. Eliminar bloques `<style>` y mover estilos a `_events.css` o componentes M360.
4. Eliminar atributos `style=""` reemplazándolos por clases semánticas.
5. Reemplazar `data-bs-toggle/target/dismiss` por atributos M360.
6. Actualizar `extra_css` y `extra_js` blocks.
7. Verificar visualmente en dev server.

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Regresión visual total | Migrar template por template, verificar en dev antes de continuar |
| JS roto (modales, dropdowns) | Implementar `m360-modal.js` y `m360-dropdown.js` antes de migrar templates que los usen |
| Colisión de tokens | Usar exclusivamente tokens `--m360-*`; eliminar `:root` custom de templates |
| Inline styles huérfanos | Auditar y reemplazar 96 `style=""` antes de eliminar Bootstrap |
| Dependencia de bootstrap-icons | Bootstrap Icons es MIT; se mantiene. Solo se elimina Bootstrap CSS/JS |
| Boxicons sin licencia | Eliminar referencias a Boxicons; reemplazar por Bootstrap Icons (MIT) |
| Tiempo de migración | Estimar ~2-3 horas por template complejo; ~30-45 min por template simple |

---

## 9. Próximos pasos inmediatos

1. **Extender componentes M360 faltantes** (`_buttons.css`, `_cards.css`, `_badges.css`).
2. **Crear `_events.css`** con grid responsive y utilities específicas.
3. **Implementar `m360-modal.js` y `m360-dropdown.js`** en `static/events/js/` o `static/m360/js/`.
4. **Migrar Fase A** (templates aislados) como primera iteración.
5. **Verificar en dev server** tras cada template migrado.

---

## 10. Archivos generados en Paso 1

- `events/templates/events/base_itcss.html` — base ITCSS para events.
- `events/templates/events/components/_site_header.html` — header M360.
- `events/templates/events/components/_site_footer.html` — footer M360.
- `docs/bootstrap_replacement_map_events.json` — auditoría cruda de clases Bootstrap.
- `docs/bootstrap_replacement_map_events.md` — este documento.
