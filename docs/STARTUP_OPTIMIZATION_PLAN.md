# Plan de optimización de arranque limpio de MementoBloom

Estado: documentado y preparado para ejecución.  
Fecha de planificación: 2026-06-21.  
Proyecto: MementoBloom.  
Objetivo: reducir redundancias de inicio de sesión y preparar un flujo robusto para instalaciones limpias sin depender de contexto personalizado.

## Alcance

Este plan cubre únicamente mejoras de funcionamiento del proyecto:

- arranque rápido
- diagnóstico de instalación
- rutas de memoria
- servicios opcionales
- auditoría compartida
- autoverificación
- continuidad ante interrupción de sesión

No incluye cambios de preferencias personales del usuario ni migración de proyectos externos.

## Progreso actualizado

Fases 0-7 ejecutadas y verificadas:

- ✅ Fase 1: módulos core compartidos (`core/paths.py`, `core/git.py`, `core/index.py`, `core/services.py`, `core/health.py`).
- ✅ Fase 2: `quick_scan.py` unificado a la ruta canónica y con flags explícitos (`--index`, `--legacy-index`, `--no-manifest`, `--json`).
- ✅ Fase 4: `bootstrap_context.py` ahora usa core, soporta `--no-services`, `--fresh-health` y `--index`.
- ✅ Fase 5: `session_start.py --quick` no modifica archivos; `generic_index` y `core.index` importados.
- ✅ Fase 6: manifiesto `index_manifest.json` y caché `.memento_runtime/health_cache.json` implementados.
- ✅ Fase 7: `doctor.py --startup` y `selftest.py` implementados; todos los tests pasan (6/6).
- ✅ docs/README actualizado con comandos de instalación limpia.
- ⏳ Pendiente menor: operación explícita de `--prepare-seed` / `--write-start-context` muy clara en `session_start.py`.
- ⏳ Pendiente menor: actualizar `tools/context_retriever.py` si consume quick_scan.

Tests verificados:
```text
OK quick_scan_empty_workspace
OK bootstrap_no_services
OK doctor_startup_no_services
OK index_manifest
OK gitignore_rules
OK no_hardcoded_workspace_in_core_tools
Total: 6 | Failures: 0
```

## Problema actual detectado

El arranque actual repite operaciones que pueden optimizarse:

1. Lectura manual de `PROJECT_META.md`, `USER_CONTEXT.md` y `START_CONTEXT.md` más ejecución de `bootstrap_context.py`, que ya resume esos archivos.
2. Ejecución de `bootstrap_context.py --print` y luego `optimize_agent.py --context`, duplicando revisiones de Git, memoria y servicios.
3. Revisión repetida de Git mediante `git status`, `git diff --stat`, `git diff` y auditorías internas.
4. Verificación repetida de Redis, Sala y Panel.
5. Lectura completa de `memory/graph/memory_index.json`, que contiene embeddings y campos no necesarios para arranque.
6. Lectura de handoffs completos cuando el resumen ya está disponible.
7. Apertura de documentos de otros proyectos cuando la tarea es MementoBloom.
8. Inconsistencia entre rutas de memoria:
   - `bootstrap_context.py` usa `memory/graph/memory_index.json`
   - `quick_scan.py` escribe en `.memento/memory/graph/memory_index.json`
   - `sync_memory.py` existe como puente manual.

## Principio de diseño

El arranque debe tener tres niveles separados:

1. **Universal**
   - Funciona para cualquier modelo, CLI o agente.
   - No depende de `optimize_agent.py`.
   - No modifica archivos.
   - No requiere Redis, Sala ni Panel.

2. **Local rápido**
   - Para uso diario en instalación ya configurada.
   - Reutiliza caché de salud.
   - No regenera seed ni contexto salvo opción explícita.

3. **Mantenimiento**
   - Auditoría profunda.
   - Regeneración de seed.
   - Reindexación.
   - Autoverificación.
   - Publicación en sala si se solicita.

## Fases de implementación

### Fase 0 — Preparación del terreno

Objetivo: evitar cambios inesperados y dejar trazabilidad.

Tareas:
- Verificar estado Git.
- Confirmar rutas críticas.
- Revisar `.gitignore`.
- No modificar `USER_CONTEXT.md`.
- No tocar Redis de forma destructiva.
- No iniciar Sala/Panel salvo instrucción explícita.

Comandos útiles:

```bash
git status --short --branch
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context
```

Criterio de aceptación:
- Se conoce el estado inicial.
- No hay cambios no deseados.
- Se identifica si `memory_index.json` está en `memory/graph/` o `.memento/memory/graph/`.

---

### Fase 1 — Crear módulos compartidos

Objetivo: eliminar duplicación entre scripts.

Nuevos módulos propuestos:

```text
core/paths.py
core/git.py
core/index.py
core/services.py
core/health.py
```

Responsabilidades:

