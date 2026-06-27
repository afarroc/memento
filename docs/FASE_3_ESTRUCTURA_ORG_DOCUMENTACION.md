# Fase 3: Estructura Organizativa y Documentación Técnica

**Proyecto:** MementoBloom  
**Documento:** Especificaciones de arquitectura, requisitos de sistema y protocolos de desarrollo  
**Versión:** 1.0.0-draft  
**Fecha:** 2026-06-25  
**Estado:** Aprobado para ejecución

---

## 1. ESTRUCTURA ORGANIZATIVA

### 1.1 Roles y responsabilidades

| Rol | Identificación | Responsabilidades principales |
|-----|----------------|------------------------------|
| **Product Owner (PO)** | Usuario Arturo | Define objetivos de cliente, aprueba planes, valida criterios de aceptación, provee contexto de usuario (`USER_CONTEXT.md`). |
| **Líder Técnico / PM** | Agente Kilo | Planifica fases, diseña arquitectura, resuelve bloqueos, valida integraciones, mantiene memoria histórica. |
| **Backend Developer** | ( Rol asignado en ejecución ) | Implementa núcleo (`core/*`), herramientas CLI (`tools/*`), correcciones de servicios y tests. |
| **DevOps / Integración** | ( Rol asignado en ejecución ) | Empaquetado, instalador portable, Docker, lockfiles, CI/CD ligero. |
| **QA / Evaluación** | ( Rol asignado en ejecución ) | Ejecuta `selftest`, `doctor`, pruebas multi-cliente, valida aislamiento y rendimiento. |
| **Documentación** | Líder Técnico + Backend | Genera y mantiene `docs/`, handoffs, `README.md`, `DEPLOYMENT.md`. |

### 1.2 Modelo de toma de decisiones

- **Decisiones técnicas:** Líder Técnico (propuesta) + Backend (implementación) → PO valida criterios de aceptación.
- **Decisiones de arquitectura:** Consenso Líder Técnico + Backend + DevOps. Si hay empate, PO define prioridad de negocio.
- **Decisiones de proceso:** Líder Técnico define flujo y sprints; PO aprueba duración y hitos.
- **Regla de oro:** Ningún cambio se fusiona sin pasar `selftest` y `doctor --startup` en al menos un entorno de prueba.

### 1.3 Comunicación y trazabilidad

| Canal | Formato | Propósito |
|-------|---------|-----------|
| `projects/mementobloom/HANDOFF_*.md` | Markdown | Memoria de sesión, handoffs, acuerdos |
| `.agent_context/START_CONTEXT.md` | Markdown | Contexto regenerable por sesión |
| `docs/FASE_*.md` | Markdown | Especificaciones técnicas permanentes |
| `NEXT_SESSION.md` | Markdown | Continuidad entre sesiones |
| `memory/graph/memory_index.json` | JSON | Índice compacto de conocimiento |
| Git (commits + tags) | Git | Versionado de código y releases |

**Regla:** Toda sesión cierra con un HANDOFF y actualiza `NEXT_SESSION.md`.

---

## 2. DOCUMENTACIÓN TÉCNICA REQUERIDA

### 2.1 Especificaciones de arquitectura

#### 2.1.1 Diagrama de componentes (texto)

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT WORKSPACE (WS_ROOT)                │
│  /proyecto_cliente/                                          │
│  ├── .agent_context/          (meta, seed, contexto)        │
│  ├── .memento/                (runtime, logs, pids)         │
│  ├── .memento_runtime/        (health_cache)               │
│  ├── memory/graph/            (índice JSON)                 │
│  ├── projects/<proyecto>/     (handoffs)                    │
│  └── mementobloom/            (código fuente instalado)     │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ MEMENTO_WORKSPACE (env var) / detección automática
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  MEMENTOBLOOM PACKAGE (ROOT)                                 │
│  ├── core/                     (paths, git, index, services)│
│  ├── tools/                    (CLI tools, entry points)    │
│  ├── panel_server.py           (dashboard HTTP)             │
│  ├── sala.py                   (sala HTTP + Redis)          │
│  ├── vault_manager.py          (credenciales)               │
│  ├── config/services.json      (endpoints externos)         │
│  └── pyproject.toml            (empaquetado)                │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ TCP / HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  SERVICIOS EXTERNOS                                          │
│  ├── Redis (localhost:6379)                             │
│  │   └── cola: memento_panel_items:<proyecto>              │
│  ├── Sala HTTP (8767)                                       │
│  └── Panel HTTP (8766)                                      │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.2 Contratos de interfaz

