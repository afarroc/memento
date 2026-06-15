# 30 Redis y panel

Redis de sala:
- Ver `.kilo/secure/USER_CONTEXT.md` o `.kilo/secure/SECURE.md` para configuración de host/puerto.
- Sala local: `python3 tools/sala.py`

Reglas:
- No ejecutes `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- Si necesitas levantar la sala, usa `python3 tools/sala.py` o `python3 tools/memento_kilo_start.py --services`.
- Verifica `/stats` y `/messages` cuando el usuario pregunte por el panel.