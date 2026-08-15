# 10 Contexto

Contexto inicial:
- Lee primero `.agent_context/START_CONTEXT.md` si existe, pero no lo trackees.
- Si el usuario pide contexto, ejecuta `python3 tools/context_builder.py --limit 20`.
- Por defecto, inicia cada sesión con el flujo completo: `python3 tools/bootstrap_context.py --print`.
  - Este modo ejecuta y verifica los 10 pasos de arranque de `PROJECT_META.md` e incluye el checklist y la personalidad del usuario en el output.
- Si el usuario pide explícitamente arranque rápido, usa `python3 tools/bootstrap_context.py --fast`.
  - Omite el checklist detallado y la lectura de `memory/personality/user_personality.md`.
- Usa `.agent_context/START_CONTEXT.md` solo como contexto local regenerable.
- Usa `memory/graph/memory_index.json` como índice compacto de memoria.

Reglas de arranque:
- Por defecto, sigue los 10 pasos listados en `.agent_context/PROJECT_META.md`.
- Resume el estado del proyecto después del bootstrap.
- Identifica el objetivo del usuario.
- Continúa desde el último handoff relevante.
- No repitas instrucciones ya registradas salvo que sea necesario para ejecutar una tarea.

Ubicación de archivos:
- `.agent_context/` → solo contexto del agente (semillas, instrucciones, START_CONTEXT regenerable, secure/).
- `projects/*/HANDOFF_*.md` → registros de gestión, cierres, conciliaciones, auditorías.
- `docs/` → documentación permanente del proyecto.
- Nunca pongas documentación de gestión en `.agent_context/` (rompe el propósito del proyecto).
