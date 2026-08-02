# Plan: Optimizar agente principal de memento según narrativa contemporánea (2026)

> Fecha: 2026-07-19 | Proyecto: memento (mementobloom) | Base: investigación web 2026 (ByteRover, MAGMA, GAM, Memanto, Cognitive Scaffold, Claude Code subagents, agentpatternscatalog)

## 1. Diagnóstico

memento YA es un agente de memoria (MAG) por diseño. Tiene infraestructura: `memory/graph/memory_index.json` (408KB, 350 entradas), `context_builder.py` (ranked), `quick_scan.py`, `vault_*`, `SESSION.md` + `.memento_runtime/session_canonical.json`.

**El gap no es de infraestructura, es de declaración y comportamiento.** El agente principal (`00-core.md`, `agent-main.md`) no declara explícitamente:
- Su arquitectura de memoria (Context Tree jerárquico + tiers de retrieval).
- El split working (SESSION.md) vs crystallized (memory_index).
- Comportamiento de curación activa (consolidar al cierre de sesión).
- Cuándo usar router por archivo vs subagente aislado.

## 2. Tipo de agente que necesita memento (según evidencia 2026)

**Single-agent, agent-native Memory Curator** con:
- **Memoria agent-native** (ByteRover): el mismo agente que razona CURA y RECUPERA la memoria; no pipeline externo. memento ya cumple (sus tools son del agente).
- **Context Tree jerárquico** (Domain>Tema>Subtema>Entry) con relaciones y provenance.
- **Retrieval progresivo por tiers**: resolver la mayoría SIN LLM (índice/router por archivo), escalar solo a lectura profunda cuando hace falta.
- **Working vs Crystallized**: SESSION.md = fluid working context; memory_index = crystallized knowledge graph.
- **Router por lectura de archivos, NO orquestador pesado**: para tareas pequeñas, `agent-main` lee `context/*.md` directo. Solo cuando hay trabajo ruidoso (leer 50 archivos, crear 17 lecciones) se delega al subagente aislado `tutor-cursos/` (patrón orquestador-worker validado).

Esto confirma y formaliza lo ya construido: NO hay que re-arquitecturar, sino **declarar y afinar**.

## 3. Plan de acción (5 fases)

### Fase A — Declarar arquitectura de memoria en el agente principal
- [x] A1 Reescribir `.agent_context/agent/instructions/00-core.md` para declarar: rol = "Agent-Native Memory Curator (single-agent)", split Working/Crystallized, Context Tree, tiers de retrieval, router-vs-subagent rule.
- [x] A2 Actualizar `.kilo/agents/agent-main.md` (description + cuerpo) para alinear identidad con la narrativa 2026.
- [x] A3 Crear `docs/ARQUITECTURA_AGENTE_2026.md` — documenta el modelo (Context Tree + tiers + working/crystallized + router/subagent), fundamentado en las fuentes.

### Fase B — Context Tree jerárquico explícito
- [x] B1 Definir convención de jerarquía en `memory/graph/`: Domain (mementobloom/m360/UPN/...) > Tema > Entry, con `@relaciones` y provenance.
- [x] B2 Documentar el estándar en `docs/CONTEXT_TREE.md` y `.agent_context/agent/MAPA_MEMORIA.md` (mapa del agente principal).
- [x] B3 `tools/memory_tree.py` que liste el árbol de dominios/temas sin volcar contenido (ambient awareness, como ByteRover).

### Fase C — Retrieval progresivo por tiers (behavioral)
- [x] C1 Codificar en `agent-main`/`00-core.md` la regla de tiers:
  - Tier 0: ¿la respuesta está en SESSION.md/START_CONTEXT? → usarla sin LLM extra.
  - Tier 1: ¿router por dominio/tema? → `python3 tools/memory_tree.py [--domain X --tags Y]` para ubicar, luego lee el archivo directo (sin subagente).
  - Tier 2: `python3 tools/context_builder.py --limit N` para decidir por ranking.
  - Tier 3: lectura profunda de handoffs / `context/`.
  - Tier 4: subagente aislado solo si trabajo ruidoso (≥3 archivos / research / creación masiva).