| Componente | Protocolo | Endpoint / Formato | Responsabilidades |
|------------|-----------|-------------------|-------------------|
| **Sala** | HTTP + Redis | `GET /stats`, `GET /messages`, `POST /send` | Transporte de mensajes entre sesiones; sin disco. |
| **Panel** | HTTP | `GET /stats`, `GET /`, `POST /api/service/start`, `POST /api/config` | dashboard de salud y control de servicios. |
| **Redis** | RESP | `PING`, cola `memento_panel_items:<proyecto>` | Broker de mensajes y health cache. |
| **Bootstrap Context** | CLI | `python3 tools/bootstrap_context.py --print` → JSON/Markdown | Contexto universal para cualquier modelo. |
| **Session Start** | CLI | `python3 tools/session_start.py --quick` | Ciclo de vida de sesión, seed, servicios. |

#### 2.1.3 Modelo de datos: índice de memoria

**Ruta canónica:** `memory/graph/memory_index.json`  
**Formato:** JSON compacto, array de entradas con schema mínimo:

```json
{
  "generated_at": "2026-06-25T12:00:00",
  "total_entries": 42,
  "entries": [
    {
      "id": "h_HANDOFF_2026-06-25_...",
      "type": "HANDOFF",
      "project": "mementobloom",
      "timestamp": "2026-06-25T10:00:00",
      "path": "projects/mementobloom/HANDOFF_....md",
      "summary": "# HANDOFF - ...",
      "tags": ["sesion", "cierre"]
    }
  ]
}
```

**Reglas:**
- Todo path almacenado debe ser relativo al `workspace_root()` (ver `core/paths.rel()`).
- No se almacenan rutas absolutas de filesystem.
- Backups automáticos en `archive/backups/memory_graph/`.

---

### 2.2 Requisitos de sistema

#### 2.2.1 Hardware / entorno de ejecución

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8 GB+ |
| Disco | 2 GB libres | 10 GB libres (para índices, vault, logs) |
| Red | Acceso a host Redis (por defecto LAN) | Redis local o accesible; puertos 8766/8767 libres |

#### 2.2.2 Software base

| Componente | Versión mínima | Notas |
|------------|----------------|-------|
| Python | 3.9 | 3.11/3.12 recomendado |
| Git | 2.30 | Para gestión de estado y versionado |
| Redis | 6.x | Servidor accesible; cliente Python no requerido (usa socket RAW) |
| Node.js / npm | 14+ | Solo para tooling local de Kilo (`.kilo/`, `.agent_context/node_modules/`) |
| Sistema operativo | macOS 12+ o Ubuntu 20.04+ | Instalador portable soporta ambos |

#### 2.2.3 Variables de entorno obligatorias / opcionales

