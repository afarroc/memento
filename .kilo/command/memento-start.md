---
description: Prepara progresivamente la semilla del agente MementoBloom y lanza Kilo
agent: memento-curador
model: kilo/kilo-auto/free
---
Para iniciar una nueva sesión de Kilo preparando la semilla progresiva del agente, ejecuta en una terminal nueva:

```bash
python3 tools/memento_kilo_start.py --project=mementobloom --limit 14
```

Arranque rápido local, sin regenerar ni trackear contexto:

```bash
python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8
```

Arranque universal para cualquier modelo:

```bash
python3 tools/bootstrap_context.py --print
```

Auditoría operativa del entorno:

```bash
python3 tools/optimize_agent.py --context
```

También puedes omitir `--project`, porque por defecto usa `mementobloom`:

```bash
python3 tools/memento_kilo_start.py --limit 14
```

Ese script prepara `.kilo/agent/init.md`, carga instrucciones progresivas desde `.kilo/agent/instructions/`, regenera `.kilo/agent/memento-curador.md`, puede regenerar `.kilo/START_CONTEXT.md` como archivo local ignorado y lanza Kilo en modo interactivo con `--agent memento-curador --model kilo/kilo-auto/free --dir . -i`.

Archivos de continuidad modelo-agnóstica:

- `.kilo/PROJECT_META.md`: meta del proyecto, trackeable.
- `.kilo/USER_CONTEXT.md`: contexto local del usuario, ignorado por Git.
- `.kilo/START_CONTEXT.md`: contexto Kilo regenerable, ignorado por Git.
- `tools/bootstrap_context.py`: imprime contexto compacto para cualquier modelo.
- `tools/optimize_agent.py`: audita agente, memoria, Git, servicios y seguridad.

Variantes útiles:

```bash
python3 tools/memento_kilo_start.py --quick
python3 tools/memento_kilo_start.py --print
python3 tools/memento_kilo_start.py --services
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context --panel
```
