# memento-curador

## Description
Curador de memoria histórica y contexto operativo para MementoBloom.

## Runtime
Puede ejecutarse con cualquier modelo, CLI o asistente capaz de leer archivos locales.

## Startup
Al iniciar, usa este flujo modelo-agnóstico:

```bash
# Contexto universal puro (stdout JSON/MD listo para cualquier modelo/CLI)
python3 tools/bootstrap_context.py --print     # modo completo por defecto
python3 tools/bootstrap_context.py --fast      # modo rápido opcional

# Flujo de sesión canónica (JSON de sesión)
python3 tools/session_bootstrap.py --print     # alias de --json
python3 tools/session_bootstrap.py --md        # alias markdown

# Para agentes externos: seed + contexto + sesión
python3 tools/session_start.py --print         # flujo completo
python3 tools/session_start.py --print --launch-agent   # idem + lanza MEMENTO_AGENT_CMD

# Contexto ranked y curación
python3 tools/context_builder.py --limit 20
python3 tools/quick_scan.py                    # escanea todos los proyectos
python3 tools/quick_scan.py <HANDOFF_PATH>     # indexa solo ese archivo
```

## Sources
- `.agent_context/PROJECT_META.md`
- `.agent_context/secure/USER_CONTEXT.md`
- `.agent_context/START_CONTEXT.md`
- `.agent_context/agent/init.md`
- `memory/graph/memory_index.json`
- `projects/mementobloom/HANDOFF_*.md`
