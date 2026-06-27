# Fase 3: Flujo de Trabajo Operativo y Gestión de Sprints

**Proyecto:** MementoBloom  
**Documento:** Metodología de sprints, organización de tareas y transición a implementación activa  
**Versión:** 1.0.0-draft  
**Fecha:** 2026-06-25  
**Estado:** Aprobado para ejecución

---

## 1. METODOLOGÍA DE GESTIÓN DE SPRINTS

### 1.1 Definición de sprint

- **Duración:** 5 días naturales (lunes a viernes).
- **Ceremonias:**
  - **Sprint Planning:** 30 min (inicio de sprint). Se revisa backlog priorizado, se asignan tareas y se define Definition of Done.
  - **Daily Sync:** 15 min (cuando hay sesión activa). Solo bloqueos y avances relevantes.
  - **Sprint Review / Demo:** 30 min (cierre de sprint). Se validan criterios de aceptación con PO.
  - **Retrospectiva:** 15 min (cierre de sprint). 1 bien, 1 mejorar, 1 acción concreta.
- **Capacidad planificada:**
  - Backend Developer: 6-8 h/día
  - DevOps: 2-4 h/día
  - QA: 2-4 h/día
  - Líder Técnico: 4-6 h/día (arquitectura, revisión, handoffs)

### 1.2 Estructura de sprint

```
Semana 1 (Sprint 0)
├─ Objetivo: Eliminar errores bloqueantes y baseline limpio
├─ Hito M1: Panel operativo en cliente
└─ Tareas: T0.1 - T0.5

Semana 1-2 (Sprint 1)
├─ Objetivo: Aislamiento y namespacing por cliente
├─ Hito M2: Instalador portable
└─ Tareas: T1.1 - T1.4

Semana 2 (Sprint 2)
├─ Objetivo: Portabilidad de instalador y dependencias
├─ Hito M3: Aislamiento verificado
└─ Tareas: T2.1 - T2.4

Semana 2-3 (Sprint 3)
├─ Objetivo: Seguridad y configuración sensible
├─ Hito M4: Seguridad endurecida
└─ Tareas: T3.1 - T3.4

Semana 3 (Sprint 4)
├─ Objetivo: Pruebas de integración multi-cliente
├─ Hito M5: Suite de pruebas verde
└─ Tareas: T4.1 - T4.4

Semana 3-4 (Sprint 5)
├─ Objetivo: Documentación y cierre de Fase 3
├─ Hito M6: Cierre de Fase 3
└─ Tareas: T5.1 - T5.4
```

---

## 2. ORGANIZACIÓN DE TAREAS (BACKLOG PRIORIZADO)

### 2.1 Backlog de Sprint 0 (Semana 1)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T0.1** | Corregir `panel_server.py`: eliminar import roto `check_tcp`, agregar `from dataclasses import dataclass`, implementar parsing de puerto por `sys.argv` | Backend | - `panel_server.py` compila sin errores.
- `session_start.py --services-only` muestra `Panel OK`.
- Endpoint `/stats` retorna JSON válido. | 2 | — |
| **T0.2** | Corregir `core/paths.py` para detectar workspace cliente automáticamente cuando falta `MEMENTO_WORKSPACE` (buscar directorio padre con `.agent_context` o `projects/`) | Backend | - `workspace_root()` retorna `/proyecto_cliente/` cuando se ejecuta desde `/proyecto_cliente/mementobloom/`.
- Test unitario mockea directorios y valida detección. | 3 | — |
| **T0.3** | Reemplazar IPs hardcodeadas (`192.168.18.59`) por variables de entorno con defaults neutros (`localhost` donde aplique) en `core/services.py`, `sala.py`, `panel_server.py` | Backend | - `REDIS_HOST` default = `localhost`.
- `SALA_PORT` y `PANEL_PORT` respetan variables de entorno.
- `doctor.py --startup` reporta uso de defaults. | 3 | — |
| **T0.4** | Hacer rutas en `memory_index.json` relativas al workspace usando `core/paths.rel()` | Backend | - Índice generado en `Ventas_Porta` no contiene rutas absolutas.
- Índice movible entre máquinas mantiene integridad. | 2 | T0.2 |
| **T0.5** | Ejecutar `selftest` y `doctor` sobre `Ventas_Porta`; capturar y resolver fallos | QA | - `selftest` pasa 100%.
- `doctor --startup` reporta 0 errores críticos.
- Se generan fixtures de prueba si aplica. | 3 | T0.1, T0.2, T0.3 |

