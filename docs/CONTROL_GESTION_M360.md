# CONTROL DE GESTIÓN M360
**Proyecto:** MementoBloom  
**Documento:** Protocolo de operación de Management360 como gestor de proyectos oficial  
**Versión:** 1.0.0  
**Fecha:** 2026-06-26  
**Estado:** Aprobado para operación

---

## 1. PRINCIPIO DE GESTIÓN

M360 es el **gestor de proyectos oficial** de MementoBloom desde Junio 2026. Todos los sprints, tareas, eventos, recordatorios e inbox deben reflejarse en M360. MementoBloom mantiene la autoría de la lógica y la planificación; M360 ejecuta y muestra el estado actual.

### 1.1 Reglas transversales

- Proyecto M360: **ID 78** "MementoBloom - S-27-06" (`http://localhost:8000/events/projects/panel/78/`)
- Credenciales M360: ver `.env` (`M360_USERNAME`, `M360_PASSWORD`) o vault_manager.py
- Endpoints base: `http://127.0.0.1:8000/events/...`
- M360 es la herramienta de ejecución; MementoBloom es la fuente de verdad de la planificación.
- No crear proyectos adicionales salvo que sean clientes formales gestionados por el equipo.
- Antes de sincronizar, siempre revisar `NEXT_SESSION.md` y `gtd_memento/` para conocer el estado real de los sprints.

---

## 2. DOCUMENTACIÓN DE CONTROL

### 2.1 Archivos obligatorios

| Archivo | Ruta | Propósito |
|---------|------|-----------|
| `docs/CONTROL_GESTION_M360.md` | Raíz docs | Este documento |
| `docs/FASE_3_INTEGRACION_M360.md` | Raíz docs | Especificación técnica de la integración |
| `tools/m360_bridge/client.py` | tools | Cliente HTTP autenticado contra M360 |
| `tools/m360_bridge/sync.py` | tools | Motor de sincronización de sprints |
| `tools/sync_sprint.py` | tools | CLI para disparar la sincronización |
| `gtd_memento/` | Raíz | Origen de verdad de sprints/tareas/inbox |
| `.env` | Raíz | Credenciales y timeouts M360 |

### 2.2 Estructura M360 en el proyecto

- **Panel de proyectos:** `http://localhost:8000/events/projects/panel/78/`
- **Tablero Kanban:** `http://localhost:8000/events/kanban/`
- **Inbox:** `http://localhost:8000/events/inbox/`
- **Tareas:** `http://localhost:8000/events/tasks/`
- **Eventos:** `http://localhost:8000/events/events/`
- **Recordatorios:** `http://localhost:8000/events/reminders/`

---

## 3. METODOLOGÍA DE GESTIÓN DE SPRINTS

### 3.1 Ciclo obligatorio

1. Planificación en MementoBloom: documento `docs/FASE_3_FLUJO_OPERATIVO.md` + `gtd_memento/03_templates/sprint_templates.csv`.
2. Sincronización con M360:
   ```bash
   python3 tools/sync_sprint.py --sprint SPRINT_X --project-id 78
   ```
3. Ejecución en M360:
   - Tareas / Kanban / Eventos / Recordatorios son gestionados por el equipo en interfaz M360.
4. Cierre de sprint:
   - Actualizar `gtd_memento/04_sprints/` con resultados.
   - Generar HANDOFF en `projects/mementobloom/HANDOFF_YYYY-MM-DD_<tipo>.md`.

### 3.2 Backlog priorizado

| ID | Tipo | Descripción | Estado M360 | Criterios de aceptación |
|----|------|-------------|-------------|--------------------------|
| SPRINT_0 | Proyecto/tareas/evento | Corregir panel_server.py, paths y Redis | Sincronizado | `sync_sprint.py --sprint SPRINT_0 --project-id 78` ok=7 |
| SPRINT_1 | Tareas | Namespacing Redis + detección de puertos | Pendiente | Sincronizar y validar en Kanban |
| SPRINT_2 | Tareas | Portabilidad de instalador + Dockerfile | Pendiente | Sincronizar y validar |
| SPRINT_3 | Tareas | Seguridad + vault + .gitignore | Pendiente | Sincronizar y validar |
| SPRINT_4 | Tareas | Pruebas multi-cliente + métricas | Pendiente | Sincronizar y validar |
| SPRINT_5 | Tareas | Documentación + release checklist | Pendiente | Sincronizar y validar |

---

## 4. USO DEL PANEL M360

### 4.1 Proyecto activo

- **ID:** 60
- **Nombre:** Memento desarrollo de si mismo
- **URL:** `http://localhost:8000/events/projects/panel/78/`
- **Regla:** todas las tareas de MementoBloom deben asociarse a este proyecto salvo que se cree uno nuevo formalmente.

