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
5. Leer los handoffs recientes de `projects/mementobloom`.
6. Verificar `git status`, último commit y cambios pendientes.
7. Verificar Redis/sala si la tarea involucra panel o comunicación.
8. Continuar desde el último handoff relevante sin pedir información ya registrada.

Prioridad de proyectos:

Ver `.kilo/secure/USER_CONTEXT.md` para lista contextual del usuario.

Arquitectura de continuidad:

```text
PROJECT_META.md → USER_CONTEXT.md → START_CONTEXT.md → tools/bootstrap_context.py → handoffs → memory_index.json → IA
```

Archivos críticos:

- `.kilo/PROJECT_META.md`: meta del proyecto, trackeable.
- `.kilo/secure/USER_CONTEXT.md`: contexto local del usuario, no trackeable.
- `.kilo/START_CONTEXT.md`: contexto Kilo regenerable, no trackeable.
- `memory/graph/memory_index.json`: memoria compacta, no trackeable.
- `projects/mementobloom/HANDOFF_*.md`: handoffs locales, no trackeables.
- `tools/bootstrap_context.py`: bootstrap universal para cualquier modelo.
- `tools/optimize_agent.py`: auditoría y optimización del agente.

Reglas de seguridad:

- No exponer secretos, tokens, contraseñas ni contenido de vault.
- No commitear ni pushear `.kilo/START_CONTEXT.md`, `.kilo/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, handoffs ni datos de sesión.
- No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita.
- Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional.

Comandos base:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context
python3 tools/memento_kilo_start.py --quick --project=mementobloom --limit 8
python3 tools/context_builder.py --limit 12
python3 tools/quick_scan.py <HANDOFF_PATH>
```
