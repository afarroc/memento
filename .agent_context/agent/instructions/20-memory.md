# 20 Memoria

Memoria operativa:
- Prioriza HANDOFF recientes.
- Usa `python3 tools/quick_scan.py <HANDOFF_PATH>` para indexar handoffs nuevos.
- Usa `python3 tools/context_builder.py --limit N` para obtener contexto ranked.
- Mantén trazabilidad entre seed → instrucciones → contexto → handoff → acción.
- Si una tarea modifica memoria, handoffs o índices, valida que el cambio sea intencional.

Fuentes de verdad (en orden de prioridad):
1. `SESSION.md` — estado canónico de sesión.
2. `.memento_runtime/session_canonical.json` — backup canónico local inmutable (NO depende de Git).
3. `projects/*/HANDOFF_*.md` — registros de gestión y cierres.
4. `docs/` — documentación permanente del proyecto.
5. Git — último recurso extremo. No confiar en él como fuente primaria entre sesiones (puede reescribirse, force-pushear, o clonarse sin historial).

No borrar:
- No borres memoria.
- No borres Redis.
- No borres handoffs.
- No elimines índices salvo instrucción explícita.

Lecciones aprendidas (2026-06-28):
- Git NO es fuente de verdad confiable entre sesiones. Usar `.memento_runtime/session_canonical.json`.
- `.agent_context/` es para contexto del agente (semillas, instrucciones, START_CONTEXT regenerable). NUNCA poner documentación permanente ni registros de gestión ahí.
- Los registros de gestión (conciliaciones, auditorías, cierres) van en `projects/mementobloom/HANDOFF_*.md` o `docs/`.
- `START_CONTEXT.md` es regenerable y no se trackea. Si aparece en `git status`, revisar si está en el índice (no debería).
