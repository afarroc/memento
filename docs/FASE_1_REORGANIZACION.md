# MementoBloom — Fase 1: Reorganización Arquitectónica

**Fecha**: 2026-06-23  
**Estado**: Beta lista  
**Commit base**: `e63c2c9`  
**Alcance**: Transformación de MementoBloom de proyecto standalone a herramienta de memoria cliente

---

## 1. Resumen Ejecutivo

MementoBloom se reorganizó completamente para funcionar como **herramienta de memoria histórica instalada dentro del proyecto cliente**, no como un proyecto independiente. La arquitectura ahora soporta dos modos de operación:

- **Modo desarrollo**: MementoBloom se desarrolla a sí mismo (proyecto `mementobloom`)
- **Modo cliente**: MementoBloom se instala como subdirectorio en un proyecto cliente y gestiona la memoria de ese proyecto

### Cambios clave

| Cambio | Antes | Después |
|---|---|---|
| Detección de proyecto | Hardcodeado `mementobloom` | Automático por `workspace_root()` |
| Rutas de datos | Absolutas o relativas a `ROOT` | Relativas a `WS_ROOT` (workspace activo) |
| Seed del agente | Genérico | Inyecta `project: <nombre>` en frontmatter y cuerpo |
| Aislamiento | No estricto | Un agente = un proyecto |
| Instalador | Interactivo, modo único | `--auto`, detección `.git`, modo cliente/desarrollo |
| Herramientas | 7 herramientas base | 10 herramientas (agregó `init_project`, `export_memory`, `clean_workspace`) |
| Empaquetado | No disponible | `pyproject.toml` para `pip install -e` |

---

## 2. Arquitectura: ROOT vs WS_ROOT

### Concepto fundamental

```
┌─────────────────────────────────────────────────────────────┐
│  ROOT (instalación de Memento)                              │
│  /ruta/cliente/mementobloom/                                │
│  - Código fuente                                             │
│  - Templates de agente (00-core, 10-context, 20-memory...)   │
│  - Herramientas CLI (tools/)                                │
│  - Scripts de instalación                                   │
│  - Archivos de configuración del tool                       │
└─────────────────────────────────────────────────────────────┘
                        ↓  MEMENTO_WORKSPACE (env var)
┌─────────────────────────────────────────────────────────────┐
│  WS_ROOT (workspace activo = proyecto cliente)              │
│  /ruta/cliente/                                             │
│  - .agent_context/ (PROJECT_META, seed, contexto)           │
│  - .memento/ (runtime, pids, logs)                          │
│  - memory/graph/ (índice JSON, manifest, grafo)             │
│  - projects/<cliente>/ (handoffs por proyecto)              │
│  - uploads/                                                 │
└─────────────────────────────────────────────────────────────┘
```

### Detección automática de ROOT

El installer (`memento_install`) detecta el modo de operación:

```bash
if [[ -n "${MEMENTO_WORKSPACE:-}" ]]; then
  # Usuario setea el workspace explícitamente
  ROOT="$MEMENTO_WORKSPACE"
elif [[ -d "$MEMENTO_DIR/.git" ]] && [[ ! -d "$(cd "$MEMENTO_DIR/.." && pwd)/.git" ]]; then
  # Modo desarrollo: mementobloom tiene .git propio, el padre no
  ROOT="$MEMENTO_DIR"
else
  # Modo cliente: mementobloom es subdirectorio de un repo cliente
  ROOT="$(cd "$MEMENTO_DIR/.." && pwd)"
fi
```

### `workspace_root()` — Fuente única de verdad

```python
# core/paths.py
def detect_workspace_root() -> Path:
    if ENV_WORKSPACE:
        return Path(ENV_WORKSPACE).expanduser().resolve()
    return ROOT.resolve()

def workspace_root() -> Path:
    return detect_workspace_root()
```

**Uso en código**:
```python
from core.paths import ROOT, workspace_root

# ROOT = instalación de Memento (código, templates)
# WS_ROOT = proyecto activo (datos, memoria, handoffs)
WS_ROOT = workspace_root()
```

