# Especificación API Genérica M360 v1

**Proyecto:** MementoBloom + Management360  
**Documento:** Especificación de endpoints JSON para integración con cualquier herramienta externa  
**Versión:** 0.1.0-draft  
**Fecha:** 2026-06-26  
**Estado:** Aprobado para revisión / Pendiente de implementación en M360

---

## 1. Principios de diseño

- **Agnóstica al consumidor**: no depende de MementoBloom ni de ninguna herramienta en particular.
- **Read-first, write-when-needed**: prioriza consultas; escritura solo cuando el flujo lo requiera.
- **Stateless**: usa la sesión Django existente (CSRF + cookie); no introduce tokens nuevos.
- **Versionada**: `/api/v1/` permite evolución sin romper clientes.
- **Filtrable y paginada**: todas las listas soportan `?q=`, `?limit=`, `?offset=`, `?from=`, `?to=`.

---

## 2. Autenticación

Método: **Session auth** (CSRF cookie + Basic Auth inicial).

1. `GET /api/csrf/` → obtener `csrftoken`.
2. `POST /api/login/` (JSON `{"username":"...","password":"..."}`) → establecer sesión.
3. Requests subsecuentes incluyen header `X-CSRFToken`.

**Nota:** para tooling automatizado, usar credenciales de servicio dedicadas (no `su`).

---

## 3. Errores estandarizados

```json
{
  "error": {
    "code": "validation_error",
    "message": "Campos requeridos faltantes: project_id",
    "fields": ["project_id"]
  }
}
```

Códigos HTTP:
- `200` OK
- `400` Bad Request (validación)
- `401` Unauthorized
- `403` Forbidden
- `404` Not Found
- `429` Rate limit (futuro)
- `500` Internal Server Error

---

## 4. Endpoints

### 4.1 Health

```
GET /api/v1/health/
```

Respuesta:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-26T22:47:00-05:00"
}
```

---

### 4.2 Proyectos

#### Listar proyectos

```
GET /api/v1/projects/
```

Query params:
- `?q=` (búsqueda por título)
- `?status=` (activo/inactivo)
- `?limit=` (default 20, max 100)
- `?offset=`

Respuesta:
```json
{
  "data": [
    {
      "id": 60,
      "title": "Memento desarrollo de si mismo",
      "description": "...",
      "status": "active",
      "created_at": "2026-06-14T...",
      "updated_at": "2026-06-26T..."
    }
  ],
  "meta": {"count": 1, "limit": 20, "offset": 0}
}
```

#### Detalle de proyecto

```
GET /api/v1/projects/{id}/
```

Incluye contadores embebidos:
```json
{
  "id": 60,
  "title": "...",
  "status": "active",
  "stats": {
    "tasks_total": 18,
    "tasks_completed": 9,
    "events_total": 12,
    "reminders_total": 5
  }
}
```

---

### 4.3 Tareas

#### Listar tareas de un proyecto

```
GET /api/v1/projects/{project_id}/tasks/
```

Query params:
- `?status=` (To Do, In Progress, Completed, In Review)
- `?q=` (búsqueda en título/descripción)
- `?assigned_to=` (user id)
- `?from=` (fecha creación mínima, ISO8601)
- `?to=` (fecha creación máxima, ISO8601)
- `?limit=`, `?offset=`

Respuesta:
```json
{
  "data": [
    {
      "id": 181,
      "title": "T0.1 compilar panel_server.py",
      "description": "...",
      "status": "Completed",
      "status_id": 3,
      "important": false,
      "assigned_to": 1,
      "assigned_to_name": "Arturo",
      "project_id": 60,
      "created_at": "2026-06-26T...",
      "updated_at": "2026-06-26T..."
    }
  ],
  "meta": {"count": 18, "limit": 20, "offset": 0}
}
```

#### Detalle de tarea

```
GET /api/v1/tasks/{task_id}/
```

Respuesta: misma estructura que item de lista, más:
```json
{
  ...
  "dependencies": [182, 183],
  "events_linked": [45, 46],
  "reminders_linked": [12]
}
```

#### Actualizar estado de tarea

```
POST /api/v1/tasks/{task_id}/status/
```

Body:
```json
{
  "status": "Completed",
  "status_id": 3,
  "note": "Verificado en Ventas_Porta"
}
```

Respuesta:
```json
{
  "id": 181,
  "status": "Completed",
  "status_id": 3,
  "updated_at": "2026-06-26T..."
}
```

---

### 4.4 Eventos

#### Listar eventos de un proyecto

```
GET /api/v1/projects/{project_id}/events/
```

Query params:
- `?from=` (fecha inicio mínima)
- `?to=` (fecha fin máxima)
- `?category=`
- `?status=`
- `?limit=`, `?offset=`

Respuesta:
```json
{
  "data": [
    {
      "id": 45,
      "title": "Sprint 0 Review",
      "start_date": "2026-06-27",
      "end_date": "2026-06-27",
      "status": "planned",
      "category": "sprint",
      "venue": "",
      "capacity": 0,
      "created_at": "..."
    }
  ],
  "meta": {"count": 12, ...}
}
```

---

### 4.5 Recordatorios

#### Listar recordatorios de un proyecto

```
GET /api/v1/projects/{project_id}/reminders/
```

Query params:
- `?task_id=`
- `?remind_before=`
- `?from=` (fecha de recordatorio)
- `?to=`
- `?limit=`, `?offset=`

Respuesta:
```json
{
  "data": [
    {
      "id": 12,
      "remind_at": "2026-06-27T09:00:00-05:00",
      "task_id": 181,
      "task_title": "T0.1 compilar panel_server.py",
      "reminder_type": "task",
      "project_id": 60
    }
  ],
  "meta": {...}
}
```

---

### 4.6 Inbox

#### Crear item de inbox

```
POST /api/v1/inbox/
```

Body:
```json
{
  "title": "Revisar deuda técnica T2.3",
  "description": "Dockerfile no probado aún",
  "created_by": "mementobloom",
  "metadata": {"source": "handoff", "sprint": 2}
}
```

Respuesta:
```json
{
  "id": 256,
  "title": "Revisar deuda técnica T2.3",
  "status": "new",
  "created_at": "..."
}
```

#### Procesar item de inbox

```
POST /api/v1/inbox/{item_id}/process/
```

Body:
```json
{
  "action": "classify",
  "classification": "task",
  "target_project_id": 60,
  "note": "Convertir a tarea T2.3"
}
```

Acciones válidas: `classify`, `convert_to_task`, `convert_to_event`, `archive`, `delete`.

---

### 4.7 Kanban (agregado)

```
GET /api/v1/kanban/
```

Respuesta:
```json
{
  "columns": {
    "To Do": {
      "title": "Por Hacer",
      "color": "#6c757d",
      "count": 5,
      "tasks": [ ... ]
    },
    "In Progress": {
      "title": "En Progreso",
      "color": "#007bff",
      "count": 4,
      "tasks": [ ... ]
    },
    "Completed": {
      "title": "Completado",
      "color": "#28a745",
      "count": 9,
      "tasks": [ ... ]
    },
    "In Review": {
      "title": "En Revisión",
      "color": "#fd7e14",
      "count": 0,
      "tasks": []
    }
  },
  "meta": {"total_tasks": 18}
}
```

---

## 5. Filtros y paginación

**Reglas comunes:**
- `limit`: máximo 100, default 20.
- `offset`: desplazamiento desde 0.
- `from` / `to`: fechas ISO8601 (date o datetime).
- `q`: búsqueda full-text simple (ILIKE en título/descripción).
- Orden default: `-created_at` (más reciente primero). Soportar `?ordering=created_at` o `?ordering=-updated_at`.

---

## 6. Implementación en M360

### 6.1 Archivos sugeridos

```
Management360/
└── api/
    ├── views.py              # auth helpers existentes
    ├── memento_views.py      # NUEVO: vistas JSON genéricas
    ├── memento_urls.py       # NUEVO: rutas /api/v1/
    └── urls.py               # MODIFICAR: incluir memento_urls
