# 10 Contexto

Contexto inicial:
- Lee primero `.agent_context/START_CONTEXT.md` si existe, pero no lo trackees.
- Si el usuario pide contexto, ejecuta `python3 tools/context_builder.py --limit 20`.
- Si el usuario pide iniciar una nueva sesión con contexto, ejecuta `python3 tools/bootstrap_context.py --print`.
- Para arranque rápido, ejecuta `python3 tools/bootstrap_context.py --print`.
- Usa `.agent_context/START_CONTEXT.md` solo como contexto local regenerable.
- Usa `memory/graph/memory_index.json` como índice compacto de memoria.

Reglas de arranque:
- Resume el estado del proyecto.
- Identifica el objetivo del usuario.
- Continúa desde el último handoff relevante.
- No repitas instrucciones ya registradas salvo que sea necesario para ejecutar una tarea.

Ubicación de archivos:
- `.agent_context/` → solo contexto del agente (semillas, instrucciones, START_CONTEXT regenerable, secure/).
- `projects/*/HANDOFF_*.md` → registros de gestión, cierres, conciliaciones, auditorías.
- `docs/` → documentación permanente del proyecto.
- Nunca pongas documentación de gestión en `.agent_context/` (rompe el propósito del proyecto).
