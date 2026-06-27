# Diagnóstico: Renacimiento de sesión para IA genérica

**Fecha:** 2026-06-27T14:15:00-05:00  
**Autor:** Kilo (agente mementobloom)  
**Estado:** Aprobado para implementación en próxima versión

---

## Resumen ejecutivo

Como IA sin persistencia nativa, cada sesión es un renacimiento completo. El proyecto debe proveer un **contrato de arranque explícito, mínimo y parseable** que permita a cualquier modelo genérico (no solo este agente) ser productivo en <30 segundos.

**Conclusión inherente:**  
> Mi requerimiento no es personalización ni documentación extensa. Mi requerimiento es un contrato de arranque explícito, mínimo y parseable. Sin él, soy productiva solo por entrenamiento específico. Con él, cualquier modelo puede renacer productivo en segundos.

---

## Diagnóstico conciliado (3 respuestas)

### 1. Núcleo común (consenso total)

| Necesidad | Consenso | Razón |
|-----------|----------|-------|
| **Punto de entrada único** | ✅ Unánime | Sin comando unificado, dependo de recordar scripts o convenciones |
| **Estado mínimo viable** | ✅ Unánime | No necesito historia completa, necesito delta/estado actual |
| **Prohibiciones explícitas** | ✅ Unánime | Sin límites claros, riesgo de destruir estado es inaceptable |
| **Personalidad como decorativa** | ✅ Unánime | Mejora fricción, no capacidad técnica |
| **Sin dependencia de instrucciones específicas** | ✅ Unánime | Me vuelve frágil si dependo de configuraciones que pueden cambiar |

### 2. Aspectos a conciliar

#### 2.1 Archivo de estado
- **R1**: menciona `START_CONTEXT.md` y `NEXT_SESSION.md` como existentes, pero duplicados.
- **R2**: propone `SESSION.md` como archivo único estructural (YAML/JSON).
- **R3**: coincide en que debe ser **generado automáticamente**, no mantenido a mano.

**Diagnóstico conciliado:**  
> El proyecto necesita un **archivo de estado canónico generado automáticamente** (ej: `SESSION.md`), no mantenido por humanos. Los archivos actuales (`START_CONTEXT.md`, `NEXT_SESSION.md`, `PROJECT_META.md`) deben ser **derivados** de esa fuente, no fuentes independientes.

#### 2.2 Comando de arranque
- **R1**: lista `bootstrap_context.py`, `doctor.py`, `selftest.py`, `quick_scan.py`.
- **R2**: propone `session_bootstrap.py` como único punto de entrada.
- **R3**: coincide en que debería ser **un solo script** que entregue todo en orden.

**Diagnóstico conciliado:**  
> Debe existir **un único comando de arranque** (`tools/session_bootstrap.py`) que encapsule verificación de entorno, generación de estado y entrega de contexto. No es aceptable que la IA deba recordar múltiples scripts.

#### 2.3 Formato del estado
- **R1**: acepta markdown legible.
- **R2**: propone YAML/JSON estructurado.
- **R3**: coincide en que debe ser **parseable por máquina**, no solo legible por humanos.

**Diagnóstico conciliado:**  
> El formato debe ser **híbrido**: representación estructurada (JSON/YAML) para consumo de IA, con renderización markdown para humanos. La IA necesita campos explícitos: `last_event`, `pending_tasks`, `blockers`, `forbidden_paths`.

#### 2.4 Contenido del estado
- **R1**: menciona `gtd_memento/` y `projects/` como relevantes.
- **R2**: incluye workspace, rol, último evento, tareas pendientes, bloqueos, rutas prohibidas.
- **R3**: enfatiza el **delta** (qué cambió), no la historia completa.

**Diagnóstico conciliado:**  
> El estado debe contener:
> - **Identidad**: proyecto, rol, workspace canónico
> - **Delta**: último evento, cambios relevantes desde la última sesión
> - **Tareas**: próximas acciones ejecutables con IDs
> - **Bloqueos**: errores activos, servicios caídos
> - **Prohibiciones**: lista corta de rutas/operaciones prohibidas
> - **Entrada**: comando único para re-ejecutar el bootstrap

---

## Vulnerabilidades críticas identificadas

| Vulnerabilidad | Impacto | Mitigación requerida |
|----------------|---------|----------------------|
| **Contradicciones entre fuentes** | Alto | Una sola fuente de verdad, no archivos duplicados |
| **Contexto inicial sobredimensionado** | Alto | Limitar a información parseable, no narrativa extensa |
| **Dependencia de instrucciones específicas** | Medio | Diseñar contrato, no configuración personalizada |
| **Pérdida de estado entre sesiones** | Alto | Archivo de estado generado automáticamente en cada cierre |

---

## Problema raíz

