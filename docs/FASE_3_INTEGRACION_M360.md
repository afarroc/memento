# Documento: Directriz de Integración M360 → MementoBloom
**Generado:** 2026-06-25T13:09:39-05:00  
**Proyecto principal:** MementoBloom  
**Infraestructura de ejecución:** Management360 (M360)  
**Alcance:** Sincronización automatizada de sprints, handoffs y tareas entre MementoBloom y M360

---

## 1. PRINCIPIO FUNDAMENTAL

MementoBloom es el **núcleo de lógica de negocio**:
- Planificación de sprints.
- Gestión de memoria histórica (handoffs, índice, seeds).
- Definición de tareas, criterios de aceptación y Definition of Done.
- Metodologías (GTD, Kanban, MoSCoW, Eisenhower).
- Contexto universal modelo-agnóstico.

M360 es el **medio técnico de ejecución** (infraestructura):
- Almacenamiento persistente de eventos, proyectos y tareas.
- Dashboard visual, panel de control y sala de chat.
- Kanban, Eisenhower, GTD ejecutables en interfaz web.
- Recordatorios, notificaciones y colaboración multi-usuario.
- API HTTP para operaciones CRUD.

**Regla de oro:** MementoBloom *decide* qué se crea/modifica; M360 *ejecuta* la creación/modificación.

---

## 2. ARQUITECTURA DE INTEGRACIÓN

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMENTOBLOOM (Lógica)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Sprint Plan │  │  Handoffs   │  │  Context Builder    │ │
│  │  (CSV/MD)   │  │  (Markdown) │  │  (JSON/MD)          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          ▼                                   │
│               ┌──────────────────┐                           │
│               │  m360_bridge.py  │  (cliente HTTP ligero)    │
│               │  - CSRF fetch    │                           │
│               │  - Session login │                           │
│               │  - CRUD events   │                           │
│               │  - CRUD projects │                           │
│               │  - CRUD tasks    │                           │
│               │  - GTD inbox     │                           │
│               └────────┬─────────┘                           │
└────────────────────────┼─────────────────────────────────────┘
                         │ HTTP (form-urlencoded / multipart)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    M360 (Ejecución)                          │
│  /events/create/        /projects/create/                   │
│  /tasks/create/         /inbox/create/                      │
│  /planning/             /reminders/create/                  │
│  /dependencies/create/  /templates/<id>/use/                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. MAPEO DE ENDPOINTS M360 → OPERACIONES DE NEGOCIO

### 3.1 Eventos

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/events/create/` | POST (form) | Crear evento de sprint (kickoff, review, retro) | title, description, start_date, end_date, status, category, price, capacity |
| `/events/<id>/status/` | POST | Cambiar estado (planificado → en progreso → completado) | status |
| `/events/<id>/assign/` | POST | Asignar responsable (usuario M360) | user_id |
| `/events/export/` | GET | Exportar eventos a CSV para reporte | — |

### 3.2 Proyectos

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/projects/create/` | POST (form) | Crear proyecto por sprint o fase | name, description, start_date, end_date, status |
| `/projects/<id>/status/` | POST | Transicionar estado (activo, pausado, completado) | status |
| `/projects/<id>/activate/` | POST | Reactivar proyecto archivado | — |
| `/projects/panel/` | GET | Obtener panel de proyectos (kanban) | — |

### 3.3 Tareas

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/tasks/create/` | POST (form) | Crear tarea desde sprint backlog | title, description, project_id, due_date, priority, status |
| `/tasks/<id>/status/` | POST | Cambiar estado (TODO, IN_PROGRESS, REVIEW, DONE) | status |
| `/tasks/<id>/dependencies/` | GET/POST | Vincular dependencias entre tareas | depends_on, dependency_type |
| `/tasks/schedules/create/` | POST | Crear tarea recurrente (revisión semanal) | cron, task_template_id |
| `/kanban/` | GET | Sincronizar columnas Kanban | — |

### 3.4 GTD / Inbox

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/inbox/create/` | POST | Inyectar items de inbox desde handoffs no procesados | title, description, created_by |
| `/inbox/process/<item_id>/` | POST | Marcar inbox item como procesado → tarea/proyecto | action (convert_to_task, convert_to_project, archive) |
| `/inbox/api/stats/` | GET | Obtener estadísticas de inbox para dashboard | — |

