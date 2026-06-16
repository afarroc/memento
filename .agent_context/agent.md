# memento-curador

## Description
Curador de memoria histórica y contexto operativo para MementoBloom.

## Runtime
Puede ejecutarse con cualquier modelo, CLI o asistente capaz de leer archivos locales.

## Startup
Al iniciar, usa este flujo modelo-agnóstico:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/session_start.py --print
python3 tools/session_start.py --print --launch-agent
python3 tools/context_builder.py --limit 20
python3 tools/quick_scan.py <HANDOFF_PATH>
```

## Sources
- `.agent_context/PROJECT_META.md`
- `.agent_context/secure/USER_CONTEXT.md`
- `.agent_context/START_CONTEXT.md`
- `.agent_context/agent/init.md`
- `memory/graph/memory_index.json`
- `projects/mementobloom/HANDOFF_*.md`