| Variable | Obligatoria | Default | Descripción |
|----------|-------------|---------|-------------|
| `MEMENTO_WORKSPACE` | Opcional | `(vacío)` | Raíz del proyecto cliente. Si falta, se detecta automáticamente. |
| `REDIS_HOST` / `MEMENTO_REDIS_HOST` | Opcional | `localhost` (Fase 3) | Host del servidor Redis. |
| `REDIS_PORT` / `MEMENTO_REDIS_PORT` | Opcional | `6379` | Puerto Redis. |
| `REDIS_KEY` | Opcional | `memento_panel_items:<proyecto>` | Cola de mensajes; incluye namespace de proyecto. |
| `SALA_PORT` | Opcional | `8767` | Puerto de la sala HTTP. |
| `PANEL_PORT` | Opcional | `8766` | Puerto del panel HTTP. |
| `MEMENTO_START_TIMEOUT` | Opcional | `12` | Timeout de arranque de servicios (segundos). |
| `MEMENTO_MAX_UPLOAD_SIZE` | Opcional | `10485760` (10 MB) | Límite de subida en sala. |

**Regla:** En Fase 3 se eliminan defaults con IPs hardcodeadas; todo default debe ser neutro o local.

---

### 2.3 Protocolos de desarrollo

#### 2.3.1 Estrategia de ramas Git

| Rama | Propósito | Protección |
|------|-----------|------------|
| `master` | Código productivo + cliente `Ventas_Porta` | Requiere PR + `selftest` verde |
| `mementobloom/v0.2.0` | Desarrollo de Fase 3 (core, herramientas) | Requiere PR + `doctor --startup` verde |
| `feature/T<n>.x-<desc>` | Tareas individuales de sprint | Se mergea a `v0.2.0` |
| `hotfix/*` | Correcciones críticas post-release | Se mergea a `master` y `v0.2.0` |

**Regla de merge:**  
1. Ejecutar `python3 tools/selftest.py`.  
2. Ejecutar `python3 tools/doctor.py --startup`.  
3. Ejecutar `python3 tools/session_start.py --services-only`.  
4. Actualizar HANDOFF correspondiente.  
5. Merge con mensaje convencional: `type(scope): descripción`.

#### 2.3.2 Convenciones de commits

