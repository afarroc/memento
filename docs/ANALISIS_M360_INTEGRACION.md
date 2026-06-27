# Análisis Exhaustivo de la Herramienta/Proyecto m360
**Para:** Proyecto MementoBloom  
**Basado en:** Exploración de `/Volumes/Macintosh HD - Datos/projects/management360`  
**Fecha:** 2026-06-25

---

## 1. ESTRUCTURA GENERAL

Management360 es un monolito Django con arquitectura de apps modulares. Aunque técnicamente es un proyecto web, funciona como **herramienta de gestión integral** mediante scripts especializados y convenciones documentadas.

### 1.1 Capas identificadas

| Capa | Componente | Función |
|------|------------|---------|
| **Aplicación web** | Django + DRF + WebSockets | Plataforma de gestión de eventos, tareas, chat, CV, KPIs, panel, salas, etc. |
| **Motor de documentación** | `scripts/m360_map.sh`, `app_map.sh` | Generación automática de `*_CONTEXT.md`, `*_DESIGN.md`, `*_DEV_REFERENCE.md` por app. |
| **Sistema GTD** | `gtd_setup/` + `load_gtd.py` + `Makefile` | Carga estructurada de categorías, inbox, templates, estados al modelo de Django. |
| **Gestión de proyectos** | `docs/plan_gestion_proyectos.md`, `SPRINT_*_PLAN.md` | Metodología ágil con GTD, Kanban, Eisenhower, MoSCoW. Definición de roles (Analista Doc/Dev/QA, Manager). |
| **Módulo memento (Django)** | `memento/` | App para notas tipo "memento mori" (no relacionada con MementoBloom; comparte nombre). |

### 1.2 Directorios y archivos clave

| Ruta | Tipo | Relevancia para MementoBloom |
|------|------|------------------------------|
| `scripts/m360_map.sh` | Script bash | Genera documentación de contexto automática por app. Adoptable. |
| `scripts/app_map.sh` | Script bash | Mapeo profundo de una sola app. Adoptable. |
| `gtd_setup/` | Directorio | Sistema de carga GTD vía CSV + scripts Python. Adoptable como backoffice de sprints. |
| `docs/plan_gestion_proyectos.md` | Documento | Metodologías de gestión implementadas. Adoptable. |
| `docs/SPRINT_8_PLAN.md` | Documento | Formato de plan de sprint detallado. Adoptable. |
| `docs/HANDOFF_*.md` | Documento | Formato de handoff estandarizado. Ya adoptado por MementoBloom. |
| `PROJECT_CONTEXT.md`, `*_CONTEXT.md` | Documento | Documentación de contexto generada automáticamente. Adoptable. |
| `MEMENTO_CONTEXT.md` (en m360) | Documento | Contexto de la app Django `memento` dentro de m360. Referencia de formato. |

---

## 2. ARCHIVOS DE CONFIGURACIÓN Y LÓGICA DE FUNCIONAMIENTO

### 2.1 Scripts de mapeo (`m360_map.sh`, `app_map.sh`)

**Lógica:**
1. Localiza `manage.py` para determinar raíz del proyecto.
2. Detecta "apps locales" como directorios con `__init__.py` + (`models.py` o `apps.py` o `urls.py`).
3. Clasifica archivos por categorías: views, templates, models, forms, urls, admin, static, tests, migrations, services, utils, management, config, other.
4. Genera un árbol de directorios.
5. Extrae endpoints de `urls.py` usando regex.
6. Extrae modelos (clases `class X(models.Model)`).
7. Extrae funciones clave de `views/` y `services/`.
8. Para modo `app`, genera `APPNAME_CONTEXT.md` y `APPNAME_DESIGN.md` (si existe motor de diseño).
9. Para modo `project`, genera `PROJECT_CONTEXT.md`.

**Capacidad adoptable:**
- Generación automática de documentación de contexto por componente.
- Auditoría de URLs.
- Categorización estandarizada de archivos.

**Limitación para MementoBloom:**
- Requiere Django (`manage.py`).
- MementoBloom es un paquete Python sin Django.

### 2.2 Sistema GTD (`gtd_setup/`)

**Estructura:**
```
gtd_setup/
├── 01_categories/      # CSV con categorías, tags, clasificaciones, estados
├── 02_inbox/           # CSV con items de bandeja de entrada
├── 03_templates/       # CSV con plantillas de proyectos, eventos base, programaciones
├── 04_backups/
├── 05_logs/
├── config.yaml         # Configuración del cargador
├── create_gtd_structure.sh
└── load_gtd.py         # Script de carga automática (orquesta pasos)
```

**Lógica:**
- Datos estructurados en CSV.
- `setup_gtd.py` valida y carga datos a modelos Django.
- `config.yaml` define pasos habilitados y archivos fuente.
- `Makefile` provee interfaz de comandos (`make load`, `make step-inbox`, etc.).

