# Continuidad - Próxima sesión

Generado: 2026-06-16T05:21:14-05:00
Base: `ea27eb3 Fix: Prevent shell injection in launch_external_agent`

## Estado actual

- Rama: `master` (sincronizada con `origin/master`)
- Pendientes de commit: `sala.py`, plantillas nuevas de agente, `agent-local/`
- Handoff cierre: `projects/mementobloom/HANDOFF_2026-06-16_051845_cierre_sesion.md`
- Memoria: 66 entradas indexadas

## Qué quedó listo

- Refactor CLI-agnóstico completado: `memento_install` ya no está acoplado a Kilo
- Agentes genéricos: `.agent_context/agent/agent-main.md` y `.agent_context/agent/agent-onboarding.md`
- Seguridad: `shell=True` reemplazado por allowlist + argv parser en `tools/session_start.py`
- ONBOARDED marker solo se escribe si el onboarding termina con código 0

## Qué falta (próximos pasos inmediatos)

1. Commit de pendientes
```bash
git add sala.py .agent_context/agent/agent-main.md .agent_context/agent/agent-onboarding.md agent-local/
git commit -m "Move generic agent templates to .agent_context/agent and keep .kilo fallback"
git push
```

2. Decidir destino de `agent-local/`
- Opción A: eliminarlo (workspace temporal)
- Opción B: moverlo a `.agent_context/agent/templates/` como respaldo oficial
- Opción C: dejarlo opcional en `.github/` o `templates/agents/`

3. Ajustar `memento_install` para volver a detectar CLI Kilo solo como opción ya no default
- Actualmente detecta `kilo`, `claude`, `code`
- Cuando no hay CLI, guardar solo contexto; no exigir agente

4. End-to-end del installer
```bash
./memento_install
```

## Contexto архитекónico para proseguir

- Core: `tools/session_start.py`, `tools/bootstrap_context.py`, `tools/optimize_agent.py`
- Agente por defecto: `.agent_context/agent/agent-main.md`
- Onboarding: `.agent_context/agent/agent-onboarding.md`
- Backward-compat names: `.agent_context/agent/memento-curador.md`, `.agent_context/agent/memento-onboarding.md`
- Contexto seguro: `.agent_context/secure/` (USER_CONTEXT.md, AGENT_CMD.env, ONBOARDED)
- Comandos válidos:
```bash
python3 tools/session_start.py --quick --limit 8
python3 tools/bootstrap_context.py --print
python3 tools/optimize_agent.py --context
./memento_start --services
```

## Notas

- El repo está limpio: `projects/mementobloom/` y `memory/graph/*.json` NO están trackeados (son locales)
- Un usuario que clone verá 0 handoffs y podrá crear los suyos propios
- Los handoffs actuales son histórico de auto-desarrollo (ver `archive/bootstrap-handoffs/` cuando se migre)
- Para producción: usar `./memento_install` en cualquier workspace nuevo

## Uso como biblioteca en workspace cliente

1. Clonar mementobloom como subdirectorio:
   ```
   cd /mi/workspace
   git clone <memento-repo> mementobloom
   ```

2. Opcional: setear `MEMENTO_WORKSPACE` (o el script detecta automáticamente si `.git` está en el workspace padre):
   ```
   export MEMENTO_WORKSPACE=/mi/workspace
   ```

3. Indexar handoffs existentes:
   ```
   python3 mementobloom/tools/quick_scan.py
   ```

4. Verificar estado:
   ```
   python3 mementobloom/tools/session_start.py --quick --limit 8
   ```

5. Los archivos creados:
   - `/mi/workspace/.memento/memory/graph/memory_index.json` - memoria del proyecto
   - `/mi/workspace/.agent_context/` - contexto y configuración