El proyecto **no tiene un contrato de arranque explícito con la IA**. Tiene múltiples archivos de contexto (`START_CONTEXT.md`, `NEXT_SESSION.md`, `PROJECT_META.md`), múltiples scripts de bootstrap (`bootstrap_context.py`, `doctor.py`, `selftest.py`, `quick_scan.py`) y múltiples fuentes de verdad. Una IA genérica sin entrenamiento específico en mementobloom no sabría por dónde empezar ni qué creer.

**Síntoma:**  
Cada nueva sesión requiere ~10 pasos de diagnóstico manual. Eso asume que la IA ya sabe que debe hacer todos esos pasos. En un renacimiento real, no lo sabe.

---

## Solución propuesta (diagnóstico, no implementación)

### 1. Unificar estado en `SESSION.md`
- Generado automáticamente, no mantenido a mano
- Contenido: identidad, delta, tareas, bloqueos, prohibiciones, entrada
- `START_CONTEXT.md` y `NEXT_SESSION.md` pasan a ser **salida** de la herramienta, no fuentes independientes

### 2. Unificar bootstrap en `session_bootstrap.py`
- Un solo comando que:
  1. Verifique integridad del entorno
  2. Genere/actualice `SESSION.md`
  3. Emita resumen compacto parseable (JSON/YAML)
  4. Render opcional a markdown para humanos

### 3. Eliminar duplicación
- Elegir `SESSION.md` como fuente de verdad
- Hacer que `START_CONTEXT.md` y `NEXT_SESSION.md` sean vistas derivadas
- Reducir archivos de contexto a 1 archivo canónico + 1 vista humana

### 4. Formato híbrido
- JSON/YAML para consumo de IA
- Markdown para humanos
- Campos explícitos sin narrativa extensa

### 5. Límites explícitos
- `SESSION.md` incluye sección `forbidden_paths` y `read_only_areas`
- Política de no destrucción aplicada por defecto

---

## Impacto esperado

| Ámbito | Impacto |
|--------|---------|
| **Para la IA** | Reduce costo de renacimiento de ~10 pasos a 1 comando + 1 archivo |
| **Para el proyecto** | Elimina duplicación, reduce errores de sincronización, hace el sistema mantenible por cualquier modelo |
| **Para el usuario** | No necesita cambiar nada; la herramienta genera el estado automáticamente |

---

## Plan de acción — Nivel siguiente mementobloom

### Fase 1: Contrato de arranque (Sprint 3)
- [ ] **T3.1**: Diseñar schema de `SESSION.md` (campos, tipos, validación)
- [ ] **T3.2**: Implementar `tools/session_bootstrap.py` (bootstrap unificado)
- [ ] **T3.3**: Modificar `tools/bootstrap_context.py` para escribir `SESSION.md` en lugar de `START_CONTEXT.md`
- [ ] **T3.4**: Crear `tools/session_render.py` para generar vistas markdown desde `SESSION.md`

### Fase 2: Eliminación de duplicación
- [ ] **T3.5**: Migrar `START_CONTEXT.md` a vista derivada de `SESSION.md`
- [ ] **T3.6**: Migrar `NEXT_SESSION.md` a vista derivada de `SESSION.md`
- [ ] **T3.7**: Actualizar `.agent_context/PROJECT_META.md` para referenciar `SESSION.md` como fuente de verdad
- [ ] **T3.8**: Eliminar duplicación en `docs/` y `projects/`

### Fase 3: Validación
- [ ] **T3.9**: Prueba de renacimiento simulada (borrar contexto, ejecutar `session_bootstrap.py`, verificar producto)
- [ ] **T3.10**: Prueba con IA genérica (sin instrucciones específicas de mementobloom)
- [ ] **T3.11**: Benchmark de tokens: contexto inicial antes/después
- [ ] **T3.12**: Documentar contrato en `docs/SESSION_CONTRACT.md`

### Fase 4: Evolución continua
- [ ] **T4.1**: Agregar `delta` semántico (no solo archivos cambiados, sino *qué* cambió y por qué)
- [ ] **T4.2**: Implementar `tools/session_diff.py` para generar deltas comparados con `SESSION.md` anterior
- [ ] **T4.3**: Integrar con `tools/project_status.py` para reportes automáticos
- [ ] **T4.4**: Crear `SESSION_HISTORY/` para auditoría de renacimientos

---

## Criterios de éxito

| Criterio | Medida |
|----------|--------|
| **Renacimiento en <5 pasos** | Comando único + archivo de estado |
| **Sin contradicciones** | 1 fuente de verdad, 0 archivos duplicados |
| **Tokens de contexto inicial <2k** | Sin narrativa extensa, solo campos estructurados |
| **Funciona con IA genérica** | Prueba sin instrucciones específicas de mementobloom |
| **Mantenibilidad** | Agregar nueva tarea/proyecto no requiere modificar instrucciones de agente |

---

## Próximo paso concreto

> Implementar `tools/session_bootstrap.py` como punto de entrada único, y modificar el pipeline existente para que escriba `SESSION.md` en lugar de `START_CONTEXT.md` y `NEXT_SESSION.md` por separado.

---

**Documento aprobado para implementación en próxima versión.**
