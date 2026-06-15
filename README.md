# MementoBloom - Sistema de Memoria Histórica IA

Sistema de registro y autorreferencia para interacciones con modelos de IA.

## Instalación
```bash
pip install -r requirements.txt
```

## Uso rápido
```bash
# Verificar memoria
python3 tools/context_builder.py

# Servidor principal (sala interactiva)
python3 tools/sala.py  # :8767

# Escaneo incremental
python3 tools/quick_scan.py

# Optimizar índice
python3 tools/optimize_memento.py --rebuild --compact

# Búsqueda
python3 tools/optimize_memento.py --search "ubigeo" --limit 5

# Arranque rápido de sesión, sin trackear contexto
python3 tools/memento_kilo_start.py --quick --limit 8

# Contexto universal modelo-agnóstico para cualquier modelo
python3 tools/bootstrap_context.py --print

# Auditoría y optimización del agente
python3 tools/optimize_agent.py --context
```

## Estructura
```text
.kilo/                  # Configuración y agente Kilo
tools/                  # Scripts ejecutables
templates/              # HTML/CSS templates (sala.html)
memory/graph/           # Índice, grafo y estadísticas de memoria
memory/seeds/           # Semillas de sistema
archive/                # Archivos legacy ignorados por git
projects/               # Handoffs por proyecto
uploads/                # Archivos subidos a sala
etl/                    # Bitácoras locales (ignorado)
.env.example            # Variables de entorno de ejemplo
```

## Uso rápido
```bash
# Desde tools/
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context
python3 tools/memento_kilo_start.py --quick --limit 8
```
- `/memento-context --ready` - Verificar expansión
- `/memento-context --project Management360` - Contexto de proyecto
- `/memento-context --search ubigeo` - Búsqueda

## Arquitectura
```
seed.md → quick_scan → memory_index.json → context_builder → IA
```

## Formato compacto
```
ENTRY: {id,type,project,ts,tags,summary}
LINK: {source,target,weight}
```