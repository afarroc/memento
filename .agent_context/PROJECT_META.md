# Memento Project Meta

Objetivo meta del usuario:

- Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico.
- El contexto debe ser legible por cualquier modelo, CLI o agente que pueda leer archivos locales.
- La continuidad debe basarse en archivos explícitos, handoffs, memoria compacta, estado Git y servicios verificables.
- Memento funciona como herramienta de memoria instalada dentro del proyecto cliente. El proyecto cliente es el proyecto principal.

Reglas universales de arranque:

1. Leer `.agent_context/PROJECT_META.md`.
2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe.
3. Leer `memory/personality/user_personality.md` para calibrar tono y estilo.
4. Leer `.agent_context/START_CONTEXT.md` si existe, como contexto local regenerable no trackeado.
5. Ejecutar `python3 tools/bootstrap_context.py --print` para obtener contexto compacto modelo-agnóstico.
6. Si se necesita iniciar como agente externo, ejecutar `python3 tools/session_start.py --print` (flujo completo: prepara seed + contexto + invoca internamente `session_bootstrap.py --print`). Para bootstrap modelo-agnóstico puro, usar `python3 tools/session_bootstrap.py --print` (alias de `--json`).
7. Leer los handoffs recientes del proyecto activo (ver `projects/` o `USER_CONTEXT.md`).
8. Verificar `git status`, último commit y cambios pendientes.
9. Verificar Redis/sala si la tarea involucra panel o comunicación.
10. Continuar desde el último handoff relevante sin pedir información ya registrada.

## Configuración del proyecto

Ver `.agent_context/secure/USER_CONTEXT.md` para configuración contextual específica.

Arquitectura de continuidad:

```text
SESSION.md → PROJECT_META.md → USER_CONTEXT.md → memory/personality/user_personality.md → tools/session_bootstrap.py → handoffs → memory_index.json → IA
```

Archivos críticos:

- `SESSION.md`: estado canónico de sesión, generado automáticamente, no trackeable.
- `.agent_context/PROJECT_META.md`: meta del proyecto, trackeable.
- `.agent_context/secure/USER_CONTEXT.md`: contexto local del usuario, no trackeable.
- `memory/personality/user_personality.md`: memoria de personalidad del usuario, no trackeable.
- `memory/graph/memory_index.json`: memoria compacta, no trackeable.
- `projects/*/HANDOFF_*.md`: handoffs locales del proyecto activo, no trackeables.
- `tools/session_bootstrap.py`: bootstrap universal para cualquier modelo, CLI o agente.
- `tools/context_builder.py`: contexto ranked para revisión más profunda.

## Personalidad del agente

El agente lee `memory/personality/user_personality.md` para calibrar tono, valores y estilo de comunicación.
Ver `docs/PERSONALIDAD_AGENTE.md` para la especificación completa.

## Neutralidad de agente

El proyecto no depende de ningún agente, modelo o CLI específico.
El directorio `.agent_context/` puede contener rutas propias de una herramienta local; si otro agente no las usa, debe ignorarlas y reconstruir el contexto desde `PROJECT_META.md`, `USER_CONTEXT.md`, `tools/bootstrap_context.py`, handoffs y estado Git.

Reglas de seguridad:

- No exponer secretos, tokens, contraseñas ni contenido de vault.
- No commitear ni pushear `.agent_context/START_CONTEXT.md`, `.agent_context/secure/USER_CONTEXT.md`, `memory/graph/*.json`, `.memento/`, `archive/`, handoffs ni datos de sesión.
- No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita.
- Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional.

Comandos base:

```bash
python3 tools/bootstrap_context.py --print
python3 tools/context_builder.py --limit 12
python3 tools/quick_scan.py <HANDOFF_PATH>
python3 tools/backup_local.py backup
```

Comandos opcionales:

```bash
python3 tools/optimize_agent.py --context
python3 tools/export_memory.py --format markdown --output docs/memory_export.md
```