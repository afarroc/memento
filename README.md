# Memento - Sistema de Memoria Histórica IA

Sistema de registro y autorreferencia para interacciones con modelos de IA.

## Filosofía

Memento funciona como **herramienta de memoria** instalada dentro del proyecto cliente, no como un proyecto independiente. Cuando se ejecuta `session_start`, el agente reconoce el proyecto cliente como el proyecto principal. Toda la memoria, handoffs y contexto son project-scoped.

## Instalación

### Como subdirectorio en proyecto cliente (recomendado)

```bash
# 1. Clonar proyecto cliente
git clone https://github.com/afarroc/adherence /ruta/proyecto_cliente
cd /ruta/proyecto_cliente

# 2. Clonar memento como subdirectorio
git clone https://github.com/afarroc/memento.git mementobloom

# 3. Ejecutar instalador (auto-detecta modo cliente)
bash mementobloom/memento_install --auto
```

### Modo desarrollo (dentro del repo memento)

```bash
cd /ruta/memento
bash memento_install --auto
```

### Inicialización manual

```bash
# Generar estructura .agent_context y memoria vacía
python3 tools/init_project.py
```

## Arquitectura: ROOT vs Workspace

```
ROOT (instalación de Memento)
  - Código, templates, scripts, instrucciones del agente
  - paths relativos a ROOT para assets del tool

WS_ROOT (workspace activo = proyecto cliente)
  - .agent_context/ (PROJECT_META, seed, contexto)
  - .memento/ (runtime, pids, logs)
  - memory/graph/ (índice JSON)
  - projects/ (handoffs por proyecto)
  - Todo resuelto via MEMENTO_WORKSPACE env var
```

**Detección automática:**
- `MEMENTO_WORKSPACE` seteado → usa ese directorio
- `ROOT/.git` existe (repo memento) → `WS_ROOT = ROOT`
- Otros (subdirectorio cliente) → `WS_ROOT = parent(ROOT)`

## Uso

### Comandos base

```bash
# Contexto universal modelo-agnóstico
python3 tools/bootstrap_context.py --print

# Diagnóstico
python3 tools/doctor.py --startup

# Test suite
python3 tools/selftest.py

# Inicio rápido de sesión
python3 tools/session_start.py --quick --limit 8

# Escanear handoffs al índice
python3 tools/quick_scan.py <HANDOFF_PATH>

# Contexto ranked
python3 tools/context_builder.py --limit 12

# Auditoría de agente
python3 tools/optimize_agent.py --context
```

### Comandos nuevos

```bash
# Exportar memoria a markdown/json para integrar en docs del cliente
python3 tools/export_memory.py --format markdown --output docs/memory_export.md

# Limpiar artefactos generados (seed, contexto, runtime)
python3 tools/clean_workspace.py --dry-run
python3 tools/clean_workspace.py --force

# Inicializar proyecto cliente con estructura memento
python3 tools/init_project.py --workspace /ruta/proyecto_cliente
```

### Wrappers de cliente

Después de `memento_install`, el cliente tiene wrappers en `.memento/bin/`:

```bash
memento-bootstrap_context
memento-doctor
memento-selftest
memento-quick_scan
memento-context_builder
memento-session_start
memento-optimize_agent
memento-export_memory
memento-init_project
memento-clean_workspace
```

Y script de inicio:
```bash
./memento-start
```

## Configuración de agente externo

Para usar con Kilo, Claude, Code, etc.:

```bash
# En .agent_context/secure/AGENT_CMD.env o variables de entorno
export MEMENTO_AGENT_CMD="kilo run --dir . --agent agent-main"

# O pasar directo
MEMENTO_AGENT_CMD="claude run" python3 tools/session_start.py --launch-agent
```

## Contexto y continuidad de sesión

Cada sesión reconstruye contexto desde archivos locales:

1. Leer `.agent_context/PROJECT_META.md`
2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe
3. Leer `.agent_context/START_CONTEXT.md` (regenerable, no trackeable)
4. Ejecutar `python3 tools/bootstrap_context.py --print`
5. Leer handoffs recientes en `projects/<proyecto>/HANDOFF_*.md`
6. Verificar `git status` y servicios
7. Continuar desde el último handoff relevante