---

## 3. Modos de Operación

### 3.1 Modo Desarrollo

**Cuándo**: Estás dentro del repo `mementobloom` y quieres desarrollar la herramienta sobre sí misma.

```bash
cd /Volumes/Macintosh\ HD\ -\ Datos/mementobloom

# Sin MEMENTO_WORKSPACE seteado
python3 tools/session_start.py --quick --limit 8

# Con agente externo
MEMENTO_AGENT_CMD="kilo run --dir ." python3 tools/session_start.py --launch-agent
```

**Comportamiento**:
- `workspace_root()` → `/Volumes/Macintosh HD - Datos/mementobloom`
- Proyecto detectado: `mementobloom`
- Seed: `project: mementobloom`
- Datos: `.agent_context/`, `memory/graph/`, `projects/mementobloom/` dentro del repo

### 3.2 Modo Cliente

**Cuándo**: MementoBloom está instalado como subdirectorio en un proyecto cliente.

```bash
cd /ruta/proyecto_cliente
./mementobloom/memento_start --quick --limit 8

# Con agente externo
MEMENTO_AGENT_CMD="kilo run --dir ." ./mementobloom/memento_start --launch-agent
```

**Comportamiento**:
- `workspace_root()` → `/ruta/proyecto_cliente`
- Proyecto detectado: `proyecto_cliente` (nombre del directorio padre)
- Seed: `project: proyecto_cliente`
- Datos: `.agent_context/`, `memory/graph/`, `projects/proyecto_cliente/` en el proyecto cliente

### 3.3 Comparación

| Aspecto | Modo Desarrollo | Modo Cliente |
|---|---|---|
| ROOT | `/ruta/mementobloom/` | `/ruta/cliente/mementobloom/` |
| WS_ROOT | `/ruta/mementobloom/` | `/ruta/cliente/` |
| Proyecto | `mementobloom` | `<nombre_cliente>` |
| Seed | `project: mementobloom` | `project: <cliente>` |
| Memoria | `memory/graph/memory_index.json` | `<cliente>/memory/graph/memory_index.json` |
| Handoffs | `projects/mementobloom/` | `projects/<cliente>/` |

---

## 4. Herramientas Disponibles

### 4.1 Herramientas base

| Herramienta | Comando | Propósito |
|---|---|---|
| `bootstrap_context.py` | `python3 tools/bootstrap_context.py --print` | Contexto universal modelo-agnóstico |
| `doctor.py` | `python3 tools/doctor.py --startup` | Diagnóstico de instalación |
| `selftest.py` | `python3 tools/selftest.py` | 7 tests automatizados |
| `session_start.py` | `python3 tools/session_start.py --quick` | Ciclo de vida de sesión, seed, contexto |
| `quick_scan.py` | `python3 tools/quick_scan.py <HANDOFF>` | Escaneo incremental de handoffs al índice |
| `context_builder.py` | `python3 tools/context_builder.py --limit 12` | Contexto ranked desde índice |
| `optimize_agent.py` | `python3 tools/optimize_agent.py --context` | Auditoría completa (seed, memoria, seguridad) |
| `optimize_memento.py` | `python3 tools/optimize_memento.py --rebuild` | Motor TF-IDF, grafo semántico, dedup |

### 4.2 Herramientas nuevas (Fase 1)

| Herramienta | Comando | Propósito |
|---|---|---|
| `init_project.py` | `python3 tools/init_project.py` | Inicializa estructura `.agent_context` en cliente nuevo |
| `export_memory.py` | `python3 tools/export_memory.py --format markdown` | Exporta memoria a markdown/json/context para integrar en docs del cliente |
| `clean_workspace.py` | `python3 tools/clean_workspace.py --dry-run` | Limpia artefactos generados (seed, contexto, runtime) con backup |

### 4.3 Wrappers de cliente

Después de `memento_install`, el cliente tiene wrappers en `.memento/bin/`:

| Wrapper | Tool subyacente |
|---|---|
| `memento-bootstrap_context` | `bootstrap_context.py` |
| `memento-doctor` | `doctor.py` |
| `memento-selftest` | `selftest.py` |
| `memento-quick_scan` | `quick_scan.py` |
| `memento-context_builder` | `context_builder.py` |
| `memento-session_start` | `session_start.py` |
| `memento-optimize_agent` | `optimize_agent.py` |
| `memento-export_memory` | `export_memory.py` |
| `memento-init_project` | `init_project.py` |
| `memento-clean_workspace` | `clean_workspace.py` |

Script de inicio:
```bash
./memento-start
```

---

## 5. Sistema de Memoria (3 capas)

### 5.1 Capa 1: Archivos de contexto

| Archivo | Ruta | Propósito | Trackeable |
|---|---|---|---|
| `PROJECT_META.md` | `.agent_context/PROJECT_META.md` | Meta del proyecto | ✅ |
| `USER_CONTEXT.md` | `.agent_context/secure/USER_CONTEXT.md` | Contexto local sensible | ❌ |
| `START_CONTEXT.md` | `.agent_context/START_CONTEXT.md` | Contexto regenerable | ❌ |

### 5.2 Capa 2: Handoffs

```
projects/<proyecto>/HANDOFF_YYYY-MM-DD_<descripcion>.md
```

- Formato Markdown con frontmatter YAML
- Contiene: problema, solución, decisiones, próximos pasos
- Generados al final de cada sesión
- No trackeables por Git

### 5.3 Capa 3: Índice JSON

```json
{
  "id": "h_HANDOFF_2026-06-23_143122_agent_optimizer",
  "type": "HANDOFF",
  "project": "mementobloom",
  "ts": "2026-06-23",
  "path": "projects/mementobloom/HANDOFF_...",
  "summary": "# HANDOFF - ...",
  "tags": ["mementobloom", "optimization"],
  "keywords": ["termux", "install", "client"],
  "score": 0.0,
  "embedding": []
}
```

**Ubicación**: `memory/graph/memory_index.json`  
**Manifest**: `memory/graph/index_manifest.json`  
**Backup**: `memory_index.json.bak_<timestamp>`

### 5.4 Motor de búsqueda

- TF-IDF bilingüe (ES + EN)
- Grafo semántico con edges ponderados
- BM25-like scoring
- Boost por proyecto y recencia

---

## 6. Ciclo de Vida de Sesión

### 6.1 Flujo de arranque

```
1. Leer .agent_context/PROJECT_META.md
2. Leer .agent_context/secure/USER_CONTEXT.md (si existe)
3. Leer .agent_context/START_CONTEXT.md (si existe)
4. Ejecutar python3 tools/bootstrap_context.py --print
5. Leer handoffs recientes del proyecto activo
6. Verificar git status y servicios
7. Generar/actualizar seed del agente (agent-main.md)
8. Continuar desde último handoff relevante
```

### 6.2 Seed del agente

El archivo `.agent_context/agent/agent-main.md` es generado dinámicamente por `session_start.py`:

```markdown
---
description: Curador de memoria histórica del proyecto
project: <nombre_proyecto>
mode: primary
model: any
steps: 25
---
<!-- generated-hash: <hash> -->

# Agente de Memoria — Proyecto: <nombre_proyecto>

Eres el agente de memoria histórica del proyecto **<nombre_proyecto>**.

## Semilla inicial
<contenido de init.md>

## Instrucciones progresivas cargadas
### .agent_context/agent/instructions/00-core.md OK
### .agent_context/agent/instructions/10-context.md OK
### .agent_context/agent/instructions/20-memory.md OK
...

## Memoria compacta actual
- Index entries: <N>
- [<id>] <type> project=<project> ts=<ts> path=<path> — <summary>
```

### 6.3 Cierre de sesión

```bash
# Generar handoff
python3 tools/optimize_agent.py --handoff --index

# Escanear handoffs nuevos
python3 tools/quick_scan.py projects/<proyecto>/HANDOFF_*.md

# Sincronizar memoria (si hay legacy)
python3 tools/sync_memory.py
```

---

## 7. Instalación

### 7.1 Modo automático (cliente)