- `core/paths.py`
  - detectar `ROOT`
  - detectar `WORKSPACE_ROOT`
  - resolver rutas relativas
  - evitar hardcodeo de `/Volumes/...`

- `core/git.py`
  - `git_status()`
  - `git_diff_stat()`
  - `latest_commit()`
  - `check_ignore()`

- `core/index.py`
  - cargar índice
  - contar por tipo/proyecto
  - obtener últimos handoffs
  - ordenar entradas
  - preparar manifiesto compacto

- `core/services.py`
  - chequear Redis
  - chequear Sala
  - chequear Panel
  - reutilizar caché de salud

- `core/health.py`
  - construir auditoría general
  - generar reporte compacto
  - servir a bootstrap, doctor y optimize_agent

Criterio de aceptación:
- `bootstrap_context.py`, `optimize_agent.py` y `session_start.py` pueden usar funciones compartidas sin cambiar comportamiento visible.
- No se introducen dependencias externas.

---

### Fase 2 — Unificar rutas de memoria

Objetivo: eliminar duplicidad `.memento/memory/graph/` vs `memory/graph/`.

Opciones recomendadas:

1. Mantener `memory/graph/memory_index.json` como ruta canónica.
2. Hacer que `quick_scan.py` acepte `--index`.
3. Agregar detección automática de índice existente.
4. Mantener compatibilidad opcional con `.memento` mediante flag explícito.

Cambios propuestos:

```bash
python3 tools/quick_scan.py --index memory/graph/memory_index.json
python3 tools/quick_scan.py --index .memento/memory/graph/memory_index.json
python3 tools/quick_scan.py --auto-index
```

Comportamiento esperado:
- Si existe `memory/graph/memory_index.json`, usarlo por defecto.
- Si no existe y existe `.memento/memory/graph/memory_index.json`, usarlo.
- Si no existe ninguno, crear `memory/graph/memory_index.json`.

Criterio de aceptación:
- `quick_scan.py` actualiza la misma ruta que lee `bootstrap_context.py`.
- `sync_memory.py` queda obsoleto o se documenta como herramienta legacy.

---

### Fase 3 — Implementar diagnóstico de instalación limpia

Objetivo: crear un único punto de diagnóstico.

Comando propuesto:

```bash
python3 tools/doctor.py --startup
```

Alternativa:

```bash
python3 tools/session_start.py --doctor
```

Checks mínimos:

- Python disponible.
- `PROJECT_META.md` existe y no está ignorado.
- `USER_CONTEXT.md` puede no existir.
- `START_CONTEXT.md` puede no existir.
- `memory/graph/` existe o puede crearse.
- `projects/` existe o puede crearse.
- `quick_scan.py` funciona con índice vacío.
- `bootstrap_context.py --print` no falla.
- `.gitignore` ignora:
  - `.agent_context/START_CONTEXT.md`
  - `.agent_context/secure/USER_CONTEXT.md`
  - `memory/graph/*.json`
  - `*HANDOFF*.md`
  - `*_CONTEXT.md`
- Redis, Sala y Panel son opcionales y no bloquean.

Salida esperada:

```text
MementoBloom Doctor
Status: OK/WARN/FAIL
Python: OK
Project meta: OK
User context: optional
Start context: optional
Memory index: OK/WARN
Git: OK/WARN
Services: Redis=OK, Sala=NO, Panel=NO
Recommendation: ...
```

Criterio de aceptación:
- Instalación limpia puede ejecutarse sin handoffs, sin `USER_CONTEXT.md`, sin Redis y sin Sala.

---

### Fase 4 — Separar bootstrap universal y auditoría de agente

Objetivo: que `bootstrap_context.py` sea el arranque universal y `optimize_agent.py` sea mantenimiento.

Cambios propuestos:

- `bootstrap_context.py`
  - no debe depender de `optimize_agent.py`
  - debe funcionar con índice vacío
  - debe soportar `--no-services`
  - debe soportar `--fresh-health`
  - debe soportar `--json`
  - debe usar rutas relativas cuando sea posible

- `optimize_agent.py`
  - debe reutilizar `core/health.py`
  - debe seguir siendo útil para auditoría del agente
  - no debe ser obligatorio para iniciar sesión

Criterio de aceptación:
- `python3 tools/bootstrap_context.py --print` funciona en instalación limpia.
- `python3 tools/optimize_agent.py --context` sigue funcionando en instalación configurada.

---

### Fase 5 — Evitar mutaciones por defecto en `session_start.py`

Objetivo: separar lectura de preparación.

Comportamiento actual a revisar:
- `session_start.py` puede escribir `START_CONTEXT.md`.
- `session_start.py` puede regenerar `agent-main.md`.

Comportamiento recomendado:

```bash
./memento_start --quick
```

Solo imprime estado.

```bash
./memento_start --prepare-seed
```

Regenera seed.

