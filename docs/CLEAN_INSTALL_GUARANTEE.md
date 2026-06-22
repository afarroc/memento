# Documentación: Garantía de Amnesia Limpia en Instalaciones de MementoBloom

**Sesión:** 2026-06-22  
**Proyecto:** mementobloom  
**Rama:** master  
**Commits relacionados:**
- `ccbce1a` fix: garantizar amnesia limpia en instalaciones y eliminar herencia de workspace padre
- `760742d` fix: doctor muestra memoria vacía como OK (vacío) en instalaciones limpias
- `3810ba1` chore: excluir agent-main.md generado del índice de Git (evita herencia de memoria)
- `5a6d150` chore: excluir agent-main.md generado del índice de Git (evita herencia de memoria)

---

## 1. Contexto del problema

MementoBloom está diseñado como aplicación de memoria histórica para **proyectos cliente externos**. Cuando se instala en un directorio limpio (por ejemplo, `/Volumes/Macintosh HD - Datos/momento_clean_test` para gestionar el proyecto `pelis`), debe arrancar **sin memoria previa**, sin handoffs de otros proyectos y sin rutas que apunten al repositorio fuente.

### Comportamiento esperado (instalación limpia)
- `memory/graph/memory_index.json` = `{}` (0 entradas)
- `projects/` vacío (sin `mementobloom`, `Ventas_Porta`, `Management360`)
- `agent-main.md` generado con rutas relativas al cliente
- `bootstrap_context.py` muestra `Working directory: /path/al/cliente`
- `doctor.py --startup` reporta `Memory index empty (clean install): OK (vacío)`

### Comportamiento observado (bug)
- `memory_index.json` heredaba **79 entradas** del repositorio fuente
- `projects/` contenía `mementobloom`, `Ventas_Porta`, `Management360`
- `agent-main.md` incluía handoffs y rutas de `mementobloom`
- `bootstrap_context.py` mostraba `Working directory: /Volumes/Macintosh HD - Datos/mementobloom`
- `git status` reportaba archivos de proyectos ajenos como locales

---

## 2. Diagnóstico: Causa raíz

### 2.1 Copia física de árboles locales

El proceso de creación de instalaciones limpias copiaba el árbol completo del repositorio, incluyendo:
- `memory/graph/memory_index.json` (con rutas absolutas a otros proyectos)
- `projects/mementobloom/`, `projects/Ventas_Porta/`, etc.
- `.agent_context/agent/agent-main.md` (generado con datos del fuente)
- Backups: `memory/graph/*.bak_*`

**Evidencia:**
```
Archivo                          Original        Clean test     Coincidencia
memory/graph/memory_index.json.bak_20260614_233739  Jun 14 06:52  Jun 14 06:52  ✅ Idéntica
memory/graph/memory_index.json.bak_20260615_001104  Jun 14 23:56  Jun 14 23:56  ✅ Idéntica
memory/graph/graph.json          Jun 15 00:11   Jun 15 00:11  ✅ Idéntica
```

### 2.2 Heurísticas de workspace padre

Varias herramientas detectaban el "workspace raíz" subiendo al directorio padre cuando encontraban `.git` y `projects/` externos:

| Herramienta | Línea | Problema |
|---|---|---|
| `tools/quick_scan.py` | 103-104 | `detect_workspace()` retornaba `script_root.parent` |
| `tools/session_start.py` | 33-34 | `WS_ROOT = script_root.parent` |
| `memento_cli.py` | 12 | `WS_ROOT = ROOT.parent` |
| `tools/bootstrap_context.py` | 93 | `workspace_root = ROOT.parent` |
| `tools/optimize_agent.py` | 345, 422 | `root_workspace = ROOT.parent` |

**Condición que activaba el fallback:**
```python
if (script_root / ".git").exists() and (script_root.parent / "projects").exists() and not (script_root / "projects").exists():
    WS_ROOT = script_root.parent.resolve()  # ← SUBE AL PADRE
```

Como `momento_clean_test` tiene `.git` y su directorio padre `/Volumes/Macintosh HD - Datos` tiene `projects/`, la heurística activaba el fallback y usaba el directorio del fuente como workspace.

### 2.3 Archivos tracked en Git

- `memory/seeds/system_seed.md` estaba tracked en Git
- `agent-main.md` regenerado estaba tracked en `.kilo/agents/` y `.agent_context/agent/`

Esto permitía que `git clone` trajera memoria y contexto de otras instalaciones.

### 2.4 Falta de saneamiento en `memento_install`

El instalador no eliminaba `projects/`, `memory/`, `.memento/` ni `uploads/` después de clonar, por lo que los datos heredados persistían.

