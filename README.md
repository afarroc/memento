# MementoBloom - Sistema de Memoria Histórica IA

Sistema de registro y autorreferencia para interacciones con modelos de IA.

## Instalación
```bash
pip install -r requirements.txt
```

## Uso como herramienta de memoria (Workspace Cliente Independiente)

Cuando mementobloom es **herramienta de memoria** para un proyecto cliente:

### Setup del cliente
```bash
# 1. Clonar proyecto cliente
git clone https://github.com/afarroc/adherence /ruta/proyecto_cliente

# 2. Clonar mementobloom como subdirectorio
cd /ruta/proyecto_cliente
git clone https://github.com/afarroc/memento.git mementobloom

# 3. Configurar estructura de memoria del cliente
mkdir -p .agent_context/agent/instructions .agent_context/secure .memento/memory/graph
cp mementobloom/.agent_context/PROJECT_META.md .agent_context/
cp mementobloom/.agent_context/agent/init.md .agent_context/agent/
cp mementobloom/.agent_context/agent/instructions/*.md .agent_context/agent/instructions/
echo '{}' > .memento/memory/graph/memory_index.json

# 4. Verificar estructura
ls -la .memento/memory/graph/
```

### Uso con CLI externo (ej: kilo)
```bash
cd /ruta/proyecto_cliente
export MEMENTO_WORKSPACE=$(pwd)
export PYTHONPATH="$(pwd)/mementobloom"

# Ver contexto del cliente
python3 mementobloom/tools/bootstrap_context.py --print --no-services

# Diagnóstico
python3 mementobloom/tools/doctor.py --startup --no-services

# Iniciar agente
export MEMENTO_AGENT_CMD="kilo run --dir . --agent agent-main -i \"$(python3 mementobloom/tools/bootstrap_context.py --print --no-services)\""
python3 mementobloom/tools/session_start.py --launch-agent
```

### Comandos del cliente
```bash
# Indexar handoffs del cliente
python3 mementobloom/tools/quick_scan.py .memento/projects/

# Búsqueda en memoria del cliente
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'mementobloom')
from tools.context_retriever import ContextRetriever
cr = ContextRetriever(workspace=Path('.'))
print(cr.get_context('query', limit=5))
"
```

# Contexto y continuidad de sesión

Cada sesión debe reconstruir contexto desde archivos locales y handoffs, sin depender de un modelo específico:

1. Leer `.agent_context/PROJECT_META.md`.
2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe.
3. Leer `.agent_context/START_CONTEXT.md` como contexto local regenerable.
4. Ejecutar `python3 tools/bootstrap_context.py --print`.
5. Continuar desde el último handoff relevante en `projects/*/`.
6. Verificar `git status`, servicios locales y memoria compacta antes de operar.

Los handoffs y `memory/graph/*.json` son memoria local no trackeable; no deben commitearse ni pushearse.

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

## Instalación limpia y diagnóstico

Para validar una instalación mínima sin contexto personalizado, handoffs, Redis, Sala o Panel:

```bash
python3 tools/doctor.py --startup --no-services
python3 tools/selftest.py
```

Para preparar un índice de memoria vacío en una instalación limpia:

```bash
python3 tools/quick_scan.py --index memory/graph/memory_index.json
```

### Comandos rápidos desde terminal

```bash
python3 tools/bootstrap_context.py --print --no-services
python3 tools/session_start.py --quick --limit 8
python3 tools/doctor.py --startup --no-services
python3 tools/selftest.py
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