### 3.5 Planning y Recordatorios

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/planning/` | GET/POST | Acceder y modificar planificación temporal | date_range |
| `/reminders/create/` | POST | Crear recordatorio de sprint review / handoff | remind_at, task_id, project_id, reminder_type |
| `/templates/<id>/use/` | POST | Instanciar plantilla de proyecto sprint | template_id, user_id |

### 3.6 Dependencias

| Endpoint M360 | Método | Uso en MementoBloom | Parámetros clave |
|---------------|--------|----------------------|------------------|
| `/dependencies/create/<task_id>/` | POST | Crear dependencia entre tareas del sprint | depends_on, dependency_type |
| `/dependencies/graph/<task_id>/` | GET | Obtener grafo de dependencias para crítico path | — |

---

## 4. DISEÑO DEL BRIDGE (`m360_bridge.py`)

### 4.1 Responsabilidades

- Autenticación CSRF + session contra M360.
- Abstracción de operaciones CRUD sobre eventos, proyectos, tareas, inbox, recordatorios.
- Manejo de errores y reintentos.
- Logging de sincronización en memoria histórica de MementoBloom.

### 4.2 Interfaz propuesta

```python
class M360Bridge:
    def __init__(self, base_url: str, username: str, password: str): ...
    def create_event(self, title, start, end, **kwargs) -> dict: ...
    def create_project(self, name, description, **kwargs) -> dict: ...
    def create_task(self, title, project_id, **kwargs) -> dict: ...
    def update_task_status(self, task_id, status) -> dict: ...
    def create_inbox_item(self, title, description) -> dict: ...
    def process_inbox_item(self, item_id, action) -> dict: ...
    def create_reminder(self, remind_at, task_id=None, project_id=None) -> dict: ...
    def create_dependency(self, task_id, depends_on, type_) -> dict: ...
    def get_kanban(self) -> dict: ...
    def logout(self) -> None: ...
```

### 4.3 Almacenamiento de credenciales

- URL base, usuario y password se almacenan en `~/.memento/vault.json` (no en código).
- Sesión se mantiene en memoria durante la vida útil del bridge; no persiste cookie en disco.
- CSRF token se obtiene dinámicamente en cada sesión.

---

## 5. FLUJO DE SINCRONIZACIÓN SPRINT → M360

```
[MementoBloom]                      [M360]
       │                               │
       │ 1. Leer SPRINT_N_PLAN.md      │
       │    y gtd_memento sprint CSV   │
       │       │                       │
       │       ▼                       │
       │ 2. Detectar operaciones       │
       │    pendientes:                │
       │    - Proyecto nuevo           │
       │    - Tareas nuevas            │
       │    - Eventos (kickoff,        │
       │      review, retro)           │
       │    - Recordatorios            │
       │    - Dependencias             │
       │       │                       │
       │       ▼                       │
       │ 3. Llamar M360Bridge          │
       │       │                       │
       │       ▼                       │
       │ 4. POST /projects/create/     │
       │    ← ID proyecto M360         │
       │       │                       │
       │ 5. POST /tasks/create/        │
       │    (con project_id)           │
       │       │                       │
       │ 6. POST /events/create/       │
       │    (kickoff, review)          │
       │       │                       │
       │ 7. POST /reminders/create/    │
       │       │                       │
       │ 8. Registro en memoria        │
       │    (handoff de sync)          │
       │                               │
```

### 5.1 Trigger: Generación de sprint

- MementoBloom genera `SPRINT_N_PLAN.md` y `sprint_tasks.csv`.
- Un hook en `session_start.py` o script dedicado invoca `m360_bridge.sync_sprint(sprint_id)`.
- El bridge:
  1. Crea proyecto en M360 (`/projects/create/`).
  2. Crea tareas asociadas (`/tasks/create/` con `project_id`).
  3. Crea eventos de calendario (`/events/create/`).
  4. Crea recordatorios (`/reminders/create/`).
  5. Crea dependencias (`/dependencies/create/`).
- Resultado: M360 refleja el sprint completo; MementoBloom mantiene la autoría.

### 5.2 Trigger: Actualización de estado

- Cuando MementoBloom cambia estado de tarea (ej: DONE), invoca `update_task_status(task_id, "DONE")`.
- M360 actualiza su panel/kanban automáticamente.
- Handoff registra la sincronización.

### 5.3 Trigger: Inbox GTD

- MementoBloom detecta items pendientes en `gtd_memento/02_inbox/inbox_items.csv` no procesados.
- Invoca `create_inbox_item()` en M360.
- M360 muestra items en `/inbox/`.
- Usuario procesa en interfaz M360; MementoBloom puede consultar `/inbox/api/stats/` para actualizar su dashboard.

---

## 6. FORMATO DE SINCRONIZACIÓN

### 6.1 CSV de sprint (origen: MementoBloom)

```csv
sprint_id,type,m360_operation,params
SPRINT_0,project,create_project,"{""name"":""Fase 3 - Sprint 0"",""description"":""Estabilización y hardening""}"
SPRINT_0,task,create_task,"{""title"":""T0.1 - Corregir panel_server.py"",""project_id"":""<DYNAMIC>"",""status"":""TODO""}"
SPRINT_0,event,create_event,"{""title"":""Sprint 0 Kickoff"",""start"":""2026-06-26"",""end"":""2026-06-26""}"
SPRINT_0,reminder,create_reminder,"{""remind_at"":""2026-06-27T09:00:00"",""task_id"":""<DYNAMIC>""}"
```

### 6.2 Handoff de sincronización

```markdown
# HANDOFF - Sync M360