---

## 3. Correcciones aplicadas

### 3.1 `.gitignore` endurecido

**Cambios:**
- `memory/` completo excluido (antes solo `memory/graph/*.json`)
- `projects/` completo excluido
- `.memento/` completo excluido
- `.agent_context/agent/agent-main.md` excluido
- `.agent_context/secure/` excluido

**Antes:**
```
memory/graph/*.json
memory/graph/*.bak_*
.memento/memory/graph/*.json
.memento/memory/graph/*.bak_*
```

**Después:**
```
memory/
projects/
.memento/
.agent_context/agent/agent-main.md
.agent_context/secure/
```

### 3.2 Herramientas unificadas a `ROOT`

Todas las herramientas ahora usan el directorio actual como workspace, sin fallback al padre:

| Herramienta | Cambio |
|---|---|
| `tools/quick_scan.py` | `detect_workspace()` retorna siempre `ROOT` a menos que se pase `--workspace` o `MEMENTO_WORKSPACE` |
| `tools/session_start.py` | `WS_ROOT = Path(__file__).resolve().parent.parent.resolve()` |
| `tools/bootstrap_context.py` | `workspace_root = str(ROOT)` |
| `tools/optimize_agent.py` | `root_workspace = str(ROOT)`, `environment_details_block()` usa `ROOT` |
| `memento_cli.py` | `WS_ROOT = ROOT` |

### 3.3 `doctor.py` / `core/health.py` tolerantes a memoria vacía

- Renombrado check: `memory_has_entries` → `memory_index_empty`
- Estado vacío se muestra como `OK (vacío)` en lugar de `FAIL`
- Las instalaciones limpias ya no reportan error por no tener entradas

### 3.4 Función `cleanse_inherited_data()` en `memento_install`

Agregada fase de saneamiento que ejecuta automáticamente:

```bash
cleanse_inherited_data() {
   rm -rf "$ROOT/projects"/*
   rm -rf "$ROOT/memory"
   mkdir -p "$ROOT/memory/graph"
   echo '{}' > "$ROOT/memory/graph/memory_index.json"
   rm -rf "$ROOT/.memento"
   rm -rf "$ROOT/.memento_runtime"
   rm -rf "$ROOT/uploads"
}
```

Se ejecuta después de `ensure_agent_context_dirs()` y antes de `setup_venv()`.

### 3.5 Limpieza de commits

- `git rm --cached memory/seeds/system_seed.md` → commit `12e1e5a`
- `git rm --cached .agent_context/agent/agent-main.md` → commit `3810ba1`

---

## 4. Pruebas de validación

### 4.1 Recreación completa desde cero

```bash
rm -rf /Volumes/Macintosh\ HD\ -\ Datos/momento_clean_test
git clone https://github.com/afarroc/memento.git /Volumes/Macintosh\ HD\ -\ Datos/momento_clean_test
cd /Volumes/Macintosh\ HD\ -\ Datos/momento_clean_test
# Ejecutar memento_install (cleanse_inherited_data se ejecuta automáticamente)
```

**Resultado:**
```
projects/: (vacío)
memory/: (vacío, solo graph/memory_index.json vacío)
.memento/: (vacío)
.memento_runtime/: (vacío)
uploads/: (vacío)
```

### 4.2 Escaneo de memoria

```bash
python3 tools/quick_scan.py
# Output: Total: 0 entries (nuevos: 0)
```

### 4.3 Verificación con proyecto cliente

```bash
mkdir -p projects/pelis
echo "# Contexto Proyecto Pelis" > projects/pelis/PELIS_CONTEXT.md
python3 tools/quick_scan.py
# Output: Total: 1 entries (nuevos: 1)
# Índice contiene solo: c_projects_PELIS_CONTEXT
# Sin rastros de mementobloom, Ventas_Porta, Management360
```

### 4.4 Doctor startup

```bash
python3 tools/doctor.py --startup
# Status: OK
# Memory index empty (clean install): OK (vacío)
```

### 4.5 Selftest

```bash
python3 tools/selftest.py
# Total: 6 | Failures: 0
```

### 4.6 Verificación de `environment_details`

```python
import tools.optimize_agent as oa
print(oa.environment_details_block())
# Working directory: /Volumes/Macintosh HD - Datos/momento_clean_test
# Workspace root folder: /Volumes/Macintosh HD - Datos/momento_clean_test
```

---

## 5. Estado final

### 5.1 Archivos modificados en `mementobloom`