```bash
cd /ruta/proyecto_cliente

# Clonar memento como subdirectorio
git clone https://github.com/afarroc/memento.git mementobloom

# Ejecutar instalador
bash mementobloom/memento_install --auto
```

### 7.2 Modo manual (desarrollo)

```bash
cd /ruta/mementobloom

# Instalar dependencias
pip install -r requirements.txt

# Inicializar estructura
python3 tools/init_project.py

# Verificar
python3 tools/selftest.py
python3 tools/doctor.py --startup
```

### 7.3 Lo que hace el instalador

1. Detecta modo (desarrollo vs cliente) por `.git` y `MEMENTO_WORKSPACE`
2. Crea entorno virtual (`venv/`)
3. Instala dependencias de `requirements.txt`
4. Instala `mementobloom` como paquete editable (`pip install -e .`)
5. Crea wrappers en `.memento/bin/`
6. Crea `memento-start` script
7. Sanea datos heredados (amnesia limpia)
8. Crea/verifica `.agent_context/` y estructura de directorios
9. Configura `USER_CONTEXT.md` básico
10. Detecta CLI (kilo, claude, code...)
11. Actualiza `.gitignore` con reglas de exclusión
12. Prepara contexto inicial de sesión
13. Genera seed del agente

### 7.4 Archivos generados por el instalador

| Archivo | Propósito |
|---|---|
| `.memento/bin/memento-*` | Wrappers de herramientas |
| `memento-start` | Script de inicio rápido |
| `.agent_context/secure/USER_CONTEXT.md` | Contexto de usuario |
| `.agent_context/secure/AGENT_CMD.env` | Comando de agente externo |
| `.agent_context/agent/agent-main.md` | Seed generado dinámicamente |
| `.agent_context/START_CONTEXT.md` | Contexto de inicio |
| `.gitignore` | Reglas de exclusión actualizadas |

---

## 8. Validación y Pruebas

### 8.1 Suite de tests

```bash
python3 tools/selftest.py
```

**7 tests**:
1. `quick_scan_empty_workspace` — Escaneo en workspace vacío
2. `bootstrap_no_services` — Bootstrap sin servicios
3. `doctor_startup_no_services` — Doctor sin servicios
4. `index_manifest` — Manifest de índice
5. `gitignore_rules` — Reglas de .gitignore
6. `no_hardcoded_workspace_in_core_tools` — Sin paths hardcodeados
7. `context_retriever_search` — Búsqueda en índice

### 8.2 Doctor de salud

```bash
python3 tools/doctor.py --startup
```

Verifica:
- `PROJECT_META.md` existe y es trackeable
- `USER_CONTEXT.md` opcional
- `START_CONTEXT.md` opcional
- `agent/init.md` existe
- `agent/agent-main.md` existe
- `memory_index.json` existe
- Servicios (Redis, Sala, Panel)

### 8.3 Prueba en proyecto cliente

```bash
cd /Volumes/Macintosh\ HD\ -\ Datos/adherence_test

# Instalar
bash mementobloom/memento_install --auto

# Verificar
./mementobloom/memento_start --quick --limit 3

# Resultado esperado:
# - Workspace: .
# - Project: adherence_test (NO mementobloom)
# - Agent seed: ready
# - Memory index: 0 entries (limpio)
```

### 8.4 Validaciones realizadas

| Validación | Resultado |
|---|---|
| selftest | 7/7 OK |
| doctor | OK |
| bootstrap_context | Funcional en ambos modos |
| session_start --quick | Proyecto correcto en ambos modos |
| quick_scan | Indexa en WS_ROOT correctamente |
| export_memory | Exporta memoria del cliente |
| clean_workspace | Limpia artefactos del cliente |
| Seed generation | `project: <nombre>` en frontmatter |
| Installer | Funciona en modo cliente y desarrollo |
| memento-start | Detecta parent `.git` correctamente |

---

## 9. Archivos Modificados/Creados

### 9.1 Core