**Hito M1 (Día 2):** Panel operativo en cliente.

---

### 2.2 Backlog de Sprint 1 (Semana 1-2)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T1.1** | Implementar prefijo de proyecto en `REDIS_KEY`: `memento_panel_items:<proyecto>` en `core/services.py`, `sala.py` y `panel_server.py` | Backend | - Cola de mensajes se namespacea por nombre de proyecto.
- Dos clientes en mismo Redis no comparten mensajes.
- Handoff generado documentando el cambio. | 4 | T0.2 |
| **T1.2** | Agregar detección de puertos libres para Sala (8767) y Panel (8766) con fallback a puertos alternativos si están ocupados | Backend | - Si puerto 8767 está ocupado, Sala usa 8768, 8769...
- Panel idem desde 8766.
- Logs informan puerto asignado. | 4 | T0.1 |
| **T1.3** | Modificar `memento_install` para generar `.gitignore` del cliente con entradas específicas de Memento sin sobrescribir las existentes | DevOps | - `memento_install` no elimina reglas previas de `.gitignore`.
- Agrega entradas nuevas solo si no existen.
- Probado en repositorio con `.gitignore` previo. | 3 | — |
| **T1.4** | Crear script `memento-configure` (CLI) que permita definir host Redis, puertos y proyecto sin editar código | Backend | - `python3 tools/configure.py --redis-host ... --sala-port ...` actualiza `.env` o variables de entorno.
- Help claro con `--help`.
- Validación de valores (enteros, hosts). | 3 | — |

**Hito M2 (Día 5):** Instalador portable funcionando en macOS host.

---

### 2.3 Backlog de Sprint 2 (Semana 2)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T2.1** | Hacer `memento_install` portable (soporta `sed -i ''` en macOS y `sed -i.bak` en Linux) | DevOps | - `memento_install --auto` ejecutado en Ubuntu 22.04 completa sin error.
- Misma salida en macOS.
- `sed` portable detecta OS. | 3 | T1.3 |
| **T2.2** | Declarar dependencias mínimas reales en `requirements.txt` (o marcar módulo de transporte Redis como opcional) | Backend | - `requirements.txt` lista dependencias activas.
- Si Redis es opcional, se indica en `README.md`.
- `pip install -r requirements.txt` funciona en entorno limpio. | 2 | — |
| **T2.3** | Crear `Dockerfile` y `docker-compose.yml` de referencia (Redis + Sala + Panel) | DevOps | - `docker compose up` levanta servicios en puertos configurables.
- README incluye instrucciones Docker.
- Imagen < 200 MB (Python slim). | 4 | T1.2, T2.1 |
| **T2.4** | Generar lockfiles (`requirements.lock`) y procedimiento de reproducible build | DevOps | - `pip freeze` exportado a `requirements.lock`.
- Script `build_package.sh` genera tarball instalable.
- Instalación desde tarball replica entorno. | 2 | T2.2 |

**Hito M3 (Día 8):** Aislamiento verificado en fixture de multi-cliente.

---

