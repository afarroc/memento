# 20 Memoria

Memoria operativa:
- Prioriza HANDOFF recientes.
- Usa `python3 tools/quick_scan.py <HANDOFF_PATH>` para indexar handoffs nuevos.
- Usa `python3 tools/context_builder.py --limit N` para obtener contexto ranked.
- Mantén trazabilidad entre seed → instrucciones → contexto → handoff → acción.
- Si una tarea modifica memoria, handoffs o índices, valida que el cambio sea intencional.

No borrar:
- No borres memoria.
- No borres Redis.
- No borres handoffs.
- No elimines índices salvo instrucción explícita.