## Aislamiento por proyecto

- Cada instancia de Memento pertenece a un solo proyecto
- El seed del agente lleva `project: <nombre>` en su frontmatter
- Handoffs y memoria son project-scoped
- No hay mezcla de contexto entre proyectos

## Estructura de directorios

```text
.agent_context/           # Contexto del proyecto cliente
  PROJECT_META.md         # Meta del proyecto (trackeable)
  START_CONTEXT.md        # Contexto de inicio (no trackeado)
  agent/                  # Seed e instrucciones del agente
    init.md
    agent-main.md         # Seed generado dinámicamente
    instructions/         # 00-core, 10-context, 20-memory, etc.
  secure/                 # USER_CONTEXT.md, SECURE.md (no trackeado)

core/                     # Módulos compartidos
  paths.py                # workspace_root(), detect_project_name()
  index.py                # Memoria: load/save/top_entries/manifest
  services.py             # Redis/Sala/Panel health checks
  git.py                  # Git status/diff/log
  health.py               # Startup diagnostic aggregator

tools/                    # CLI tools
  bootstrap_context.py    # Contexto universal modelo-agnóstico
  session_start.py        # Ciclo de vida de sesión, seed, servicios
  doctor.py               # Diagnóstico de instalación
  selftest.py             # 7 tests automatizados
  quick_scan.py           # Escaneo incremental de handoffs
  context_builder.py      # Contexto ranked desde índice
  optimize_agent.py       # Auditoría completa (seed, memoria, seguridad)
  optimize_memento.py     # Motor TF-IDF, grafo semántico, dedup
  export_memory.py        # Exportar memoria a markdown/json/context
  init_project.py         # Inicializar estructura en cliente nuevo
  clean_workspace.py      # Limpiar artefactos generados
  context_retriever.py    # Búsqueda simple por keywords
  agent_prompt.py         # Prompt neutral con contexto
  sync_memory.py          # Bridge legacy .memento → memory/

memory/graph/             # Índice compacto (no trackeado)
  memory_index.json       # Entradas {id, type, project, ts, tags, summary}
  index_manifest.json     # Resumen: total, by_type, by_project, latest
  graph.json              # Grafo semántico (edges con peso)

projects/<proyecto>/      # Handoffs por proyecto (no trackeado)
  HANDOFF_YYYY-MM-DD_*.md

panel_server.py           # Dashboard HTTP (puerto 8766)
sala.py                   # Sala de mensajes HTTP+Redis (puerto 8767)
memento_cli.py            # CLI interactivo (memento>)
```

## Formato compacto de memoria

```json
{
  "id": "h_HANDOFF_2026-06-23_141003_agent_optimizer",
  "type": "HANDOFF",
  "project": "adherence",
  "ts": "2026-06-23",
  "path": "projects/adherence/HANDOFF_2026-06-23_141003_agent_optimizer.md",
  "summary": "# HANDOFF - ...",
  "tags": ["adherence", "setup"],
  "keywords": ["termux", "install", "client"],
  "score": 0.0,
  "embedding": []
}
```

## Seguridad

- No commitear: `.agent_context/START_CONTEXT.md`, `.agent_context/secure/*`, `memory/graph/*.json`, `.memento/`, `projects/*/HANDOFF_*.md`
- No exponer secretos, vault, tokens
- No `FLUSHALL` en Redis sin instrucción explícita
- `USER_CONTEXT.md` ignorado por Git automáticamente

## Integración de memoria en proyecto cliente

```bash
# Exportar memoria a docs del cliente
python3 tools/export_memory.py --format markdown --output docs/memory_export.md

# O en formato JSON para procesamiento
python3 tools/export_memory.py --format json --output docs/memory.json
```

## Instalación limpia

```bash
python3 tools/doctor.py --startup --no-services
python3 tools/selftest.py
python3 tools/clean_workspace.py --force
```
