# Memento Project Meta

Objetivo meta del usuario:

- Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico.
- El contexto debe ser legible por cualquier modelo, CLI o agente que pueda leer archivos locales.
- La continuidad debe basarse en archivos explícitos, handoffs, memoria compacta, estado Git y servicios verificables.
- Memento funciona como herramienta de memoria instalada dentro del proyecto cliente. El proyecto cliente es el proyecto principal.

Reglas universales de arranque:

1. Leer `.agent_context/PROJECT_META.md`.
2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe.
3. Leer `memory/personality/user_personality.md` para calibrar tono y estilo.
4. Leer `.agent_context/START_CONTEXT.md` si existe, como contexto local regenerable no trackeado.
5. Ejecutar `python3 tools/session_start.py --print` como flujo único de arranque del agente main.
   - Este flujo prepara el agent seed, carga todas las instrucciones de `agent/instructions/*.md`, actualiza `START_CONTEXT.md` y expande el contexto universal.
   - Para arranque rápido, usar `python3 tools/session_start.py --print --fast`.
6. Leer los handoffs recientes del proyecto activo (ver `projects/` o `USER_CONTEXT.md`).
7. Verificar `git status`, último commit y cambios pendientes.
8. Verificar Redis/sala si la tarea involucra panel o comunicación.
9. Continuar desde el último handoff relevante sin pedir información ya registrada.

> Nota: `python3 tools/bootstrap_context.py --print` es la herramienta interna que expande el contexto universal dentro del flujo de `session_start.py`. No es un punto de entrada separado para el agente main.

## Configuración del proyecto

Ver `.agent_context/secure/USER_CONTEXT.md` para configuración contextual específica.

### Proyectos cliente registrados
- **perfil_personal** (Arturo) — Cuadro de mando personal, M360 ID 24, Ticket TICK-0013
  - Naturaleza: dashboard web, no almacena datos físicos
  - Datos organizados en `/Volumes/Macintosh HD - Datos/01_CV..08_Config`
  - Stack: HTML/CSS/JS vanilla, puerto 8080
- **Carpinteria** — Proyecto de carpintería/bricolaje digital, M360 ID 25, Tickets TICK-0027/TICK-0028/TICK-0029
  - Naturaleza: documentación + scaffolding Django + HTMX
  - Ruta física código fuente: `/Volumes/Macintosh HD - Datos/projects/Carpinteria/src/carpinteria_project/`
  - Stack objetivo: Django + HTMX + Alpine.js + Tailwind; Fase 3 React + Three.js
  - Seguimiento memento: `mementobloom/projects/Carpinteria/`

Arquitectura de continuidad:

```text
SESSION.md → PROJECT_META.md → USER_CONTEXT.md → memory/personality/user_personality.md → tools/session_bootstrap.py → handoffs → memory_index.json → IA
```

Archivos críticos:

- `SESSION.md`: estado canónico de sesión, generado automáticamente, no trackeable.
- `.agent_context/PROJECT_META.md`: meta del proyecto, trackeable.
- `.agent_context/secure/USER_CONTEXT.md`: contexto local del usuario, no trackeable.
- `memory/personality/user_personality.md`: memoria de personalidad del usuario, no trackeable.
- `memory/graph/memory_index.json`: memoria compacta, no trackeable.
- `projects/*/HANDOFF_*.md`: handoffs locales del proyecto activo, no trackeables.
- `tools/session_bootstrap.py`: bootstrap universal para cualquier modelo, CLI o agente.
- `tools/context_builder.py`: contexto ranked para revisión más profunda.

## Personalidad del agente

El agente lee `memory/personality/user_personality.md` para calibrar tono, valores y estilo de comunicación.
Ver `docs/PERSONALIDAD_AGENTE.md` para la especificación completa.

## Neutralidad de agente

El proyecto no depende de ningún agente, modelo o CLI específico.

**Regla absoluta para el agente main de memento y agentes generados desde memento:**
- DEBEN cargar `.agent_context/agent/instructions/*.md` como parte obligatoria del contexto inicial.
- NO deben ignorar estas instrucciones bajo ninguna circunstancia.
- El bootstrap (`tools/bootstrap_context.py`) incluye estas instrucciones en el contexto generado.

Para agentes externos no-memento que no soporten este formato, pueden reconstruir el contexto mínimo desde:
- `.agent_context/PROJECT_META.md`
- `.agent_context/secure/USER_CONTEXT.md`
- `tools/bootstrap_context.py`
- handoffs recientes
- estado Git

Reglas de seguridad:

- No exponer secretos, tokens, contraseñas ni contenido de vault.
- No commitear ni pushear `.agent_context/START_CONTEXT.md`, `.agent_context/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, handoffs ni datos de sesión.
- No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita.
- Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional.

Comandos base:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/context_builder.py --limit 12
python3 tools/quick_scan.py <HANDOFF_PATH>
python3 tools/backup_local.py backup
```

Comandos opcionales:

```bash
python3 tools/optimize_agent.py --context
python3 tools/export_memory.py --format markdown --output docs/memory_export.md
```