**Capacidad adoptable:**
- Formato CSV estructurado para sprint backlog.
- Flujo separado en pasos: categories → classifications → status → inbox → templates.
- Dry-run y estadísticas.

### 2.3 Metodologías de gestión (`docs/plan_gestion_proyectos.md`)

**Enfoques documentados:**
1. **GTD** — Bandeja de entrada, procesamiento, listas contextuales, revisión semanal.
2. **Kanban** — Columnas, WIP, drag & drop, métricas de flujo.
3. **Eisenhower** — Matriz Urgente/Importante.
4. **MoSCoW** — Must/Should/Could/Won’t.

**Modelos de datos propuestos para gestiont:**
- `TagCategory`, `Tag`
- `TaskDependency`
- `ProjectTemplate`, `TemplateTask`
- `InboxItem`
- `Reminder`

**Capacidad adoptable:**
- Clasificación de tareas por prioridad/método.
- Plantillas de proyecto.
- Dependencias entre tareas.

### 2.4 Sistema de sprints (`SPRINT_8_PLAN.md`)

**Formato documentado:**
- Contexto pre-sprint.
- Orden de ejecución (Día 1, Día 2, etc.).
- Tareas detalladas con:
  - ID, Rol, Prioridad, Dependencias, Archivos clave.
  - Criterios de aceptación.
  - Brief para Analista Dev/Analista Doc.
- Tareas paralelas.
- Pendientes pre-sprint.
- Definición de "Sprint Completado".
- Handoff para próxima sesión.

**Roles definidos:**
- Manager (PM)
- Analista Doc
- Analista Dev
- Analista QA

**Capacidad adoptable:** Ya adoptada en el plan Fase 3 (generado anteriormente).

---

## 3. EVALUACIÓN DE CAPACIDADES RELEVANTES PARA MEMENTOBLOOM

| Capacidad | Valor para MementoBloom | Estado actual en MementoBloom |
|-----------|--------------------------|-------------------------------|
| **Mapa de contexto automático** | Alto. Permite autogenerar documentación de arquitectura por componente (core, tools, panel, sala). | Parcial. Existe documentación manual pero no generada automáticamente. |
| **GTD estructurado (CSV)** | Medio. Útil para backoffice de planificación y carga masiva de tareas/handoffs. | No existe. Handoffs son Markdown generados por script. |
| **Metodologías de gestión** | Alto. Proporciona rigor en priorización, definición de done y flujo. | Parcial. Plan Fase 3 adoptó Kanban/sprint implícitamente. |
| **Formato de handoff estandarizado** | Alto. Ya se usa en MementoBloom pero podría alinearse más con m360. | Sí, formato Markdown similar. |
| **Roles definidos** | Medio. Clarifica responsabilidades en documentación. | No formalizado. |
| **Sistema de sprints documentado** | Alto. Ya se diseñó en Fase 3. | Sí. |
| **App memento dentro de m360** | Bajo/Conflictivo. Es una app Django de notas personales, no gestión de memoria IA. | No relacionada. |

---

## 4. ESTRATEGIA DE INTEGRACIÓN

### 4.1 Enfoque: Adopción selectiva sin acoplamiento estructural

MementoBloom debe **mantener su independencia arquitectónica** (paquete Python standalone, no Django). Sin embargo, puede **adoptar** las convenciones, formatos, scripts y metodologías de m360 para fortalecer su gestión.

**Principios:**
- **No fusionar código:** MementoBloom no se convierte en app Django de m360.
- **Adoptar formatos:** Usar el estilo de documentación, handoffs y sprints de m360.
- **Reimplementar herramientas equivalentes:** Crear scripts inspirados en `m360_map.sh` y `gtd_setup/` adaptados a la arquitectura de MementoBloom.
- **Mantener trazabilidad:** Referenciar en MementoBloom la fuente de las convenciones adoptadas.

### 4.2 Puntos de integración específicos

#### 4.2.1 Documentación automática de contexto (inspirado en `m360_map.sh`)

Crear `tools/memento_map.sh` que:
- Detecte la raíz del proyecto (no requiere `manage.py`, busca `.agent_context/PROJECT_META.md` o `memory/graph/`).
- Clasifique archivos en: core, tools, panel, sala, vault, models, tests, docs, config, scripts.
- Genere:
  - `PROJECT_CONTEXT.md` (visión global).
  - `MEMENTO_DESIGN.md` (arquitectura).
  - `MEMENTO_DEV_REFERENCE.md` (referencia de desarrollo).
  - Por componente: `CORE_CONTEXT.md`, `TOOLS_CONTEXT.md`, etc.

#### 4.2.2 Sistema GDT/Kanban para sprints (inspirado en `gtd_setup/`)