- [x] C2 Documentar la regla en `00-core.md`, `docs/ARQUITECTURA_AGENTE_2026.md` y `bootstrap_context.py`.

### Fase D — Curación activa (crystallization)
- [x] D1 Al cierre de sesión, el agente debe: indexar handoff nuevo (`quick_scan.py`), actualizar `memory_index.json`, escribir/actualizar `SESSION.md` y `.memento_runtime/session_canonical.json`, y redactar resumen en sala/panel si se pide.
- [x] D2 Regla: "cierra sesión = cristaliza" (consolidar working→crystallized).
- [x] D3 Checklist de cierre añadida a `00-core.md`.

### Fase E — Router vs Subagent (evitar sobre-orquestación)
- [x] E1 Afinar `tutor-cursos/` para que solo se use en trabajo ruidoso (ya definido). Confirmar que `agent-main` NO invoca subagentes para tareas pequeñas.
- [x] E2 Documentar la regla "≥3 archivos o research → spawn; si no, inline" en `docs/ARQUITECTURA_AGENTE_2026.md` y `00-core.md`.

## 4. Qué NO hacer (lecciones de la investigación)
- NO convertir memento en multi-agente por defecto (68% de casos no lo necesita; ~15× costo tokens; misma calidad en 64% de tareas).
- NO usar orquestador para tareas secuenciales/pequeñas.
- NO delegar memoria a pipeline externo (debe ser agent-native).
- NO suprimir seguridad/ética (`90-safety.md` se mantiene).

## 5. Criterio de éxito (cumplido)
- [x] `agent-main` y `00-core.md` declaran explícitamente arquitectura 2026 (single-agent, agent-native memory, Context Tree, tiers, working/crystallized, router-first).
- [x] Existe `docs/ARQUITECTURA_AGENTE_2026.md` fundamentado.
- [x] El cierre de sesión incluye paso de cristalización (curación activa) — checklist en `00-core.md`.
- [x] `tutor-cursos/` es el único subagente, solo para trabajo ruidoso.

## 6. Archivos creados/modificados
- `.agent_context/agent/instructions/00-core.md` (rewrite — arquitectura 2026, tiers, checklist cierre)
- `.kilo/agents/agent-main.md` (align description + bloque arquitectura)
- `docs/ARQUITECTURA_AGENTE_2026.md` (nuevo — documento permanente fundamentado)
- `docs/CONTEXT_TREE.md` (nuevo — convención jerárquica Domain>Tema>Entry)
- `.agent_context/agent/MAPA_MEMORIA.md` (nuevo — mapa de navegación del agente)
- `tools/memory_tree.py` (nuevo — lista árbol sin volcar contenido, integrado en bootstrap)
- `tools/bootstrap_context.py` (añade comando `memory_tree`)
- `.agent_context/agent/tutor-cursos/AGENT.md` (nuevo — agente especialista)
- `.agent_context/agent/tutor-cursos/MANUAL.md` (nuevo)
- `.agent_context/agent/tutor-cursos/context/` (5 shards)
- `.agent_context/agent/tutor-cursos/plantillas/` (curso.md, leccion.md)
- `.agent_context/agent/tutor-cursos/estado/indice_cursos.md` (nuevo)
- `docs/AGENTE_TUTOR_CURSOS.md` (nuevo)
- `docs/AGENTE_TUTOR_CURSOS_PROPUESTA.md` (nuevo)

## 7. Estado actual
Todas las fases (A, B, C, D, E) están **completadas**. El agente principal de memento está alineado con la narrativa 2026: single-agent, agent-native Memory Curator, Context Tree jerárquico, retrieval por tiers, working/crystallized split, y subagente aislado solo para trabajo ruidoso.

## 8. Próximos pasos sugeridos (no iniciados)
- Probar el agente tutor recreando un curso UPN vacío (p.ej. Comunicación 1) desde su sílabo.
- Continuar migración ITCSS de templates restantes en M360 (`standalone_lesson_form`, `standalone_lessons_list`, `tutor/*`, `admin/*`).
- (Opcional) `tools/memory_tree.py --watch` o integración con panel para visualizar el árbol.
- (Opcional) fijar relaciones cruzadas explícitas `@dominio/tema/entry` en `tags` para grafo multi-dominio.
