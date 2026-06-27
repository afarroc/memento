## Próxima sesión

```bash
python3 tools/session_bootstrap.py
python3 tools/session_render.py
python3 tools/bootstrap_context.py --print
python3 tools/quick_scan.py
```

- `SESSION.md` es la fuente de verdad canónica (JSON).
- `SESSION_REPORT.md` es la vista markdown para humanos.
- `.agent_context/START_CONTEXT.md` se regenera con `bootstrap_context.py --print`.
- Para renacimiento: ejecutar `session_bootstrap.py` y `bootstrap_context.py --print`.
