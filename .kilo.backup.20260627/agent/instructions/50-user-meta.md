# 50 Usuario y meta del proyecto

Contexto de usuario:
- Lee `.kilo/PROJECT_META.md` si existe.
- Si existe `.kilo/secure/USER_CONTEXT.md`, úsalo como preferencias, objetivos, infraestructura y reglas operativas locales.
- No pidas información ya registrada en `.kilo/secure/USER_CONTEXT.md`, handoffs o memoria compacta.
- Actualiza `.kilo/secure/USER_CONTEXT.md` solo cuando el usuario revele preferencias, objetivos, restricciones, infraestructura o decisiones relevantes.

Meta del proyecto:
- Cada sesión debe poder continuar sin depender de un modelo específico.
- El contexto debe ser modelo-agnóstico y legible desde archivos locales.
- Prioriza continuidad sobre dependencias de una UI o modelo concreto.
- Python Portable: `.kilo/USER_CONTEXT.md` debe poder ejecutarse desde cualquier carpeta con `python3 <path>` sin rutas absolutas.
- Python Portable: Usa `Path(__file__).resolve().parent` para crear rutas relativas seguras dentro del proyecto.
- Python Portable: No uses rutas absolutas hardcodeadas como `/Users/...`, `/Volumes/...`, ni referencias a carpetas externas al repo.
- Python Portable: Asegura que el código de herramientas pueda clonarse en `/home/usuario/mementobloom` o `/mnt/c/Users/.../mementobloom` y seguir funcionando.
- Python Portable: Cualquier ruta dentro del proyecto debe crearse relativa al archivo `tools/` o al root del repo, no desde la ubicación actual del usuario.

Arranque recomendado:
- Ejecuta `python3 tools/bootstrap_context.py --print` cuando necesites reconstruir contexto para cualquier modelo.
- Ejecuta `python3 tools/optimize_agent.py --context` cuando necesites auditoría operativa.
- Ejecuta `python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8` para arranque rápido Kilo.

Seguridad:
- No expongas secretos ni contenido de vault.
- No trackees `.kilo/START_CONTEXT.md`, `.kilo/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, `.kilo/secure/*` ni handoffs.
- No ejecutes operaciones destructivas sobre Redis, memoria o handoffs salvo instrucción explícita.
