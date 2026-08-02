# context/lecciones_aprendidas.md — Lecciones del agente tutor

- Git NO es fuente de verdad entre sesiones; usar `estado/indice_cursos.md` del agente y `SESSION.md`.
- La credencial SSH de termux está en `mementobloom/.env` (TERMUX_ROOT_*) y `.memento/vault.json` (`termux_root`), NO en `.agent_context/secure/VAULT.md`.
- MariaDB termux: datadir real es `/data/data/com.termux/files/usr/var/lib/mysql`, NO `$HOME/.mariadb/data`.
- Al recrear curso: validar render con sesión activa en M360 antes de marcar completado.
- Escapar `$` de moneda en contenido HTML para M360 (MathJax).
- API M360 POST/PATCH puede fallar por validación de tutor → SQL directo como workaround, registrar en `estado/indice_cursos.md`.
