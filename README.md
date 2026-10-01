# MementoBloom - Sistema de Memoria Histórica para IA

**Estado:** Activo - gestión continua de proyectos cliente  
**Memoria:** 573 entradas indexadas  
**Commit Management360:** 7e40e075 (`m360(digitalizacion): add module README`)  
**Último commit mementobloom:** 6c046db (docs: keep TaxiLima2026 web Django as active view)

---

## Arquitectura dual

```
ROOT (código)          WS_ROOT (workspace cliente)
├── core/              ├── .agent_context/
├── tools/             │   ├── PROJECT_META.md (trackeado)
├── docs/              │   └── secure/USER_CONTEXT.md (no trackeado)
└── .agent_context/    ├── memory/graph/ (índice)
                       └── projects/<proyecto>/HANDOFF_*.md
```

---

## Instalación

```bash
# Cliente
git clone https://github.com/afarroc/memento.git mementobloom
bash mementobloom/memento_install --auto

# Desarrollo
bash memento_install --auto
```

---

## Comandos esenciales

| Acción | Comando |
|--------|---------|
| Contexto | `python3 tools/bootstrap_context.py --print` |
| Diagnóstico | `python3 tools/doctor.py --startup` |
| Tests | `python3 tools/selftest.py` |
| Registrar cliente | `python3 tools/register_client.py --name <proyecto>` |
| Escanear memoria | `python3 tools/quick_scan.py` |

---

## Proyectos registrados

| Proyecto | M360 ID | Nomenclatura | Estado |
|----------|---------|--------------|--------|
| mementobloom | — | — | Activo |
| perfil_personal | 24 | `PERFIL-*` | Activo |
| TaxiLima2026 | 23 | `TAXI-*` | Activo |
| Carpinteria | 25 | `CARP-*` | Activo |
| poco_xiaomi | 26 | `POCO-*` | Activo |
  - Código fuente: `/Volumes/Macintosh HD - Datos/projects/poco_xiaomi/`
  - Documentación de gestión: `mementobloom/projects/poco_xiaomi/`
| Management360 | 22 | `M360-*`, `DIGIT-*`, `CV-REVIEW-*`, `TASK-BITACORA-*` | Activo |
| Ventas_Porta | — | — | Registrado |
| Administracion_UPN | — | — | Registrado |
| jewelry_catalog | — | — | Registrado |
| LaMarca | — | — | Registrado |
| miui_termux | — | — | Registrado |
| novela_bl | — | — | Registrado |
| adherence_test | — | — | Registrado |
| banca_telefonica | — | — | Registrado |
| civilizaciones | — | — | Registrado |

---

## Servicios

| Servicio | Estado |
|----------|--------|
| Redis | OK (cloud) |
| Sala | STARTED (8767) |
| Panel | STARTED (8766) |

---

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `docs/PROJECT_CONTEXT.md` | Índice maestro de contexto |
| `projects/mementobloom/docs/tickets.md` | Sistema de tickets de servicio |
| `docs/CONTEXT_TREE.md` | Árbol de memoria jerárquico |
| `docs/guides/register-client.md` | Registro de clientes |
| `projects/<cliente>/docs/nomenclatura_tareas.md` | Nomenclatura por proyecto |

---

## Próximos pasos

1. Resolver tareas Mango360 sin prefijo documentado
2. Crear tareas faltantes para `poco_xiaomi`
3. Sincronizar tickets corregidos con panel/bridge
4. Verificar persistencia LLM en `poco_xiaomi` tras reinicio
5. Validar flujo `/digitalizacion/auditoria/<id>/` → aprobar → `/digitalizacion/certificar/<id>/` en Management360
6. Revisar `doc.refresh_from_db()` en `auditoria_documento` POST para evitar loop auditoría→certificación

---

*Ver `docs/AUDITORIA_PROYECTO.md` para auditoría completa*
