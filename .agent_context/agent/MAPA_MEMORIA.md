# MAPA_MEMORIA.md — Cómo navegar la memoria de memento

Da al agente principal **ambient awareness** de la memoria sin saturar contexto.

## Context Tree (Domain > Tema > Entry)
La memoria vive en `memory/graph/memory_index.json` (≈349 entries, 10 dominios). Jerarquía:
- **Domain** = campo `project` (mementobloom, m360, Management360, Administracion_UPN, jewelry_catalog, Ventas_Porta, docs, analyst, adherence_test).
- **Tema** = campo `type` (HANDOFF, CONTEXT, SOURCE, COMPONENT, NOTE, COMMIT) + `tags`.
- **Entry** = nodo hoja con `id`, `ts`, `path` (provenance), `summary`, `tags`.

## Herramienta de navegación (sin volcar contenido)
```bash
python3 tools/memory_tree.py                      # árbol completo Domain > Tema > Entry
python3 tools/memory_tree.py --domain Administracion_UPN --tags silabo
python3 tools/memory_tree.py --json               # conteos por dominio/tipo
```

## Orden de recuperación (tiers — ver `instructions/00-core.md`)
0. `SESSION.md` / `START_CONTEXT.md` (working context)
1. `memory_tree.py` para ubicar dominio/tema por nombre → leer el archivo directo (router)
2. `tools/context_builder.py --limit N` (ranked) para decidir por relevancia
3. lectura profunda de handoffs / `context/`
4. subagente aislado (`tutor-cursos/`) solo en trabajo ruidoso

## Documentación
- `docs/CONTEXT_TREE.md` — convención del Context Tree.
- `docs/ARQUITECTURA_AGENTE_2026.md` — arquitectura del agente (2026).