Seguir [Conventional Commits](https://www.conventionalcommits.org/):

```
fix(panel): corregir import de check_tcp y parsing de puerto
feat(redis): agregar namespacing por proyecto en cola
docs(README): actualizar flujo de instalación cliente
chore(deps): declarar dependencias mínimas en requirements.txt
test(core): agregar fixture de cliente para selftest
```

**Reglas:**
- Incluir referencia a tarea (T0.1, T1.2…) cuando aplique.
- No commitear secretos, `.env`, `vault.json`, `.agent_context/secure/*`, `memory/graph/*.json`, `.memento/`, `projects/*/HANDOFF_*.md`, `archive/`.
- Máximo 72 horas entre handoff y commit cuando haya cambios pendientes relevantes.

#### 2.3.3 Criterios de "Done"

Una tarea se considera completada cuando:

1. Código mergeado a rama objetivo.
2. `selftest` pasa sin errores.
3. `doctor --startup` retorna `{"status": "ok"}` o `warn` justificado.
4. Documentación actualizada (`docs/` o `README.md` según alcance).
5. HANDOFF generado en `projects/mementobloom/` describiendo cambios.
6. (Si aplica) Validado en fixture de cliente o entorno `Ventas_Porta`.

#### 2.3.4 Revisión de código

- Todo PR requiere al menos 1 aprobación (Backend o Líder Técnico).
- Líder Técnico actúa como revisor de arquitectura y seguridad.
- Backend revisaTests y compatibilidad.
- QA ejecuta pruebas de integración antes de merge.

#### 2.3.5 Pruebas

| Nivel | Herramienta | Cobertura objetivo |
|-------|-------------|-------------------|
| Unitarias | `pytest` | `core/*` > 80% |
| Integración | `selftest.py` + fixtures | 100% de flujos críticos |
| Sistema | `doctor.py --startup` | 100% de checks obligatorios |
| Humo | `session_start.py --quick` | Funcional en 3 entornos (macOS host, fixture, Linux contenedor) |

---

## 3. GOBIERNO Y MANTENIBILIDAD

### 3.1 Política de versionado

- Formato: `MAJOR.MINOR.PATCH[-etiqueta]`
- Ejemplo: `0.2.0-stable`, `0.2.1-hotfix`
- Cambios de Fase incrementan `MINOR`. Hotfixes incrementan `PATCH`.
- Tags en Git: `v0.2.0-stable`, `v0.2.1-hotfix`.

### 3.2 Gestión de dependencias

- **Dependencias core:** Declaradas en `requirements.txt` (sin lockfile en Fase 3; lockfile se agrega en T2.4).
- **Dependencias opcionales:** Documentadas en `requirements-dev.txt` o sección `[project.optional-dependencies]` de `pyproject.toml`.
- **Prohibido:** Agregar dependencias externas sin antes evaluar impacto en instalación cliente.

### 3.3 Seguridad operativa

| Regla | Descripción |
|-------|-------------|
| No borrar memoria | No se eliminan `memory/graph/*`, `.memento/`, `projects/*/HANDOFF_*.md` sin PO. |
| No FLUSHALL Redis | Solo se permite con instrucción explícita; namespacing reduce necesidad. |
| No commits de secretos | Bloqueado por `.gitignore` + `doctor.py` + revisión humana. |
| Rutas relativas | Todo output de herramientas usa `core/paths.rel()`; sin rutas absolutas. |

### 3.4 Ciclo de vida de documentación

| Documento | Propietario | Frecuencia de actualización | Formato |
|-----------|-------------|------------------------------|---------|
| `README.md` | Líder Técnico | Por release | Markdown |
| `DEPLOYMENT.md` | DevOps | Por cambio de instalador | Markdown |
| `docs/FASE_*.md` | Líder Técnico | Por fase | Markdown |
| `NEXT_SESSION.md` | Líder Técnico | Por sesión | Markdown |
| `projects/mementobloom/HANDOFF_*.md` | Líder Técnico | Por sesión | Markdown |
| `.agent_context/START_CONTEXT.md` | Herramienta (`bootstrap_context.py`) | Por `session_start.py` | Markdown |

---

## 4. ESPECIFICACIONES DE REQUISITOS (SRS) — RESUMEN

### 4.1 Requisitos funcionales

| ID | Requisito |
|----|-----------|
| RF-01 | El sistema debe detectar automáticamente el workspace del cliente sin depender de `MEMENTO_WORKSPACE`. |
| RF-02 | El sistema debe generar un contexto universal legible por cualquier LLM/CLI. |
| RF-03 | El sistema debe soportar handoffs y memoria compacta por proyecto cliente. |
| RF-04 | Los servicios (Redis, Sala, Panel) deben arrancar sin intervención manual tras `session_start.py --quick`. |
| RF-05 | El instalador debe funcionar en macOS y Linux sin modificaciones. |
| RF-06 | Dos clientes en misma máquina deben estar aislados (paths, seeds, colas Redis). |
| RF-07 | El usuario debe poder ejecutar `doctor.py --startup` y obtener un reporte de salud accionable. |

### 4.2 Requisitos no funcionales

| ID | Requisito |
|----|-----------|
| RNF-01 | Tiempo de arranque de sesión: < 5 segundos en fixture de prueba. |
| RNF-02 | Sin dependencias externas obligatorias (stdlib-only en capa base). |
| RNF-03 | Formato de datos legible por humanos (JSON, Markdown). |
| RNF-04 | Cobertura de tests >80% en `core/`. |
| RNF-05 | Sin rutas absolutas en archivos versionados. |

---

## 5. REFERENCIAS

- Plan de Fase 3: `docs/FASE_3_PLAN_APROBADO.md`
- Fase 1 (reorganización): `docs/FASE_1_REORGANIZACION.md`
- Plan de optimización de arranque: `docs/STARTUP_OPTIMIZATION_PLAN.md`
- Memoria de Sesión actual: `projects/mementobloom/HANDOFF_2026-06-25_memoria_sesion_fase3.md`
- Contexto de usuario: `.agent_context/secure/USER_CONTEXT.md`