Crear `gtd_memento/` con:
- `01_categories/` — Tags para tipos de tareas (core, tools, docs, test, fix, feat) y prioridades (P0-P3).
- `02_inbox/` — Items pendientes en formato CSV.
- `03_templates/` — Plantillas de sprint, reporte de handoff, reporte de doctor.
- `04_sprints/` — Planes de sprint en formato CSV + Markdown generado.
- `config.yaml` — Configuración del generador.
- `sprint_builder.py` — Generador de `SPRINT_X_PLAN.md` desde CSV.
- `Makefile` — Comandos `make sprint-new`, `make sprint-report`, `make context`.

#### 4.2.3 Metodologías de gestión (inspirado en `plan_gestion_proyectos.md`)

Adoptar formalmente en MementoBloom:
- **GTD** para captura de pendientes: todo issue/tarea pendiente se escribe en `gtd_memento/02_inbox/inbox_items.csv`.
- **Kanban** para visualización de sprint: columnas TODO/IN_PROGRESS/REVIEW/DONE.
- **MoSCoW** para priorización en sprint planning.
- **Eisenhower** para clasificación de bugs/deuda técnica.

#### 4.2.4 Roles (inspirado en m360)

Definir en `docs/FASE_3_ESTRUCTURA_ORG_DOCUMENTACION.md`:
- **Technical Lead / PM** — Planificación, arquitectura, revisión.
- **Backend Dev** — Implementación de core/tools.
- **DevOps** — Empaquetado, Docker, instalador.
- **QA** — Pruebas, fixtures, validación.
- **Doc** — Documentación, handoffs, mapas de contexto.

#### 4.2.5 Handoffs mejorados

Adoptar el formato extendido de m360:
```markdown
# HANDOFF - YYYY-MM-DD - <Descripción>
> Sesión: <Tipo de sesión>
> Manager: <Rol>
> Sprint: <N>

## Decisión Tomada
...
## Sistema entregado
...
## Próxima Iteración Sugerida
...
```

---

## 5. PLAN DE ACCIÓN PARA INTEGRACIÓN INMEDIATA

| Paso | Acción | Herramienta m360 adoptada | Responsable | Entregable |
|------|--------|---------------------------|-------------|------------|
| 1 | Crear `tools/memento_map.sh` (inspirado en `m360_map.sh`) | Motor de mapeo | Backend/Líder Técnico | Script funcional |
| 2 | Generar `PROJECT_CONTEXT.md`, `MEMENTO_DESIGN.md`, `MEMENTO_DEV_REFERENCE.md` para mementobloom | Formato de documentación | Líder Técnico | Documentos en `docs/` |
| 3 | Crear `gtd_memento/` con CSV base + `sprint_builder.py` + `Makefile` | Sistema GTD | Backend | Directorio funcional |
| 4 | Ejecutar `memento_map.sh project` sobre mementobloom y commitear docs | Mapa de contexto | Líder Técnico | Docs versionados |
| 5 | Generar primer sprint plan real (`SPRINT_0_PLAN.md`) usando plantilla m360 | Formato SPRINT | Líder Técnico | Documento de sprint |
| 6 | Commitear `docs/FASE_3_PLAN_APROBADO.md` y `docs/FASE_3_FLUJO_OPERATIVO.md` | Gobernanza | Líder Técnico | Código + docs |

---

## 6. RIESGOS Y MITIGACIONES DE INTEGRACIÓN

| Riesgo | Mitigación |
|--------|------------|
| MementoBloom no es Django, scripts m360 no son 100% compatibles | Adaptar scripts manteniendo formato de salida (CONTEXT.md, SPRINT_PLAN.md). |
| Duplicación de estándares entre m360 y memento | Documentar en MementoBloom que adopta convenciones de m360; mantener una única fuente de verdad. |
| Complejidad excesiva del sistema GTD para un equipo pequeño | Implementar versión ligera: CSV simple + Makefile, sin app Django asociada. |
| Confusión entre app Django `memento` y proyecto `MementoBloom` | Usar nombres canónicos: `mementobloom` (proyecto), `m360` (proyecto Django), `m360-memento` (app Django). |

---

## 7. CONCLUSIONES

**m360 es una herramienta de gestión y documentación** más que una librería. Su valor para MementoBloom está en:
1. **Convenciones probadas** de documentación automática (`*_CONTEXT.md`).
2. **Metodologías estructuradas** (GTD, Kanban, sprints).
3. **Formato de handoff y sprint plan** que ya está alineado con lo planeado en Fase 3.

**Recomendación:** Adoptar el *formato* y la *metodología* de m360, reimplementando las herramientas específicas (scripts de mapeo, GTD ligero) dentro del ecosistema de MementoBloom. No hay necesidad de acoplamiento estructural; la integración es cultural y procedimental.
