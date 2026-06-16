# MementoBloom - Sistema de Memoria Histórica IA

Sistema de registro y autorreferencia para interacciones con modelos de IA.

## Instalación
```bash
pip install -r requirements.txt
```

## Uso rápido

### Instalador guiado para primera instalación

```bash
./memento_install
```

El instalador valida Python, crea entorno virtual opcional, instala dependencias,
configura contexto local y permite iniciar el proyecto como agente usando el CLI
que el usuario elija.

### Comandos directos

```bash
python3 tools/context_builder.py

# Servidor principal (sala interactiva)
python3 tools/sala.py  # :8767

# Escaneo incremental
python3 tools/quick_scan.py

# Optimizar índice
python3 tools/optimize_memento.py --rebuild --compact

# Búsqueda
python3 tools/optimize_memento.py --search "ubigeo" --limit 5

# Preparar seed y contexto local de sesión, sin trackear contexto
python3 tools/session_start.py --quick --limit 8
# Compatibilidad con el launcher anterior
./memento_start --quick --limit 8

# Iniciar como agente externo configurado localmente
export MEMENTO_AGENT_CMD='<agent-cli> run --dir .'
./memento_start --print --no-services --limit 14 --launch-agent

# Contexto universal modelo-agnóstico para cualquier modelo, CLI o asistente
python3 tools/bootstrap_context.py --print

# Auditoría y optimización del agente
python3 tools/optimize_agent.py --context
```

## Estructura
```text
.agent_context/        # Contexto local, seed y configuración genérica
tools/                 # Scripts ejecutables
templates/             # HTML/CSS templates (sala.html)
memory/graph/          # Índice, grafo y estadísticas de memoria
memory/seeds/          # Semillas de sistema
archive/               # Archivos legacy ignorados por git
projects/              # Handoffs por proyecto
uploads/               # Archivos subidos a sala
etl/                   # Bitácoras locales (ignorado)
.env.example           # Variables de entorno de ejemplo
```

## Comandos rápidos desde terminal
```bash
python3 tools/bootstrap_context.py --print
python3 tools/session_start.py --quick --limit 8
python3 tools/optimize_agent.py --context
python3 tools/agent_prompt.py "pregunta" --limit 10
# Iniciar el proyecto como agente usando el CLI configurado localmente
MEMENTO_AGENT_CMD='<agent-cli> run --dir .' python3 tools/session_start.py --print --launch-agent
```
- `/memento-context --ready` - Verificar expansión
- `/memento-context --project Management360` - Contexto de proyecto
- `/memento-context --search ubigeo` - Búsqueda

## Arquitectura
```
PROJECT_META.md → USER_CONTEXT.md → START_CONTEXT.md → bootstrap_context.py → handoffs → memory_index.json → IA
```

## Formato compacto
```
ENTRY: {id,type,project,ts,tags,summary}
LINK: {source,target,weight}
```
