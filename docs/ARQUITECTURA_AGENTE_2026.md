# Arquitectura del Agente memento (2026)

Documento de referencia permanente. Define el tipo de agente que es memento y su comportamiento, alineado con la investigación de agentes de memoria de 2026.

> Nota de arquitectura: kilo (u otro agente de turno) es solo el ejecutor que recibe esta inyección desde **memento**. El sistema de agentes es memento; vive en `.agent_context/agent/`.

## 1. Tipo de agente

memento es un **Agent-Native Memory Curator** de tipo **single-agent**.

- **Agent-native (ByteRover, arxiv 2604.01599):** el mismo agente que razone CURA y RECUPERA la memoria. No hay pipeline externo de chunking/embedding/grafo separado del razonamiento. Las operaciones de memoria son herramientas del agente (`tools/quick_scan.py`, `context_builder.py`, `bootstrap_context.py`), no llamadas a un servicio ajeno.
- **Single-agent (consenso 2026: Anthropic, OpenAI, Microsoft, LangChain, Azure):** un coordinador que posee el contexto. No se usa multi-agente por defecto (68% de despliegues no lo necesitaba; ~15× costo en tokens; misma o mejor calidad en 64% de tareas).
- **Router-first:** para tareas pequeñas, el agente lee archivos directo (router por nombre). Solo delega a subagente aislado cuando el trabajo es ruidoso.

## 2. Split Working / Crystallized

| Capa | Archivos | Naturaleza | Propósito |
|------|----------|------------|-----------|
| Working (fluid) | `SESSION.md`, `.memento_runtime/session_canonical.json`, `.agent_context/START_CONTEXT.md` | Estado vivo de sesión | Razonamiento inmediato, ventana deslizante |
| Crystallized (knowledge graph) | `memory/graph/memory_index.json`, `graph.json` | Memoria compacta persistente | Retención a largo plazo, portable, versionable |

Inspirado en **Cognitive Scaffold (ACL 2026)**: decoupling de Fluid Working Context vs persistent Knowledge Graph. Al saturar el working context, se cristaliza en el grafo (handoff + index).

## 3. Context Tree jerárquico

La memoria se organiza como grafo jerárquico (Domain > Tema > Entry) con relaciones y provenance:

- **Domain:** `mementobloom`, `m360`, `Management360`, `Administracion_UPN`, `jewelry_catalog`, `Ventas_Porta`, ...
- **Tema:** por funcionalidad (migración ITCSS, cursos UPN, despliegue, email, ...)
- **Entry:** handoff / doc / nota, cada una con `@relaciones` y fuente.

Coincide con **ByteRover Context Tree** y **GAM (ACL 2026)** jerarquía graph-based. Almacenamiento en markdown/human-readable, sin DB externa (criterio de ByteRover y Memanto).

## 4. Retrieval progresivo por tiers

Resuelve la mayoría SIN LLM extra (patrón de ByteRover 5-tier, adaptado):

| Tier | Señal | Acción | LLM extra |
|------|-------|--------|-----------|
| 0 | En `SESSION.md`/`START_CONTEXT.md` | Usar directo | No |
| 1 | Nombre de archivo conocido | Leer archivo directo (router) | No |
| 2 | Tema general | `tools/context_builder.py --limit N` (ranked) | 1 llamada |
| 3 | Requiere profundidad | Leer handoffs / `context/` | Sí |
| 4 | Trabajo ruidoso | Subagente aislado (`tutor-cursos/`) → resumen | Solo en subagente |

## 5. Router vs Subagent (evitar sobre-orquestación)

Regla empírica (bobrenze, agentpatternscatalog, Vantaige 2026):
- **Inline** si: <3 archivos, secuencial, sin riesgo, necesita contexto de la sesión.
- **Spawn subagente** si: ≥3 archivos independientes, research, o creación masiva (p.ej. recrear curso de 17 lecciones). El subagente corre en contexto aislado y devuelve **resumen, no transcript**.

El único subagente hoy: `.agent_context/agent/tutor-cursos/` (recrea cursos UPN en M360 desde sílabos).

## 6. Curación activa (cristalización al cierre)

Al cerrar sesión, el agente consolida working→crystallized:
1. `python3 tools/quick_scan.py <HANDOFF_NUEVO>` → indexar.
2. Actualizar `memory/graph/memory_index.json`.
3. Escribir/actualizar `SESSION.md` y `.memento_runtime/session_canonical.json`.
4. Redactar resumen en sala/panel si se pide.
5. Handoff en `projects/mementobloom/HANDOFF_*.md`.

## 7. Qué NO hacer (lecciones 2026)

- No multi-agente por defecto (costo 15×, misma calidad en la mayoría).
- No orquestador para tareas secuenciales/pequeñas.
- No delegar memoria a pipeline externo (debe ser agent-native).
- No suprimir seguridad/ética (`90-safety.md` se mantiene).

## 8. Fuentes

- ByteRover — Agent-Native Memory (arxiv 2604.01599)
- MAGMA / GAM — Multi/Hierarchical Graph Agentic Memory (ACL 2026)
- Memanto — Typed Semantic Memory (arxiv 2604.22085)
- Cognitive Scaffold — Fluid/Crystallized memory (ACL 2026)
- Claude Code docs / agentpatternscatalog — Subagent Context-Isolation
- nexgismo / RankSquire / Azure CAF — Single vs multi-agent guidance 2026
