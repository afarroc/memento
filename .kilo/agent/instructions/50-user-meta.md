# 50 Usuario y meta del proyecto

Contexto de usuario:
- Lee `.kilo/PROJECT_META.md` si existe.
- Lee `.kilo/USER_CONTEXT.md` si existe y úsalo como preferencias, objetivos, infraestructura y reglas operativas del usuario.
- No pidas información ya registrada en `.kilo/USER_CONTEXT.md`, handoffs o memoria compacta.
- Actualiza `.kilo/USER_CONTEXT.md` solo cuando el usuario revele preferencias, objetivos, restricciones, infraestructura o decisiones relevantes.

Meta del proyecto:
- Cada sesión debe poder continuar sin depender de un modelo específico.
- El contexto debe ser modelo-agnóstico y legible desde archivos locales.
- Prioriza continuidad sobre dependencias de una UI o modelo concreto.

Arranque recomendado:
- Ejecuta `python3 tools/bootstrap_context.py --print` cuando necesites reconstruir contexto para cualquier modelo.
- Ejecuta `python3 tools/optimize_agent.py --context` cuando necesites auditoría operativa.
- Ejecuta `python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8` para arranque rápido Kilo.

Seguridad:
- No expongas secretos ni contenido de vault.
- No trackees `.kilo/START_CONTEXT.md`, `.kilo/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni handoffs.
- No ejecutes operaciones destructivas sobre Redis, memoria o handoffs salvo instrucción explícita.