### 4.2 Kanban

- **URL:** `http://localhost:8000/events/kanban/`
- **Columnas vigentes en M360:** To Do, In Progress, Review, Completed y estados adicionales según catálogo.
- **Regla:** el estado en M360 es el estado oficial del sprint. Si hay divergencia, M360 prevalece.

### 4.3 Inbox

- **URL:** `http://localhost:8000/events/inbox/`
- Procesar items pendientes de `gtd_memento/02_inbox/inbox_items.csv` convirtiéndolos en tareas o proyectos en M360.

### 4.4 Eventos y recordatorios

- **Eventos:** kickoff, review, retro por sprint.
- **Recordatorios:** vinculados a las tareas y proyectos según el `sync.py`.

---

## 5. SINCRONIZACIÓN MEMENTOBLOOM -> M360

### 5.1 Comandos obligatorios

| Comando | Propósito | Frecuencia |
|---------|-----------|------------|
| `python3 tools/sync_sprint.py --sprint SPRINT_X --project-id 78` | Sincronizar un sprint completo | Al final de planning y al cerrar sprint |

```
[M365] gtd_memento                        [M360]
     |                                        |
     | 1. Leer sprint y templates             |
     |       |                               |
     |       v                               |
     | 2. Inferir SprintSpec                 |
     |       |                               |
     |       v                               |
     | 3. POST /events/tasks/create/         |
     |       |                               |
     |       v                               |
     | 4. POST /events/events/create/        |
     |       |                               |
     |       v                               |
     | 5. POST /events/reminders/create/     |
     |       |                               |
     |       v                               |
     | 6. Validar panel/kanban M360          |
     |                                        |
```

### 5.3 Criterios de éxito en sync

- Código HTTP = 200 o 302
- Respuesta JSON no contiene `errorlist`
- URL final termina en `/events/<recurso>/panel/` o `/events/<recurso>/<id>/detail/`
- En panel/kanban se refleja la creación en menos de 30 segundos

---

## 6. ROLES Y RESPONSABILIDADES

| Rol | Responsable | Acciones |
|-----|-------------|----------|
| Technical Lead | Usuario principal | Planificación, arquitectura, revisión, handoffs |
| Backend Dev | Agente Kilo | Implementación core/tools, bridge |
| QA | Usuario principal | Pruebas, validación M360, verificación sync |
| Doc | Usuario principal | Documentación, control de gestión, handoffs |

### 6.1 Protocolo de handoff

Todo cambio relevante debe cerrar sesión con:
1. `python3 tools/session_start.py --services-only`
2. `python3 tools/selftest.py`
3. `python3 tools/doctor.py --startup`
4. Generar HANDOFF en `projects/mementobloom/HANDOFF_YYYY-MM-DD_<tipo>.md`
5. Actualizar `NEXT_SESSION.md`

---

## 7. RIESGOS Y CONTINGENCIAS

| Riesgo | Mitigación |
|--------|------------|
| M360 no arranca o se cae | Reiniciar `manage.py runserver` en carpeta M360; MementoBloom sigue funcionando con sync degradado |
| CSRF o sesión caducada | Re-ejecutar `python3 tools/m360_bridge/client.py` como CLI para validar login |
| Timeout en sincronización | Aumentar `M360_TIMEOUT=60` en `.env` |
| Divergencia de estados | M360 prevalece; actualizar manualmente M360 y reflejar en handoff |
| Duplicación de proyectos | Solo crear proyectos desde M360; no duplicar IDs 60-65 sin autorización |

---

## 8. CRITERIOS DE ÉXITO DEL PROCESO

1. [x] M360 opera como gestor oficial de proyectos de MementoBloom
2. [x] Sincronización funcional para proyectos, tareas, eventos, recordatorios e inbox
3. [x] Documento de control leíble por cualquier modelo/agente
4. [ ] Completar sync de sprints 1-5 (próxima sesión)
5. [ ] Docs actualizados con procedimientos de contingencia y troubleshooting

---

## 9. PRÓXIMOS PASOS

1. Validar sincronización de **SPRINT_0** completada (`ok=7, errors=0`)
2. Ejecutar SPROUT_1:
   ```bash
    python3 tools/sync_sprint.py --sprint SPRINT_1 --project-id 78
   ```
3. Actualizar `gtd_memento/04_sprints/SPRINT_1_PLAN.md`
4. Ejecutar selftest y doctor local
5. Generar HANDOFF de cierre de sesión
6. Registrar sync exitoso en `docs/CONTROL_GESTION_M360.md` y actualizar este documento

**Comando para inicio de próxima sesión:**
```bash
python3 tools/session_start.py --quick --limit 8
```
