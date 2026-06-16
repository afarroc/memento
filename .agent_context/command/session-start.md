---
description: Prepara la semilla del agente y el contexto local de sesión
agent: memento-curador
---
Para iniciar una nueva sesión preparando la semilla progresiva del agente, ejecuta en una terminal nueva:

```bash
python3 tools/session_start.py --project=mementobloom --limit 14
```

Arranque rápido local, sin regenerar ni trackear contexto:

```bash
python3 tools/session_start.py --quick --project=mementobloom --limit 8
```

Arranque universal para cualquier modelo, CLI o asistente:

```bash
python3 tools/bootstrap_context.py --print
```

Auditoría operativa del entorno:

```bash
python3 tools/optimize_agent.py --context
```

También puedes omitir `--project`, porque por defecto usa `mementobloom`:

```bash
python3 tools/session_start.py --limit 14
```

Ese script prepara `.agent_context/agent/init.md`, carga instrucciones progresivas desde `.agent_context/agent/instructions/`, regenera `.agent_context/agent/memento-curador.md` y puede regenerar `.agent_context/START_CONTEXT.md` como archivo local ignorado. No impone ningún agente externo; el CLI, modelo o asistente que use el proyecto decide cómo consumir ese contexto.

Para iniciar el proyecto como agente usando un CLI configurado localmente:

```bash
export MEMENTO_AGENT_CMD='<agent-cli> run --dir .'
python3 tools/session_start.py --print --no-services --limit 14 --launch-agent
```

Con el wrapper compatible:

```bash
export MEMENTO_AGENT_CMD='<agent-cli> run --dir .'
./memento_start --print --no-services --limit 14 --launch-agent
```

Si el CLI requiere instrucciones explícitas, usa el contexto generado:

```bash
python3 tools/bootstrap_context.py --print
```

Archivos de continuidad modelo-agnóstica:

- `.agent_context/PROJECT_META.md`: meta del proyecto, trackeable.
- `.agent_context/secure/USER_CONTEXT.md`: contexto local del usuario, ignorado por Git.
- `.agent_context/START_CONTEXT.md`: contexto local regenerable, ignorado por Git.
- `tools/bootstrap_context.py`: imprime contexto compacto para cualquier modelo.
- `tools/session_start.py`: prepara seed y contexto local de sesión.
- `tools/optimize_agent.py`: audita agente, memoria, Git, servicios y seguridad.

Variantes útiles:

```bash
python3 tools/session_start.py --quick
python3 tools/session_start.py --print
python3 tools/session_start.py --services
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context --panel
```
