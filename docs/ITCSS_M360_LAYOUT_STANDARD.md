# ITCSS M360 — Layout base estándar

## Objetivo
Usar `core/templates/m360/base.html` como layout genérico ITCSS M360 para apps sin layout personalizado o que quieran homogeneizarse.

## Contrato de herencia
- Extender desde `m360/base.html`.
- Usar `inner_content` para el contenido principal.
- Dejar las apps hijas entregar:
  - `header`
  - `sidebar`
  - `content` / `inner_content`
  - `footer`
  - `extra_head`
  - `extra_js`

## Modos recomendados
1. **Sin sidebar personalizado**: no declarar `{% block sidebar %}`; el layout queda con `<main class="m360-content">` ancho completo.
2. **Con sidebar estándar**: incluir `m360/components/_sidebar.html` y activar `m360-sidebar.js` con `[data-m360-sidebar-open]`, `[data-m360-sidebar-close]` y `[data-m360-backdrop]`.
3. **Mixto**: declarar header/sidebar/footer por app; el layout base solo pone `<main class="m360-content">`.

## Estándares visuales
- Usar tokens `--m360-*` desde `static/m360/css/tokens/_settings.css`.
- Usar componentes `m360-*` del sistema: cards, buttons, forms, tables, tabs, dropdowns, modal, sidebar.
- Scope: `.m360-root` para estilos de app.
- No mezclar Bootstrap/NiceAdmin en nuevas vistas.

## Migración por fases
1. App puente: `digitalizacion`.
2. Próxima app sugerida: `events` o `courses`.
3. Deprecar layouts legacy app por app; no eliminar `core/templates/layouts/base.html` hasta que nadie dependa de él.
