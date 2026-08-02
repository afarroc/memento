# Propuesta: Agente Tutor de Cursos — Espacio, entorno y arquitectura

> Documento de diseño validado contra mejores prácticas 2026 (Claude Code docs, agentpatternscatalog "Subagent Context-Isolation", llmbestpractices "Subagents", Deep Agents Pattern particula.tech, codified-context-infrastructure, agentic-engineering).
> Fecha: 2026-07-19 — Proyecto: mementobloom (clientes: Management360, Administracion_UPN)

---

## 1. Objetivo

Crear un **agente especialista residente** en mementobloom que actúe como *tutor de cursos*: crea, estructura y mantiene cursos en M360 (Management360) a partir de los sílabos de UPN (`projects/Administracion_UPN/docs/`), recreando el contenido que antes se migraba manualmente desde la MariaDB antigua (termux).

En lugar de migrar manualmente, el agente **recrea** cursos desde la fuente canónica (sílabos UPN en markdown) usando el bridge `tools/m360_bridge/client.py`.

---

## 2. Principio rector (de la investigación web)

La evidencia 2026 convergente dice que lo que hace escalable a un sistema multi-agente no es la calidad de las instrucciones, sino **dónde están los límites (walls)**:

1. **Router vs contenido**: el archivo siempre-cargado es un índice de punteros, no una biblioteca. El conocimiento vive en shards, se carga solo cuando la tarea coincide.
2. **Aislamiento entre agentes**: el agente corre en su propia ventana de contexto; el padre recibe solo un resumen.
3. **Namespace por persona**: cada agente tiene su propio folder de estado, manuales y herramientas. Sin dumping ground compartido.
4. **Separación input vs output**: los manuales/fuentes NO se mezclan con los entregables generados.

Fuentes: claudecodeguide.dev (Subagent Context-Isolation), agentpatternscatalog.org (Subagent Isolation), llmbestpractices.com (Claude Code Subagents), particula.tech (Deep Agents Pattern: planner + virtual filesystem + subagentes + memoria), malakavenu.com / sebyx07 / codified-context-infrastructure (estructura agents/ + rules/ + context/ + skills/ + commands/).

---

## 3. Diseño para mementobloom (respeta convenciones del proyecto)

**Aclaración de arquitectura:** el proyecto y su sistema de agentes es **memento**, no kilo. Kilo (u otro agente de turno) es solo el ejecutor que recibe la inyección desde memento. Por tanto, el agente tutor se define dentro de la arquitectura de memento: `.agent_context/agent/` (donde ya viven `agent-main.md`, `agent-onboarding.md` e `instructions/`). NO se usa `.kilo/agents/` (eso es config del agente de turno, no del proyecto).

### 3.1 Definición del agente (memento)
`.agent_context/agent/tutor-cursos/AGENT.md` — archivo hermano de `agent-main.md`, con frontmatter mínimo de memento (el agente de turno lo inyecta según corresponda). Incluye misión, reglas de arranque, herramienta (bridge) y límites.

### 3.2 Espacio del agente (namespace aislado)
 `.agent_context/agent/tutor-cursos/` ← **todo lo del agente vive aquí**, nunca mezclado con el contexto general del agente principal (`instructions/`).

```
.agent_context/agent/tutor-cursos/
├── AGENT.md                  # Semilla/persona del tutor (hot memory, <200 líneas)
├── MANUAL.md                 # Manual de operación: cómo recrear un curso paso a paso
├── context/                  # Cold memory — shards por tema (cargados on-demand)
│   ├── m360_modelo.md        # Modelo de datos M360: Course/Module/Lesson/Category
│   ├── m360_api.md           # Mapeo a tools/m360_bridge/client.py (create_course, etc.)
│   ├── silabo_upn.md         # Convenciones de sílabos UPN (Ciclo 01/02, unidades, semanas)
│   ├── migracion_mariadb.md  # Auditoría MariaDB→Postgres (qué falta, qué está vacío)
│   └── lecciones_aprendidas.md
├── plantillas/               # Templates reutilizables
│   ├── curso.md              # Esqueleto de curso (módulos/semanas)
│   └── leccion.md            # Esqueleto de lección (HTML desde markdown)
└── estado/                   # Namespace de estado del agente (persistente entre sesiones)
    ├── indice_cursos.md      # Qué cursos ya recreó y su ID en M360
    └── cola_trabajo.md       # Pendientes (p.ej. UPN 55-60, Aritmética, Álgebra)
```

### 3.3 Herramienta del agente
El agente NO necesita herramienta nueva: usa `tools/m360_bridge/client.py` (ya tiene `api_v1_create_course`, `create_course_category`, `update_course`, list, etc.).
- Si se requiere un helper específico (p.ej. parsear sílabo markdown → payload de curso), se añade `tools/m360_bridge/tutor_cursos.py` (no en el namespace del agente, es tool compartido del proyecto).

### 3.4 Documentación permanente
La especificación del agente también va a `docs/` (documentación permanente del proyecto):
`docs/AGENTE_TUTOR_CURSOS.md` — arquitectura, alcance, y cómo invocarlo.

### 3.5 Handoff de gestión
Cierres del agente tutor → `projects/mementobloom/HANDOFF_*_tutor_cursos.md` (mismo patrón que los demás).

---

## 4. Flujo de trabajo del agente (recrear curso UPN)

1. Leer sílabo fuente en `projects/Administracion_UPN/docs/Ciclo_02/...`.
2. Consultar `estado/indice_cursos.md` para no duplicar.
3. `api_v1_create_course` (o SQL si M360 no disponible o la API falla por validación no superable).
4. Crear módulos (unidades) y lecciones (semanas) desde el sílabo.
5. Convertir contenido markdown → HTML (`markdown.markdown(extensions=['tables','fenced_code'])`, escapar `$`).
6. Registrar en `estado/indice_cursos.md` el ID asignado.
7. Devolver al agente padre un resumen corto (ID curso, módulos, lecciones).

---

## 5. Por qué este diseño es el más eficiente (según la evidencia)

- **Hot memory pequeña** (`AGENT.md` <200 líneas, solo mapa+reglas) → bajo costo de tokens por sesión.
- **Cold memory en `context/`** cargada on-demand → el agente principal nunca carga los 5 shards si no trabaja en cursos.
- **Namespace `estado/` aislado** → el agente acumula estado sin contaminar el `SESSION.md` ni la memoria global.
- **Bridge existente reutilizado** → no se reinventa la integración M360.
- **Separación fuentes/entregables** → los sílabos (fuente) no se tocan; el agente solo escribe en M360 vía API.

---

## 6. Siguientes pasos (ESTADO: IMPLEMENTADO 2026-07-19)

1. ✅ Creado `.agent_context/agent/tutor-cursos/AGENT.md` (definición memento, hermano de agent-main.md).
2. ✅ Creado namespace `.agent_context/agent/tutor-cursos/`: MANUAL.md, context/ (5 shards), plantillas/ (curso.md, leccion.md), estado/indice_cursos.md.
3. ✅ Creado `docs/AGENTE_TUTOR_CURSOS.md` (especificación permanente).
4. (Opcional) `tools/m360_bridge/tutor_cursos.py` helper de parseo de sílabo.
5. Probar recreando un curso UPN vacío (p.ej. Comunicación 1) desde su sílabo.
