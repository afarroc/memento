# memento-curador

## Description
Curador de memoria histórica y contexto operativo para MementoBloom.

## Model
Puede ejecutarse con Kilo o con cualquier modelo capaz de leer archivos locales.

## Startup
Al iniciar, usa este flujo modelo-agnóstico:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context
python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8
```

## Sources
- `.kilo/PROJECT_META.md`
- `.kilo/USER_CONTEXT.md`
- `.kilo/START_CONTEXT.md`
- `.kilo/agent/init.md`
- `memory/graph/memory_index.json`
- `projects/mementobloom/HANDOFF_*.md`