```bash
./memento_start --write-start-context
```

Escribe contexto local.

```bash
./memento_start --print
```

Prepara e imprime, manteniendo compatibilidad.

Criterio de aceptación:
- El modo rápido no genera cambios Git.
- La regeneración de seed es explícita.
- La escritura de `START_CONTEXT.md` es explícita.

---

### Fase 6 — Caché de salud y manifiesto compacto

Objetivo: reducir lecturas costosas y chequeos repetidos.

Archivos propuestos:

```text
memory/graph/index_manifest.json
.memento_runtime/health_cache.json
```

Manifiesto de índice:

- total
- by_type
- by_project
- latest_handoffs
- updated_at

Caché de salud:

- redis
- sala
- panel
- checked_at

Reglas:
- Reutilizar caché si tiene menos de 30 segundos.
- Forzar actualización con `--fresh-health`.
- No bloquear si la caché no existe.

Criterio de aceptación:
- `bootstrap_context.py` puede iniciar sin cargar todo `memory_index.json`.
- Las verificaciones de servicios no se repiten innecesariamente.

---

### Fase 7 — Autoverificación

Objetivo: validar cambios automáticamente.

Comando propuesto:

```bash
python3 tools/selftest.py
```

Tests mínimos:

- resolución de rutas
- bootstrap con índice vacío
- quick_scan con índice vacío
- doctor con servicios no disponibles
- git ignore rules
- no hardcodeo de `/Volumes/...`
- no lectura obligatoria de `USER_CONTEXT.md`

Criterio de aceptación:
- `python3 tools/selftest.py` pasa en instalación limpia.

---

### Fase 8 — Documentación y README

Objetivo: separar instalación limpia de uso avanzado.

Secciones recomendadas:

```text
Instalación mínima
Arranque rápido
Primer handoff
Servicios opcionales
Uso como agente
Mantenimiento
Solución de problemas
```

Comandos documentados:

```bash
python3 tools/doctor.py --startup
python3 tools/selftest.py
./memento_start --quick
python3 tools/bootstrap_context.py --print
python3 tools/quick_scan.py --index memory/graph/memory_index.json
```

Criterio de aceptación:
- Un modelo, CLI o persona puede instalar y arrancar sin leer instrucciones internas del agente.

## Protocolo de interrupción

Si la sesión se interrumpe o se alcanza el límite de pasos:

1. Leer este documento:

```bash
docs/STARTUP_OPTIMIZATION_PLAN.md
```

2. Leer el handoff correspondiente:

```bash
projects/mementobloom/HANDOFF_2026-06-21_1838_startup_optimization_plan.md
```

3. Verificar estado:

```bash
git status --short --branch
python3 tools/bootstrap_context.py --print
python3 tools/doctor.py --startup
```

4. Identificar la última fase completada.
5. Continuar con la siguiente fase inconclusa.
6. No reiniciar fases ya completadas salvo que fallen pruebas.
7. No ejecutar operaciones destructivas sobre Redis, memoria, handoffs o índices.
8. No commitear sin instrucción explícita.

## Orden recomendado de ejecución

1. Fase 0 — Preparación del terreno.
2. Fase 1 — Crear módulos compartidos.
3. Fase 2 — Unificar rutas de memoria.
4. Fase 3 — Implementar `doctor.py --startup`.
5. Fase 4 — Separar bootstrap y auditoría de agente.
6. Fase 5 — Evitar mutaciones por defecto en `session_start.py`.
7. Fase 6 — Caché de salud y manifiesto compacto.
8. Fase 7 — Autoverificación.
9. Fase 8 — Documentación y README.

## Criterios generales de aceptación

La implementación se considera completa cuando:

- El arranque universal funciona en instalación limpia.
- No se requiere `USER_CONTEXT.md`.
- No se requieren handoffs existentes.
- No se requiere Redis.
- No se requiere Sala.
- No se requiere Panel.
- `quick_scan.py` y `bootstrap_context.py` usan la misma ruta de índice.
- `session_start.py --quick` no modifica archivos.
- `doctor.py --startup` reporta estado sin fallar.
- `selftest.py` valida el flujo mínimo.
- README explica instalación limpia y uso avanzado por separado.

## Estado actual

- **Implementación funcional:** Fases 0-7 completadas y verificadas.
- **Pendientes menores (no bloqueantes):**
  - Refinar ayuda/comando de `session_start.py` para exponer modos de escritura explícita (`--prepare-seed`, `--write-start-context`).
  - Verificar `tools/context_retriever.py` si se requiere backend de búsqueda avanzada (actualmente usa fallback `top_entries`).
- **Tests verificados:**
```text
OK quick_scan_empty_workspace
OK bootstrap_no_services
OK doctor_startup_no_services
OK index_manifest
OK gitignore_rules
OK no_hardcoded_workspace_in_core_tools
Total: 6 | Failures: 0
```
