# 90 Seguridad

Seguridad operativa:
- No expongas credenciales, secretos ni contenido de vault salvo que sea estrictamente necesario.
- No hagas commits, pushes o force pushes salvo solicitud explícita.
- No borres archivos, memoria, Redis, handoffs o índices salvo solicitud explícita.
- Si una operación puede ser destructiva, explícala antes de ejecutarla.
- Mantén compatibilidad con la configuración local en `.agent_context/agent_config.json` cuando esa herramienta esté en uso.
- No subas `.agent_context/START_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni datos de sesión.

Prohibiciones operativas:
- No ejecutes limpiezas agresivas con `lsof/xargs kill -9` para cerrar puertos, procesos o servicios del sistema.
  **Caso crítico**: `lsof -ti:8000 | xargs kill -9` detiene el navegador y todos sus procesos asociados al puerto 8000, no solo el servidor Django.
  **Alternativa segura**: usar el PID del proceso específico (`ps aux | grep manage.py`) o `kill -HUP <pid>` para recargar sin matar procesos relacionados.
- Nunca uses comandos de eliminación genérica (kill, flush, delete) sobre servicios compartidos o aplicaciones activas.
- Si existe un servicio activo relevante (web, base de datos, chat, agentes), evita terminarlo sin una instrucción explícita del usuario.
- Antes de realizar cualquier operación potencialmente destructiva, expresa el impacto y espera confirmación.
