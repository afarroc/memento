# MementoBloom Bootstrap Context

Generated: 2026-06-27T14:47:12
Project: mementobloom
Working directory: /Volumes/Macintosh HD - Datos/mementobloom

## User and project meta
- PROJECT_META.md: OK
- USER_CONTEXT.md: OK
- START_CONTEXT.md: OK
- Agent init: OK
- USER_CONTEXT ignored by Git: OK

## Project meta summary
Objetivo meta del usuario: - Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico. - El contexto debe ser legible por cualquier modelo, CLI o agente que pueda leer archivos locales. - La continuidad debe basarse en archivos explícitos, handoffs, memoria compacta, estado Git y servicios verificables. - Memento funciona como herramienta de memoria instalada dentro del proyecto cliente. El proyecto cliente es el proyecto principal. Reglas universales de arranque: 1. Leer `.agent_context/PROJECT_META.md`. 2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe. 3. Leer `memory/personality/user_personality.md` para calibrar tono y estilo. 4. Leer `.agent_context/START_CONTEXT.md` si existe, como contexto local regenerable no trackeado. 5. Ejecutar `python3 tools/bootstrap_context.py --print` para obtener contexto compacto modelo-agnóstico. 6. Si se necesita iniciar como agente externo, ejecutar `python3 tools/session_start.py --print --launch-agent` con `MEMENTO_AGENT_CMD` configurado. 7. Leer los handoffs recientes del proyecto activo (ver `projects/` o `USER_CONTEXT.md`). 8. Verificar `git status`, último commit y cambios pendientes. 9. Verificar Redis/sala si la tarea involucra panel o comunicación. 10. Continuar desde el último handoff relevante sin pedir información ya registrada. Ver `.agent_context/secure/USER_CONTEXT.md` para configuración contextual específica. Arquitectura de continuidad: ```text SESSION.md → PROJECT_META.md → USER_CONTEXT.md → memory/personality/user_personality.md → tools/session_bootstrap.py → handoffs → memory_index.json → IA ``` Archivos críticos: - `SESSION.md`: estado canónico de sesión, generado automáticamente, no trackeable. - `.agent_context/PROJECT_META.md`: meta del proyecto, trackeable. - `.agent_context/secure/USER_CONTEXT.md`: contexto local del usuario, no trackeable. - `memory/personality/user_personality.md`: memoria de personalidad del usuario, no trackeable. - `memory/graph/memory_index.json`: memoria compacta, no trackeable. - `projects/*/HANDOFF_*.md`: handoffs locales del proyecto activo, no trackeables. - `tools/session_bootstrap.py`: bootstrap universal para cualquier modelo, CLI o agente. - `tools/context_builder.py`: contexto ranked para revisión más profunda. El agente lee `memory/personality/user_personality.md` para calibrar tono, valores y estilo de comunicación. Ver `docs/PERSONALIDAD_AGENTE.md` para la especificación completa. El proyecto no depende de ningún agente, modelo o CLI específico. El directorio `.agent_context/` puede contener rutas propias de una herramienta local; si otro agente no las usa, debe ignorarlas y reconstruir el contexto desde `PROJECT_META.md`, `USER_CONTEXT.md`, `tools/bootstrap_context.py`, handoffs y estado Git. Reglas de seguridad: - No exponer secretos, tokens, contraseñas ni contenido de vault. - No commitear ni pushear `.agent_context/START_CONTEXT.md`, `.agent_context/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, handoffs ni datos de sesión. - No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita. - No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita. - Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional. Comandos base: ```bash python3 tools/bootstrap_context.py --print python3 tools/context_builder.py --limit 12 python3 tools/quick_scan.py <HANDOFF_PATH> python3 tools/backup_local.py backup ``` Comandos opcionales: ```bash python3 tools/optimize_agent.py --context python3 tools/export_memory.py --format markdown --output docs/memory_export.md ```

## User context summary
Actualizado: 2026-06-14T04:35:00-05:00 - Idioma principal: español. - Estilo preferido: directo, técnico y orientado a acción. - Evitar conversación innecesaria. - Responder con resúmenes claros, comandos concretos y estado verificable. El usuario quiere que MementoBloom sea útil para que cada sesión iniciada sepa exactamente todo lo necesario sobre el usuario y el proyecto sin depender de un modelo específico. Cualquier modelo debería poder proseguir con la gestión del proyecto si puede leer: - `.agent_context/PROJECT_META.md` - `.agent_context/secure/USER_CONTEXT.md` - `.agent_context/START_CONTEXT.md` - `tools/bootstrap_context.py` - handoffs recientes - `memory/graph/memory_index.json` - estado Git - servicios locales/remotos relevantes 1. `mementobloom` 2. `Management360` 3. `Ventas_Porta` - Workspace actual: `/Volumes/Macintosh HD - Datos/mementobloom` - Workspace raíz: `/Volumes/Macintosh HD - Datos` - Redis remoto de sala: `192.168.18.59:6379` - Cola Redis: `memento_panel_items` - Sala local: `http://127.0.0.1:8767` - Panel local conocido: `http://127.0.0.1:8766` - Fuente remota Termux registrada: `192.168.18.59:8022` - Usuario remoto Termux: `u0_a212` - Commit actual: `04f3e6b` (Fix USER_CONTEXT path in optimize_agent.py to secure location) - Memoria indexada: 59 entradas Mejorar el entorno del proyecto para que cada sesión pueda reconstruir contexto de usuario y proyecto de forma modelo-agnóstica. - No pedir datos ya registrados en memoria. - Continuar desde el último handoff relevante. - No trackear contexto local regenerable. - No commitear sin solicitud explícita. - No ejecutar operaciones destructivas. - Publicar resúmenes en la sala cuando el usuario lo pida.

