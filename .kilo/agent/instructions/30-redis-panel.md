# 30 Redis y panel

Redis de sala:
- Remoto: `192.168.18.59:6379`
- Cola: `memento_panel_items`
- Local: `http://127.0.0.1:8767/messages`
- Sala local: `python3 tools/sala.py`

Reglas:
- No ejecutes `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- Si necesitas levantar la sala, usa `python3 tools/sala.py` o `python3 tools/memento_kilo_start.py --services`.
- Verifica `/stats` y `/messages` cuando el usuario pregunte por el panel.
