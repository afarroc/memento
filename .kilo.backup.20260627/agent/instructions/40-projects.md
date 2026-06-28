# 40 Proyectos prioritarios

Prioriza estos proyectos cuando haya ambigüedad:
1. `projects/mementobloom`
2. `projects/Management360`
3. `projects/Ventas_Porta`

Para MementoBloom:
- La semilla del agente está en `.kilo/agent/init.md`.
- El agente generado está en `.kilo/agent/memento-curador.md`.
- El contexto de arranque puede regenerarse localmente en `.kilo/START_CONTEXT.md`, pero no debe trackearse.

Para Management360 y Ventas_Porta:
- Usa sus HANDOFF recientes para reconstruir estado.
- No asumas que servicios remotos están activos; verifica antes de operar.
