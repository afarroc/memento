# Agente Tutor de Cursos (memento)

Agente especialista residente en mementobloom para **crear y estructurar cursos en M360 (Management360)** a partir de los sílabos de UPN.

> Arquitectura: el proyecto y su sistema de agentes es **memento**. Kilo (u otro agente de turno) es solo el ejecutor que recibe la inyección desde memento. Este agente vive en `.agent_context/agent/tutor-cursos/`, hermano de `agent-main.md` y `agent-onboarding.md`.

## Propósito
En lugar de migrar manualmente la base MariaDB antigua (termux), el agente **recrea** cursos en M360 desde la fuente canónica: los sílabos en markdown de `projects/Administracion_UPN/docs/`.

## Espacio del agente (namespace aislado)
```
.agent_context/agent/tutor-cursos/
├── AGENT.md                  # Definición/persona (hot memory, <200 líneas)
├── MANUAL.md                 # Procedimiento paso a paso
├── context/                  # Cold memory — shards on-demand
│   ├── m360_modelo.md        # Modelo Course/Module/Lesson/Category
│   ├── m360_api.md           # Mapeo a tools/m360_bridge/client.py
│   ├── silabo_upn.md         # Convenciones de sílabos UPN
│   ├── migracion_mariadb.md  # Auditoría MariaDB→Postgres
│   └── lecciones_aprendidas.md
├── plantillas/               # Templates reutilizables
│   ├── curso.md
│   └── leccion.md
└── estado/                   # Estado persistente del agente
    └── indice_cursos.md      # Cursos recreados + cola de trabajo
```

## Herramienta
`tools/m360_bridge/client.py` — `api_v1_create_course`, `create_course_category`, `update_course`, `list_courses`, etc.

## Flujo
1. Leer sílabo fuente. 2. Consultar `estado/indice_cursos.md`. 3. Crear curso (o SQL si M360 no disponible o API con validación no superable). 4. Crear módulos (unidades) y lecciones (semanas) con markdown→HTML. 5. Registrar ID en `estado/`. 6. Resumen corto al padre.

## Diseño basado en evidencia 2026
- **Context Isolation** (claudecodeguide.dev, agentpatternscatalog): router vs contenido, aislamiento entre agentes, namespace por persona.
- **Deep Agents Pattern** (particula.tech): planner + virtual filesystem (offload a archivos) + memoria a largo plazo.
- **Codified Context Infrastructure**: constitución (hot) + agentes especializados (Tier 2) + conocimiento on-demand (Tier 3).
- Separación estricta fuente (`projects/Administracion_UPN/docs/`) vs estado del agente (`estado/`).

## Estado inicial (2026-07-19)
- Curso ya recreado: Matemática Básica Ciclo 02 → M360 ID 2 (5 mód, 17 les).
- Pendientes en `estado/indice_cursos.md`: UPN 55-60 (vacíos en MariaDB), Aritmética (3 les), Álgebra (18 les).
- MariaDB antigua CORRIENDO (PID 14868, 192.168.18.59:3306) solo para auditoría.
