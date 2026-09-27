## Próxima sesión

```bash
python3 tools/session_start.py --print
python3 tools/quick_scan.py
```

### Estado actual
- **Proyecto activo:** mementobloom
- **mementobloom:** sesión de corrección de nomenclatura completada. Documentación actualizada. Servicios STARTED: panel (8766), sala (8767), redis OK.
- **Memoria indexada:** 522 entries
- **Tickets:** TICK-0054 abierto para `poco_xiaomi` (POCO-CAM-001). Corrección global de nomenclatura aplicada a tickets y tareas Mango360.
- **Clientes registrados:** 14 proyectos cliente con nomenclatura documentada.

### Clientes y nomenclatura

| Cliente | M360 ID | Nomenclatura | Estado |
|---------|---------|--------------|--------|
| perfil_personal | 24 | `PERFIL-*` | Activo |
| TaxiLima2026 | 23 | `TAXI-*` | Activo |
| Carpinteria | 25 | `CARP-*` | Activo |
| poco_xiaomi | 26 | `POCO-*` | Activo |
| Management360 | 22 | `M360-*`, `DIGIT-*`, `CV-REVIEW-*`, `TASK-BITACORA-*` | Activo |

### Próximos pasos prioritarios
1. Resolver tareas Mango360 restantes sin prefijo documentado:
   - Management360 tasks 188-194, 204
   - perfil_personal tasks 298-300, 309
2. Resolver duplicado `TAXI-SIM-008` en Mango360 (tasks 314 y 316)
3. Crear tareas Mango360 faltantes para `poco_xiaomi`: POCO-SERV-001, POCO-SERV-002, POCO-DATA-001
4. Sincronizar tickets corregidos con panel/bridge cuando esté activo

### Trabajo en progreso en mementobloom
- Sistema de tickets local (`core/tickets.py`, `tools/ticket.py`) operativo
- Nomenclatura de tareas documentada por proyecto en `projects/<cliente>/docs/nomenclatura_tareas.md`
- `m360_task_results.json` contiene resultados de creación de tickets M360 (pendiente de limpiar/archivar)

### Notas
- `SESSION.md` es la fuente de verdad canónica (JSON).
- `.agent_context/START_CONTEXT.md` se regenera con `bootstrap_context.py --print`.
- Para renacimiento: ejecutar `session_start.py --print`.