## Sincronización
- Sprint: SPRINT_0
- Proyecto M360 ID: 42
- Tareas creadas: 12
- Eventos creados: 3
- Recordatorios: 2
- Errores: 0
```

---

## 7. CONFIGURACIÓN REQUERIDA

### 7.1 Variables de entorno (`.env` del proyecto MementoBloom)

```env
M360_BASE_URL=http://localhost:8000
M360_USERNAME=arturo
M360_PASSWORD=<vault>
M360_CSRF_ENDPOINT=/api/csrf/
M360_TIMEOUT=10
```

### 7.2 Vault entry

```json
{
  "sources": {
    "m360": {
      "base_url": "http://localhost:8000",
      "username": "arturo"
    }
  },
  "secrets": {
    "m360_password": {
      "value": "<base64 o fernet>",
      "encrypted": true
    }
  }
}
```

---

## 8. PLAN DE IMPLEMENTACIÓN DE LA INTEGRACIÓN

| Fase | Tarea | Entregable | Prioridad |
|------|-------|------------|-----------|
| **I1** | Implementar `m360_bridge.py` con autenticación y métodos CRUD básicos | Cliente HTTP funcional | Alta |
| **I2** | Implementar `sync_sprint.py` que lee `SPRINT_N_PLAN.md` y dispara operaciones M360 | Script de sincronización | Alta |
| **I3** | Agregar hook en `session_start.py` o comando `memento-sync` para ejecutar sync automáticamente | CLI tool | Media |
| **I4** | Implementar `pull_m360.py` para traer kanban/estados actualizados desde M360 | Sincronización bidireccional | Media |
| **I5** | Agregar validación en `doctor.py` para verificar conectividad con M360 | Check de salud | Baja |
| **I6** | Documentar flujo en `README.md` y `docs/FASE_3_INTEGRACION_M360.md` | Documentación | Media |

---

## 9. RIESGOS ESPECÍFICOS DE INTEGRACIÓN

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| M360 cambia endpoints o formularios | Alto | Versionar API client; incluir fallback a scrapeo si es necesario. |
| CSRF token no disponible | Alto | Implementar fetch de CSRF antes de cada POST; reintentar una vez si falla. |
| Sesión expira durante sync largo | Medio | Re-autenticar automáticamente al detectar 403. |
| Latencia alta entre MementoBloom y M360 | Bajo | Timeout configurable; batch de operaciones. |
| Conflictos de estado (M360 vs MementoBloom) | Medio | MementoBloom es fuente de verdad; M360 refleja. Resolver conflictos con timestamp. |

---

## 10. CRITERIOS DE ÉXITO

1. `python3 tools/sync_sprint.py --sprint SPRINT_0` crea en M360: 1 proyecto, N tareas, M eventos, K recordatorios sin intervención manual.
2. Estado de tareas en M360 refleja cambios originados en MementoBloom en < 30 segundos.
3. Si M360 está caído, MementoBloom continúa funcionando (degradado) y registra errores en handoff sin crash.
4. Vault almacena credenciales M360 de forma segura; no hay secrets en código.
5. Cualquier modelo nuevo puede leer `docs/FASE_3_INTEGRACION_M360.md` para entender el flujo de sincronización.

---

**Próxima acción:** Crear carpeta `tools/m360_bridge/` con `__init__.py`, `client.py`, `models.py`, `sync.py` e implementar I1-I2 en paralelo con Sprint 0 de Fase 3.