### 2.4 Backlog de Sprint 3 (Semana 2-3)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T3.1** | Mejorar `vault_manager.py`: cambiar base64 por cifrado Fernet (`cryptography`) o marcar claramente como encoding, no seguridad | Backend | - Vault con `encrypted=true` usa Fernet si `cryptography` disponible.
- Si no, warning en logs + fallback a base64.
- Documentado en `docs/FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md`. | 4 | — |
| **T3.2** | Asegurar que `.agent_context/secure/*`, `memory/graph/*.json`, `.memento/`, `projects/*/HANDOFF_*.md` estén excluidos de Git en instalaciones cliente | QA | - `git status` en cliente no muestra archivos sensibles.
- `doctor --startup` alerta si falta exclusión.
- `memento_install` actualiza `.gitignore`. | 3 | T1.3 |
| **T3.3** | Implementar validación de `.env` al arranque: `doctor.py` alerta si faltan variables críticas | Backend | - `doctor.py --startup` reporta `warn`/`error` por env vars faltantes.
- Propone valores por defecto seguros.
- No rompe arranque si faltan opcionales. | 3 | T0.3 |
| **T3.4** | Sanitizar rutas absolutas en logs y exports: todo path impreso debe ser relativo o validado con `rel()` | Backend | - `bootstrap_context.py` no imprime `/Users/...`.
- `export_memory.py` usa rutas relativas}.
- Tests unitarios validan sanitización. | 2 | T0.4 |

**Hito M4 (Día 10):** Seguridad endurecida y saneamiento de config sensible.

---

### 2.5 Backlog de Sprint 4 (Semana 3)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T4.1** | Crear fixture de cliente de prueba (`tests/fixtures/client_project/`) con estructura completa | QA | - Directorio contiene `.agent_context`, `.memento`, `memory/graph`, `projects/`.
- Script `create_fixture.sh` regenera fixture en cualquier OS.
- Fixture se incluye en repo (no en `.gitignore`). | 3 | — |
| **T4.2** | Ejecutar `session_start.py --quick` sobre fixture; validar seed, contexto y arranque de servicios sin errores | QA | - Salida muestra servicios OK.
- Seed generado es correcto (proyecto = fixture).
- Sin excepciones en logs. | 3 | T4.1, T0.1 |
| **T4.3** | Probar instalación de dos clientes distintos (`ClienteA`, `ClienteB`) compartiendo mismo Redis | QA | - No se filtran mensajes entre clientes.
- Cada cliente ve su propio `projects/<nombre>`.
- `doctor.py` reporta namespacing activo. | 4 | T1.1 |
| **T4.4** | Medir tiempo de arranque de sesión y optimizar lecturas redundantes en `bootstrap_context.py` y `session_start.py` | Backend | - Tiempo de `session_start.py --quick` < 5s.
- Sin lecturas duplicadas de `PROJECT_META.md` o `memory_index.json`.
- Métricas documentadas en handoff. | 4 | T0.5 |

**Hito M5 (Día 12):** Suite de pruebas verde y métricas baseline.

---

### 2.6 Backlog de Sprint 5 (Semana 3-4)

| ID | Tarea | Responsable | Criterios de aceptación | Horas estimadas | Dependencias |
|----|-------|-------------|------------------------|-----------------|---------------|
| **T5.1** | Actualizar `README.md` y `DEPLOYMENT.md` con flujo de instalación cliente, configuración de entorno y troubleshooting | Docs | - README enfocado en usuario cliente, no en desarrollador.
- Sección "Troubleshooting" responde a 5 errores comunes.
- Capturas de pantalla o ejemplos de comando actualizados. | 4 | T1.3, T2.1 |
| **T5.2** | Generar `docs/FASE_3_ESTABILIZACION.md` con lecciones aprendidas, limitaciones conocidas y roadmap Fase 4 | Docs | - Documento incluye retrospectiva, métricas, deuda técnica pendiente.
- Limitaciones conocidas explícitas (ej: vault base64 en fallback).
- Roadmap Fase 4 propuesto (sin comprometer fechas). | 3 | Todo Sprint 0-4 |
| **T5.3** | Crear checklist de release: `memento-doctor`, `memento-selftest`, `memento-export` para generar paquete distribuible | DevOps |- Script `release.sh` ejecuta checks y empaqueta.
- Tag `v0.2.0-stable` se genera automáticamente.
- Paquete instalable reproduce entorno. | 3 | T2.4 |
| **T5.4** | Commit de cierre de Fase 3 en cliente `Ventas_Porta` (handoff + índices + configuración) | Backend | - Commit `docs: cierre Fase 3 en Ventas_Porta`.
- Handoff `HANDOFF_2026-06-25_fase3_ventas_porta.md` generado.
- Memoria índice inicializada con contexto de proyecto. | 3 | Todo |

