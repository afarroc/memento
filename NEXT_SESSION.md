## Próxima sesión

```bash
python3 tools/session_start.py --print
python3 tools/quick_scan.py
```

### Estado actual
- **Proyecto activo:** TaxiLima2026
- **TaxiLima2026:** arquitectura híbrida del motor reestructurada en `sim/flame_like/`, `sim/rules/`, `sim/domain/`. Mesa-Frames/Polars operativos en venv. `MesaFramesEngine` real implementado. `Coordinator` integrado en `sim/api.py`. Persistencia JSON implementada en `sim/api.py.load()`. Vista mantenida activamente: web Django en `web/`. Vistas no mantenidas: `dashboard/app.py` (Streamlit), `sim_gui/main.py` (Tkinter), `frontend/` (SvelteKit). CRM Mango360: `75` tareas totales (`20` completed). Docs sincronizados.
- **Management360:** API v1 M360 con filtros corregidos
- **Memoria indexada:** 495 entries
- **CRM limpieza:** eliminadas tareas de prueba `mementobloom auth test` de Carpinteria ID 25 y perfil_personal ID 24.
- **Tickets:** TICK-0028 abierto para backend Mesa-Frames real y coordinador integrado.

### Próximos pasos prioritarios - TaxiLima2026
1. **Completado:** Migración a Mesa-Frames con Polars — instalado y backend `MesaFramesEngine` funcional
2. **Completado:** Integración de `Coordinator` en `sim/api.py` — desacopla UI del backend
3. **Completado:** Persistencia de partidas — `sim/api.py.load()` implementado con formato JSON
4. **Completado:** Vista web Django mantenida activamente; `dashboard/app.py`, `sim_gui/main.py` y `frontend/` marcados como no mantenidos
5. Pendiente: completar consumo de `/api/simulation/decisions/` en templates Django si se requiere mostrar decisiones del `Coordinator`
6. Pendiente: corregir bug pre-existente de `MetricsCalculator`/`WorldState` si se requieren métricas completas en `MesaFramesEngine`
7. Pendientes no técnicas:
   - Validar cotización renting `TAXI-FIN-006` con Tair Renting / LeasyAuto cuando corresponda.
   - Preparar despliegue o compartición del sitio Django cuando corresponda.
8. Trabajo en progreso en mementobloom:
   - Sistema de tickets local (`core/tickets.py`, `tools/ticket.py`) en desarrollo.
   - `m360_task_results.json` contiene resultados de creación de tickets M360 (pendiente de limpiar/archivar).

### Notas
- `SESSION.md` es la fuente de verdad canónica (JSON).
- `.agent_context/START_CONTEXT.md` se regenera con `bootstrap_context.py --print`.
- Para renacimiento: ejecutar `session_start.py --print`.