```

### 6.2 Reglas de implementación

1. No modificar vistas HTML existentes (`events/views/*`).
2. Reutilizar managers (`TaskManager`, `ProjectManager`, `EventManager`) para consistencia.
3. Usar `JsonResponse` con `safe=False` cuando se devuelvan listas.
4. Decoradores: `@login_required`, `@require_GET`, `@require_POST`.
5. Validación manual de inputs (sin DRF, para mantener dependencias actuales).
6. Documentar cada endpoint con docstring y ejemplo de respuesta.

---

## 7. Consumidor MementoBloom (post-implementación)

Una vez disponible `/api/v1/` en M360, MementoBloom podrá:

1. Sincronizar sprints completos (plan vs real) via `sync_sprint.py`.
2. Actualizar estado de tareas automáticamente desde `tools/restore_sala.py` o `tools/session_start.py`.
3. Generar reportes de salud de sprint consultando `/api/v1/projects/{id}/tasks/` + eventos + recordatorios.
4. Crear inbox items desde handoffs o sesiones de usuario.
5. Eliminar duplicados de polling a vistas HTML.

El bridge M360 existente (`tools/m360_bridge/client.py`) debe evolucionar para usar estos endpoints JSON como fuente de verdad, manteniendo el código HTML como fallback solo si `/api/v1/` no está disponible.

---

## 8. Aprobación y seguimiento

- **Documento padre:** `docs/FASE_3_INTEGRACION_M360.md`
- **Sprint objetivo:** Sprint 2 (pendiente de confirmación)
- **Tareas derivadas:**
  - M360-1: Implementar `/api/v1/health/` y `/api/v1/projects/` en M360
  - M360-2: Implementar endpoints de tareas (list, detail, status)
  - M360-3: Implementar endpoints de eventos, recordatorios e inbox
  - M360-4: Implementar `/api/v1/kanban/` agregado
  - MB-1: Evolucionar `tools/m360_bridge/client.py` para consumir `/api/v1/`
  - MB-2: Actualizar `tools/sync_sprint.py` para leer estado real vía API
