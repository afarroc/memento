# MementoBloom Startup Context

Generated: 2026-06-28T01:50:46
Workspace: .
Project: mementobloom
Index entries: 167

## Startup instruction
Prepara la semilla progresiva del agente, lee el contexto inicial y continúa desde el último handoff relevante sin pedir información ya registrada.

## Project meta
- Path: `.agent_context/PROJECT_META.md`
- Estado: local/contextual
- Objetivo meta del usuario:
- - Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico.
- - El contexto debe ser legible por cualquier modelo, CLI o agente que pueda leer archivos locales.
- - La continuidad debe basarse en archivos explícitos, handoffs, memoria compacta, estado Git y servicios verificables.
- - Memento funciona como herramienta de memoria instalada dentro del proyecto cliente. El proyecto cliente es el proyecto principal.
- Reglas universales de arranque:
- 1. Leer `.agent_context/PROJECT_META.md`.
- 2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe.
- 3. Leer `memory/personality/user_personality.md` para calibrar tono y estilo.

## User context
- Path: `.agent_context/secure/USER_CONTEXT.md`
- Estado: local/contextual
- Actualizado: 2026-06-14T04:35:00-05:00
- - Idioma principal: español.
- - Estilo preferido: directo, técnico y orientado a acción.
- - Evitar conversación innecesaria.
- - Responder con resúmenes claros, comandos concretos y estado verificable.
- El usuario quiere que MementoBloom sea útil para que cada sesión iniciada sepa exactamente todo lo necesario sobre el usuario y el proyecto sin depender de un modelo específico.
- Cualquier modelo debería poder proseguir con la gestión del proyecto si puede leer:
- - `.agent_context/PROJECT_META.md`
- - `.agent_context/secure/USER_CONTEXT.md`

## Top recent memory
- h_HANDOFF_2026-06-27_225500_calibracion_m360_sync | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_225500_calibracion_m360_sync.md
  # HANDOFF - Calibración M360 y sincronización de memoria ## Datos básicos - Proyecto: mementobloom
- h_HANDOFF_2026-06-27_215200_sprint3_m360_sync | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_215200_sprint3_m360_sync.md
  # HANDOFF - Sincronización Sprint 3 en M360 ## Datos básicos - Proyecto: mementobloom - Fecha/hora:
- h_HANDOFF_2026-06-27_213600_sprint3_plan | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_213600_sprint3_plan.md
  # HANDOFF - Plan Sprint 3: Seguridad y configuración sensible ## Datos básicos - Proyecto: mementobl
- h_HANDOFF_2026-06-27_213100_cierre_sesion_sprint2 | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_213100_cierre_sesion_sprint2.md
  # HANDOFF - Cierre de sesión: Sprint 2 completado ## Datos básicos - Proyecto: mementobloom - Fecha/
- h_HANDOFF_2026-06-27_212700_cleanup_sprint2_cierre | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_212700_cleanup_sprint2_cierre.md
  # HANDOFF - Cleanup Sprint 2 y cierre de sesión ## Datos básicos - Proyecto: mementobloom - Fecha/ho
- h_HANDOFF_2026-06-27_183500_cierre_sesion | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_183500_cierre_sesion.md
  # HANDOFF - Cierre de sesión ## Datos básicos - Proyecto: mementobloom - Fecha/hora: 2026-06-27T18:3
- h_HANDOFF_2026-06-27_173306_cierre_sesion | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_173306_cierre_sesion.md
  # HANDOFF - Cierre de sesión ## Datos básicos - Proyecto: mementobloom - Fecha/hora: 2026-06-27T17:3
- h_HANDOFF_2026-06-27_170921_cierre_sesion | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_170921_cierre_sesion.md
  # HANDOFF - Cierre de sesión ## Datos básicos - Proyecto: mementobloom - Fecha/hora: 2026-06-27T17:0
- h_HANDOFF_2026-06-27_153645_redis_external_enforcement | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_153645_redis_external_enforcement.md
  # HANDOFF - Redis External Enforcement and Session Cleanup ## Datos básicos - Proyecto: mementobloom
- h_HANDOFF_2026-06-27_06_session_contract_fase2 | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_06_session_contract_fase2.md
  # HANDOFF - Cierre: Fase 2 SESSION_CONTRACT completada ## Datos básicos - Proyecto: mementobloom -
- h_HANDOFF_2026-06-27_05_session_contract_fase1 | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_05_session_contract_fase1.md
  # HANDOFF - Cierre: contrato de arranque Fase 1 (SESSION.md) ## Datos básicos - Proyecto: mementobl
- h_HANDOFF_2026-06-27_04_doc_sync_final | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_04_doc_sync_final.md
  # HANDOFF - Documentación y sincronización de memoria final ## Datos básicos - Proyecto: mementoblo
- h_HANDOFF_2026-06-27_03_cierre_m360_api_v1 | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_03_cierre_m360_api_v1.md
  # HANDOFF - Cierre: integración M360 API v1 completada ## Datos básicos - Proyecto: mementobloom -
- h_HANDOFF_2026-06-27_02_m360_integration_completed | HANDOFF | project=mementobloom | ts=2026-06-27 | path=projects/mementobloom/HANDOFF_2026-06-27_02_m360_integration_completed.md
  # HANDOFF - M360 API v1 + Integración completa ## Datos básicos - Proyecto: mementobloom - Fecha/ho

## Git state
- 4 cambio(s): M .agent_context/START_CONTEXT.md,  M SESSION.md, ?? docs/RECONCILIACION_M360_ESTADO_ACTUAL_20260628.md, ?? docs/RECONCILIACION_START_CONTEXT_20260628.md

## Services
Redis OK at 192.168.18.59:6379 | Sala OK at http://127.0.0.1:8767 | Panel OK at http://127.0.0.1:8766

## Safe next-session commands
- `python3 tools/session_start.py --quick --limit 8` (proyecto por defecto: mementobloom)
- `python3 tools/bootstrap_context.py --print` imprime contexto universal para cualquier modelo.
- `python3 tools/optimize_agent.py --context` audita y resume el entorno operativo.
- `python3 tools/session_start.py --services-only`