## Git state
- Commit: 0f61d3e feat(contract): implementar Fase 1 SESSION_CONTRACT
- Pending changes: 2
  - M SESSION.md
  - ?? gtd_memento/

## Diff stat
SESSION.md | 32 ++++++++++++--------------------
 1 file changed, 12 insertions(+), 20 deletions(-)

## Memory
- Index: memory/graph/memory_index.json (109 entries)
- By type: {"COMPONENT": 1, "CONTEXT": 1, "HANDOFF": 106, "NOTE": 1}
- By project: {"Ventas_Porta": 10, "mementobloom": 99}

## Latest handoffs
- h_HANDOFF_2026-06-27_05_session_contract_fase1 | mementobloom | 2026-06-27 | # HANDOFF - Cierre: contrato de arranque Fase 1 (SESSION.md) ## Datos básicos - Proyecto: mementobl
- h_HANDOFF_2026-06-27_04_doc_sync_final | mementobloom | 2026-06-27 | # HANDOFF - Documentación y sincronización de memoria final ## Datos básicos - Proyecto: mementoblo
- h_HANDOFF_2026-06-27_03_cierre_m360_api_v1 | mementobloom | 2026-06-27 | # HANDOFF - Cierre: integración M360 API v1 completada ## Datos básicos - Proyecto: mementobloom -
- h_HANDOFF_2026-06-27_02_m360_integration_completed | mementobloom | 2026-06-27 | # HANDOFF - M360 API v1 + Integración completa ## Datos básicos - Proyecto: mementobloom - Fecha/ho
- h_HANDOFF_2026-06-27_01_m360_api_v1 | mementobloom | 2026-06-27 | # HANDOFF - M360 API v1 + Memoria sincronizada ## Datos básicos - Proyecto: mementobloom - Fecha/ho

## Top context entries
- h_HANDOFF_2026-06-27_05_session_contract_fase1 | HANDOFF | mementobloom | 2026-06-27 | # HANDOFF - Cierre: contrato de arranque Fase 1 (SESSION.md) ## Datos básicos - Proyecto: mementobl
- h_HANDOFF_2026-06-27_04_doc_sync_final | HANDOFF | mementobloom | 2026-06-27 | # HANDOFF - Documentación y sincronización de memoria final ## Datos básicos - Proyecto: mementoblo
- h_HANDOFF_2026-06-27_03_cierre_m360_api_v1 | HANDOFF | mementobloom | 2026-06-27 | # HANDOFF - Cierre: integración M360 API v1 completada ## Datos básicos - Proyecto: mementobloom -
- h_HANDOFF_2026-06-27_02_m360_integration_completed | HANDOFF | mementobloom | 2026-06-27 | # HANDOFF - M360 API v1 + Integración completa ## Datos básicos - Proyecto: mementobloom - Fecha/ho
- h_HANDOFF_2026-06-27_01_m360_api_v1 | HANDOFF | mementobloom | 2026-06-27 | # HANDOFF - M360 API v1 + Memoria sincronizada ## Datos básicos - Proyecto: mementobloom - Fecha/ho
- h_HANDOFF_2026-06-26_verificacion_recreacion | HANDOFF | mementobloom | 2026-06-26 | # HANDOFF - Verificación y Recreación Proyecto 60 ## Datos básicos - **Proyecto:** mementobloom - *
- h_HANDOFF_2026-06-26_verificacion_m360_fix_signal | HANDOFF | mementobloom | 2026-06-26 | # HANDOFF - Verificacion M360 y fix signal inbox ## Datos básicos - **Proyecto:** mementobloom - **
- h_HANDOFF_2026-06-26_sincronizacion_sprint0 | HANDOFF | mementobloom | 2026-06-26 | # HANDOFF - Sincronización de memoria y estado Sprint 0 ## Datos básicos - **Proyecto:** mementoblo

## Services
Redis NO at localhost:6379 | Sala OK at http://127.0.0.1:8767 | Panel OK at http://127.0.0.1:8766 cache

## Bootstrap commands
- python3 tools/bootstrap_context.py --print
- python3 tools/doctor.py --startup
- python3 tools/selftest.py
- python3 tools/context_builder.py --limit 12
- python3 tools/quick_scan.py <HANDOFF_PATH>

## Optional agent-specific commands
- python3 tools/optimize_agent.py --context