| Archivo | Cambios |
|---|---|
| `core/paths.py` | Agregado `detect_project_name()`, `workspace_root()` como fuente única |
| `core/index.py` | Fix `LEGACY_INDEX_PATH`; `resolve_index_path` usa workspace |
| `core/services.py` | `HEALTH_CACHE_PATH` en `.memento_runtime/` del workspace |

### 9.2 Herramientas

| Archivo | Cambios |
|---|---|
| `tools/session_start.py` | `INDEX_PATH = default_index_path()`; seed inyecta `project`; `ONBOARDED` marker |
| `tools/optimize_agent.py` | Datos en `WS`, código en `ROOT` |
| `tools/quick_scan.py` | Usa `core.paths.detect_workspace_root()` |
| `tools/context_builder.py` | `__main__` usa `workspace_root()` |
| `tools/agent_prompt.py` | Índice apunta a `workspace_root()` |
| `tools/sync_memory.py` | Paths sincronizados al workspace activo |
| `tools/export_memory.py` | **Nuevo**: exporta memoria a markdown/json/context |
| `tools/init_project.py` | **Nuevo**: inicializa estructura en cliente |
| `tools/clean_workspace.py` | **Nuevo**: limpia artefactos con backup |
| `tools/seed_builder.py` | Eliminado path hardcodeado |
| `tools/auto_ref.py` | Eliminado filtro `mementobloom` |

### 9.3 Instalador y scripts

| Archivo | Cambios |
|---|---|
| `memento_install` | Detección inteligente ROOT; wrappers para 10 herramientas; `memento-start` respeta `MEMENTO_AGENT_CMD` |
| `memento_start` | Setea `MEMENTO_WORKSPACE`; detecta parent `.git` |
| `memento-init` | **Nuevo**: wrapper para `init_project` |
| `memento-export` | **Nuevo**: wrapper para `export_memory` |
| `memento-clean` | **Nuevo**: wrapper para `clean_workspace` |

### 9.4 Otros

| Archivo | Cambios |
|---|---|
| `panel_server.py` | Handoffs, memoria y git usan `workspace_root()` |
| `memento_cli.py` | `WS_ROOT = workspace_root()` |
| `handoff_gen.py` | Default workspace relativo |
| `vault_setup.py` | Eliminado source `vscode` con path absoluto |
| `vault_manager.py` | Eliminado source `vscode` |
| `README.md` | Actualizado con arquitectura ROOT/WS_ROOT |
| `PROJECT_META.md` | Generalizado a "proyecto" |
| `pyproject.toml` | **Nuevo**: empaquetado editable |

---

## 10. Decisiones Técnicas

### 10.1 ¿Por qué ROOT vs WS_ROOT?

Separar la instalación del tool de los datos del proyecto permite:
- Instalar memento una sola vez y usarlo en múltiples proyectos
- No mezclar código del tool con datos del cliente
- Actualizar memento sin afectar datos de clientes
- Clonar/backupear el proyecto cliente sin incluir el tool

### 10.2 ¿Por qué `MEMENTO_WORKSPACE` como env var?

- Estándar de facto en herramientas de CLI
- No requiere configuración de archivo
- Fácil de setear en wrappers bash
- Compatible con cualquier shell
- Override explícito para casos edge

### 10.3 ¿Por qué detección por `.git`?

- El directorio padre del cliente es el workspace natural
- `.git` es el indicator más confiable de "raíz de proyecto"
- No requiere configuración adicional
- Funciona para git, mercurial, etc. (futuro)

### 10.4 ¿Por qué seed con `project:` en frontmatter?

- Aislamiento estricto: el agente sabe en qué proyecto está
- Frontmatter YAML es parseable por cualquier LLM
- Visible en el archivo para debugging
- Permite validación temprana de identidad

---

## 11. Limitaciones Conocidas

### 11.1 Bloqueantes resueltos

