# MementoBloom Project Meta

Objetivo meta del usuario:

- Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico.
- El contexto debe ser legible por cualquier modelo, CLI o agente que pueda leer archivos locales.
- La continuidad debe basarse en archivos explícitos, handoffs, memoria compacta, estado Git y servicios verificables.

Reglas universales de arranque:

1. Leer `.kilo/PROJECT_META.md`.
2. Leer `.kilo/secure/USER_CONTEXT.md` si existe.
3. Leer `.kilo/START_CONTEXT.md` si existe, como contexto local regenerable no trackeado.
4. Ejecutar `python3 tools/bootstrap_context.py --print` para obtener contexto compacto modelo-agnóstico.
5. Leer los handoffs recientes del proyecto activo (ver `projects/` o `USER_CONTEXT.md`).
6. Verificar `git status`, último commit y cambios pendientes.
7. Verificar Redis/sala si la tarea involucra panel o comunicación.
8. Continuar desde el último handoff relevante sin pedir información ya registrada.

## Configuración del proyecto

Ver `.kilo/secure/USER_CONTEXT.md` para configuración contextual específica.

Arquitectura de continuidad:

```text
PROJECT_META.md → USER_CONTEXT.md → START_CONTEXT.md → tools/bootstrap_context.py → handoffs → memory_index.json → IA
```

Archivos críticos:

- `.kilo/PROJECT_META.md`: meta del proyecto, trackeable.
- `.kilo/secure/USER_CONTEXT.md`: contexto local del usuario, no trackeable.
- `.kilo/START_CONTEXT.md`: contexto local regenerable, no trackeable.
- `memory/graph/memory_index.json`: memoria compacta, no trackeable.
- `projects/*/HANDOFF_*.md`: handoffs locales del proyecto activo, no trackeables.
- `tools/bootstrap_context.py`: bootstrap universal para cualquier modelo, CLI o agente.
- `tools/context_builder.py`: contexto ranked para revisión más profunda.

## Neutralidad de agente

El proyecto no depende de ningún agente, modelo o CLI específico.
El directorio `.kilo/` puede contener rutas propias de una herramienta local; si otro agente no las usa, debe ignorarlas y reconstruir el contexto desde `PROJECT_META.md`, `USER_CONTEXT.md`, `tools/bootstrap_context.py`, handoffs y estado Git.

Reglas de seguridad:

- No exponer secretos, tokens, contraseñas ni contenido de vault.
- No commitear ni pushear `.kilo/START_CONTEXT.md`, `.kilo/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, handoffs ni datos de sesión.
- No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita.
- Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional.

Comandos base:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/context_builder.py --limit 12
python3 tools/quick_scan.py <HANDOFF_PATH>
```

Comandos opcionales:
```bash
python3 tools/optimize_agent.py --context
```
