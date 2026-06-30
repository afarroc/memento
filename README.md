# MementoBloom - Sistema de Memoria Histórica para IA

**Estado:** Activo - Sprint 3 en progreso  
**Memoria:** 160 entradas indexadas  
**Commit:** c72c1fb (T3.5 completado)

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

---

## Proyectos registrados

| Proyecto | Entries | Estado |
|----------|---------|--------|
| mementobloom | 131 | Desarrollo |
| m360 | 22 | Bridge API implementado |
| Ventas_Porta | 15 | Catálogo retail |
| Administracion_UPN | 9 | Fase 2 GTD |

---

## Blockers

- **Management360:** Connection refused (servicio no disponible)

---

## Sprint 3 pendiente

- T3.1: Vault Fernet encoding
- T3.2: Exclusiones Git cliente
- T3.3: Validación .env
- T3.4: Sanitizar rutas

---

*Ver `docs/AUDITORIA_PROYECTO.md` para auditoría completa*