| Issue | Estado | Solución |
|---|---|---|
| Paths absolutos hardcodeados | ✅ | `workspace_root()` en todos los tools |
| Seed sin identidad de proyecto | ✅ | `project: <nombre>` en frontmatter |
| Installer modo único | ✅ | Detección `.git` + `MEMENTO_WORKSPACE` |
| Falta de herramientas de gestión | ✅ | `init_project`, `export_memory`, `clean_workspace` |
| Sin empaquetado | ✅ | `pyproject.toml` |
| Heredoc syntax error | ✅ | Terminadores sin indentación |

### 11.2 Issues pendientes (no bloqueantes)

| Issue | Impacto | Workaround |
|---|---|---|
| `kilo run --auto` sin mensaje falla | Bajo | Usar `kilo run --dir .` (interactivo) |
| Contexto largo en `-i` puede romper shell | Bajo | Usar archivo temporal |
| Panel NO en algunas configuraciones | Bajo | No es crítico para funcionamiento |

---

## 12. Próxima Fase

### 12.1 Objetivos

1. **Versionado de memento** — Actualizaciones automáticas en clientes
2. **Instalador guiado** — Para usuarios no avanzados
3. **Paquetización** — PyPI, Homebrew, npm wrapper
4. **Integración con APIs de IAs** — OpenAI, Anthropic, Google, Ollama

### 12.2 Roadmap propuesto

#### Fase 2: Versionado y actualizaciones

- [ ] Sistema de versionado semántico (`mementobloom --version`)
- [ ] CLI `memento-update` para actualizar instalaciones cliente
- [ ] Changelog automático entre versiones
- [ ] Migración de datos entre versiones (si hay breaking changes)
- [ ] Notificación de actualizaciones disponibles

#### Fase 3: Instalador guiado

- [ ] Interfaz interactiva mejorada (menús claros)
- [ ] Detección automática de entorno (venv, pip, python)
- [ ] Configuración de `MEMENTO_WORKSPACE` con wizard
- [ ] Selección de CLI/agente con preview
- [ ] Validación post-instalación paso a paso
- [ ] Documentación integrada en el installer

#### Fase 4: Paquetización

- [ ] Publicar en PyPI (`pip install mementobloom`)
- [ ] Homebrew tap
- [ ] npm package (`npx mementobloom`)
- [ ] Docker image
- [ ] GitHub releases con binarios precompilados
- [ ] Script de actualización `memento-update`

#### Fase 5: Integración con APIs de IAs

- [ ] Módulo `core/llm.py` con interfaz unificada
- [ ] Soporte para: OpenAI GPT, Anthropic Claude, Google Gemini, Ollama local
- [ ] Configuración por archivo (`config/llm.json`) o env vars
- [ ] Fallback automático entre proveedores
- [ ] Context window optimization (truncado inteligente)
- [ ] Embeddings locales (sentence-transformers) como fallback
- [ ] Cache de respuestas para reducir costo

### 12.3 Consideraciones técnicas

- **Backward compatibility**: Mantener compatibilidad con instalaciones existentes
- **Data migration**: Si cambian formatos de índice/handoff, proveer migración automática
- **Security**: Nunca exponer API keys en logs o contexto
- **Privacy**: Los datos del cliente nunca salen de su workspace
- **Offline-first**: Funcionar sin conexión (Redis local, embeddings locales)

---

## 14. Checklist de Beta

- [x] Arquitectura dual ROOT/WS_ROOT implementada
- [x] Detección automática de workspace
- [x] Seed del agente con identidad de proyecto
- [x] Aislamiento estricto por proyecto
- [x] 10 herramientas funcionales
- [x] Instalador automático (`--auto`)
- [x] `pyproject.toml` para empaquetado
- [x] selftest 7/7 OK
- [x] doctor OK
- [x] Prueba en proyecto cliente (`adherence_test`)
- [x] Documentación README actualizada
- [x] Wrappers de cliente (`.memento/bin/`)
- [x] Script `memento-start`
- [x] Validación de rutas sin hardcoding
- [x] Backup automático en `clean_workspace`
- [x] Exportación de memoria

---

*Documento generado: 2026-06-23*  
*Fase: 1 — Reorganización Arquitectónica*  
*Estado: Beta lista*  
*Siguiente fase: Versionado, instalador guiado, paquetización, APIs de IAs*