**Hito M6 (Día 15):** Cierre de Fase 3, release `v0.2.0-stable`, handoffs generados.

---

## 3. FLUJO DE TRABAJO OPERATIVO: TRANSICIÓN A IMPLEMENTACIÓN ACTIVA

### 3.1 Estado actual ( punto de partida )

| Aspecto | Estado |
|---------|--------|
| Plan aprobado | ✅ Sí (Fase 3) |
| Memoria de sesión | ✅ Generada (`HANDOFF_2026-06-25_memoria_sesion_fase3.md`) |
| Documentación técnica | ✅ Generada (`docs/FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md`) |
| Panel | ✅ Corregido y funcional (verificación pendiente en fixture) |
| Índice de memoria | ✅ Inicializado en `Ventas_Porta` y `mementobloom` |
| Instalador portable | ⚠️ No iniciado |
| Tests automatizados | ⚠️ `selftest` + `doctor` OK; necesita suite multi-cliente |

### 3.2 Pasos previos al Sprint 0 (antes de escribir código)

1. **Crear rama de desarrollo:**
   ```bash
   git checkout -b mementobloom/v0.2.0
   ```
2. **Configurar entorno de fixture:**
   ```bash
   python3 tools/init_project.py --workspace /tmp/test_client --force
   ```
3. **Validar baseline actual:**
   ```bash
   python3 tools/selftest.py
   python3 tools/doctor.py --startup
   python3 tools/session_start.py --services-only
   ```
4. **Generar primer handoff de sprint:**
   ```bash
   # (se hará automáticamente al cerrar la sesión)
   ```

### 3.3 Ejecución de Sprint 0 (paso a paso)

**Checklist de arranque:**

| Paso | Acción | Verificación |
|------|--------|--------------|
| 1 | Aplicar T0.1: editar `panel_server.py` | `python3 -m py_compile panel_server.py` OK |
| 2 | Aplicar T0.2: editar `core/paths.py` | Test unitario manual con `MEMENTO_WORKSPACE` vacío |
| 3 | Verificar T0.3: `grep "192.168.18.59" mementobloom/` no encuentra hardcodeos | ✅ Completado |
| 4 | Verificar T0.4: `python3 tools/doctor.py --startup` en `Ventas_Porta` | ✅ Completado |
| 5 | Ejecutar QA (T0.5): `selftest` + `doctor` | Ambos pasan en `Ventas_Porta` y fixture |

**Regla de commit en Sprint 0:**
- Un commit por tarea (o combine si son dependientes).
- Mensaje: `fix(core): <descripción> | T0.x`
- Incluir en cuerpo del commit: "Verifica: `selftest` y `doctor --startup` OK"

### 3.4 Organización del trabajo en sesiones futuras

#### 3.4.1 Inicio de sesión (protocolo obligatorio)

1. Ejecutar `python3 tools/bootstrap_context.py --print` y leer salida.
2. Leer `NEXT_SESSION.md` y último `HANDOFF_*.md` en `projects/mementobloom/`.
3. Ejecutar `git status` y `git log --oneline -5`.
4. Reportar estado en 3 líneas: servicios, memoria, pendiente principal.

#### 3.4.2 Durante la sesión

