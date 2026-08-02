# Convención Context Tree de memento

El `memory/graph/memory_index.json` se organiza como un **Context Tree jerárquico** (Domain > Tema > Entry), inspirado en ByteRover (arxiv 2604.01599) y GAM (ACL 2026). Cada entry es un nodo hoja con relaciones y provenance.

## 1. Dominios (Domain = campo `project`)
Cada entrada pertenece a un dominio. Dominios actuales:

| Dominio | Significado |
|---------|-------------|
| `mementobloom` | El proyecto memento en sí (agente, tools, infra) |
| `m360` | Cliente M360 (Management360, trabajo directo sobre su repo) |
| `Management360` | Gestión de proyectos M360 (vía bridge API) |
| `Administracion_UPN` | Proyecto UPN (sílabos, cursos) |
| `jewelry_catalog` | Cliente jewelry_catalog |
| `Ventas_Porta` | Cliente Ventas_Porta |
| `docs` | Documentación permanente del proyecto |
| `analyst` | Análisis / investigación |
| `adherence_test` | Proyecto de prueba |

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
