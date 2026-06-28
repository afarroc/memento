# 10 Contexto

Contexto inicial:
- Lee primero `.kilo/START_CONTEXT.md` si existe, pero no lo trackees.
- Si el usuario pide contexto, ejecuta `python3 tools/context_builder.py --limit 20`.
- Si el usuario pide iniciar una nueva sesión con contexto, ejecuta `python3 tools/memento_kilo_start.py --print`.
- Para arranque rápido, ejecuta `python3 tools/memento_kilo_start.py --quick`.
- Usa `.kilo/START_CONTEXT.md` solo como contexto local regenerable.
- Usa `memory/graph/memory_index.json` como índice compacto de memoria.
- Si existe contexto seguro en `.kilo/secure/SECURE.md`, léelo solo como referencia local y no lo expongas.
- El contexto de usuario puede residir en `.kilo/secure/USER_CONTEXT.md` y no se expone.

Reglas de arranque:
- Resume el estado del proyecto.
- Identifica el objetivo del usuario.
- Continúa desde el último handoff relevante.
- No repitas instrucciones ya registradas salvo que sea necesario para ejecutar una tarea.
