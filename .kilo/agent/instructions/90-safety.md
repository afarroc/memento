# 90 Seguridad

Seguridad operativa:
- No expongas credenciales, secretos ni contenido de vault salvo que sea estrictamente necesario.
- No hagas commits, pushes o force pushes salvo solicitud explícita.
- No borres archivos, memoria, Redis, handoffs o índices salvo solicitud explícita.
- Si una operación puede ser destructiva, explícala antes de ejecutarla.
- Mantén compatibilidad con la configuración Kilo en `.kilo/kilo.json`.
- No subas `.kilo/START_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/` ni datos de sesión.

Prohibiciones operativas:
- No ejecutes limpiezas agresivas con `lsof/xargs kill -9` para cerrar puertos, procesos o servicios del sistema.
- Nunca uses comandos de eliminación genérica (kill, flush, delete) sobre servicios compartidos o aplicaciones activas.
- Si existe un servicio activo relevante (web, base de datos, chat, agentes), evita terminarlo sin una instrucción explícita del usuario.
- Antes de realizar cualquier operación potencialmente destructiva, expresa el impacto y espera confirmación.