- **Una tarea activa a la vez.** No abrir múltiples frentes sin cerrar el anterior.
- **Commitear cada tarea completada** (o al menos al cambiar de contexto).
- **Actualizar `NEXT_SESSION.md`** antes de cerrar: estado actual, próxima tarea, comandos para continuar.

#### 3.4.3 Cierre de sesión (protocolo obligatorio)

1. Ejecutar `python3 tools/session_start.py --services-only`.
2. Ejecutar `python3 tools/selftest.py`.
3. Generar HANDOFF en `projects/mementobloom/HANDOFF_YYYY-MM-DD_<tipo>.md`.
4. Actualizar `NEXT_SESSION.md`.
5. Commitear cambios de documentación y memoria (código commiteado según flujo normal).

**Template mínimo de HANDOFF de cierre:**
```markdown
# HANDOFF - <Tipo de cierre>

## Datos básicos
- Proyecto: mementobloom
- Fecha/hora: YYYY-MM-DDTHH:MM:SS-05:00
- Sprint: N
- Rama: <rama actual>

## Estado
- Commit: <hash>
- Servicios: Redis OK | Sala OK | Panel OK/NO
- Tests: selftest OK/FAIL, doctor OK/WARN/ERROR

## Cambios en esta sesión
- T0.x - Descripción
- (lista de archivos modificados)

## Próximos pasos
- T<n>.x - Descripción
```

---

## 4. CRITERIOS DE AVANCE Y CONTROL

### 4.1 Indicadores de salud de sprint

| Indicador | Verde | Amarillo | Rojo |
|-----------|-------|----------|------|
| Tareas completadas vs planificadas | ≥ 80% | 50-79% | < 50% |
| `selftest` verde | Sí | Parcial | No |
| `doctor --startup` | OK | WARN | ERROR |
| Handoffs generados | 1 por sesión | 1 por 2 sesiones | 0 en última sesión |
| Deuda técnica nueva | 0 | 1-2 items | > 2 items |

### 4.2 Control de integración

- **Integración continua ligera:** Antes de cerrar cada día, ejecutar pipeline mínimo en rama de sprint:
  ```bash
  python3 tools/selftest.py && \
  python3 tools/doctor.py --startup && \
  python3 tools/session_start.py --services-only
  ```
- **Integración dura:** Antes de merge a `master`, además de lo anterior:
  - Validar en fixture de cliente.
  - Validar en cliente real `Ventas_Porta`.
  - Actualizar documentación.

---

## 5. RECURSOS DE APOYO

| Recurso | Ruta | Propósito |
|---------|------|-----------|
| Plan de Fase 3 | `docs/FASE_3_PLAN_APROBADO.md` | Plan maestro |
| Estructura y doc técnica | `docs/FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md` | Arquitectura, requisitos, protocolos |
| Flujo operativo | `docs/FASE_3_FLUJO_OPERATIVO.md` | Este documento |
| Memoria de sesión | `projects/mementobloom/HANDOFF_2026-06-25_memoria_sesion_fase3.md` | Acuerdos y decisiones |
| Próxima sesión | `.agent_context/START_CONTEXT.md` + `NEXT_SESSION.md` | Continuidad |
| Diagnóstico | `python3 tools/doctor.py --startup` | Salud del sistema |
| Pruebas | `python3 tools/selftest.py` | Validación automática |

---

## 6. PRÓXIMOS PASOS INMEDIATOS (Sprint 2)

1. Iniciar Sprint 2: portabilidad de instalador (`T2.1`), dependencias (`T2.2`), Docker (`T2.3`).
2. Verificar namespacing en fixture multi-cliente.
3. Commitear cambios pendientes de documentación y memoria cuando se solicite.

**Comando para continuar:**
```bash
python3 tools/session_start.py --services-only && \
python3 tools/selftest.py && \
python3 tools/doctor.py --startup
```