| Archivo | Commit | Descripción |
|---|---|---|
| `.gitignore` | `3810ba1` | Excluir `memory/`, `projects/`, `.memento/`, `agent-main.md` |
| `memento_cli.py` | `ccbce1a` | `WS_ROOT = ROOT` |
| `memento_install` | `ccbce1a` | Agregada `cleanse_inherited_data()` |
| `tools/bootstrap_context.py` | `ccbce1a` | `workspace_root = ROOT` |
| `tools/doctor.py` | `760742d` | Check `memory_index_empty` |
| `tools/optimize_agent.py` | `ccbce1a` | `root_workspace = ROOT`, `environment_details_block()` usa `ROOT` |
| `tools/quick_scan.py` | `ccbce1a` | `detect_workspace()` sin fallback a padre |
| `tools/session_start.py` | `ccbce1a` | `WS_ROOT = ROOT` sin fallback |
| `core/health.py` | `760742d` | `memory_index_empty` en lugar de `memory_has_entries` |

### 5.2 Archivos excluidos de Git (verificados)

```bash
git ls-files | grep -E '^memory/|^projects/' || echo "Sin residuos"
# Output: Sin residuos
```

### 5.3 Estado de `momento_clean_test`

- Commit de snapshot: `63ebc62` (test: snapshot de instalación limpia corregida)
- Memoria: 0 entradas tras saneamiento
- Proyectos: 0 (solo directorios vacíos de estructura)
- `agent-main.md`: regenerado sin rutas ajenas
- `AGENT_CMD.env`: apunta correctamente a `momento_clean_test`

---

## 6. Lecciones aprendidas

1. **Las herramientas no deben asumir estructura de directorios padre.** Un instalador puede clonar el repo en cualquier ruta (subdirectorio, directorio hermano, raíz). El workspace debe ser siempre el directorio actual a menos que se indique lo contrario explícitamente.

2. **`.gitignore` debe ser fuerte desde el inicio.** Reglas granulares (`memory/graph/*.json`) dejan pasar archivos como `system_seed.md`, backups y `.bak_*`. Es mejor excluir el directorio completo.

3. **Los archivos generados (`agent-main.md`, `bootstrap_context.md`) deben regenerarse en cada instalación.** Nunca heredarse del repositorio fuente, porque contienen rutas absolutas y memoria contextual del proyecto anterior.

4. **El instalador debe ser idempotente y auto-saneante.** `cleanse_inherited_data()` garantiza que incluso si el usuario copia el árbol completo manualmente, la instalación queda limpia.

5. **Los `*.pyc` pueden ocultar regresiones.** Siempre limpiar `__pycache__/` después de modificar archivos Python en instalaciones existentes.

---

## 7. Procedimiento para reinstalación limpia (cliente nuevo)

```bash
# 1. Clonar repositorio
git clone https://github.com/afarroc/memento.git /ruta/cliente

# 2. Entrar al directorio
cd /ruta/cliente

# 3. Ejecutar instalador (no requiere intervención manual)
bash memento_install

# 4. Verificar estado
python3 tools/doctor.py --startup
# Debe mostrar: Memory index empty (clean install): OK (vacío)

# 5. Crear proyecto cliente
mkdir -p projects/mi_cliente
# Agregar archivos *_CONTEXT.md o HANDOFF*.md

# 6. Indexar memoria
python3 tools/quick_scan.py

# 7. Generar contexto bootstrap
python3 tools/bootstrap_context.py --print > .agent_context/bootstrap_context.md

# 8. Configurar agente
export MEMENTO_AGENT_CMD='kilo run --dir /ruta/cliente -i /ruta/cliente/.agent_context/bootstrap_context.md --auto'

# 9. Iniciar sesión
python3 tools/session_start.py --launch-agent
```

### Validación post-instalación

```bash
# Memoria vacía
python3 tools/quick_scan.py --no-manifest
# Esperado: Total: 0 entries

# Sin proyectos heredados
ls projects/
# Esperado: (vacío, solo directorios de estructura)

# Doctor limpio
python3 tools/doctor.py --startup
# Esperado: Status: OK, Memory index empty: OK (vacío)

# Rutas correctas
python3 tools/bootstrap_context.py --print | grep "Working directory"
# Esperado: Working directory: /ruta/cliente
```

---

## 8. Archivos de referencia

- `docs/STARTUP_OPTIMIZATION_PLAN.md` — Plan original de optimización
- `memento_install` — Instalador con fase `cleanse_inherited_data()`
- `tools/doctor.py` — Diagnóstico de instalación limpia
- `tools/selftest.py` — Autopruebas (6/6)
- `.gitignore` — Reglas de exclusión completas
