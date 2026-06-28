# PROJECT_CONTEXT.md — MementoBloom

## Objetivo

- Cada sesión iniciada debe poder continuar la gestión del proyecto sin depender de un modelo específico.
- El contexto debe ser legible por cualquier agente, CLI o herramienta que pueda leer archivos locales.
- La continuidad se apoya en archivos explícitos, handoffs, memoria compacta (`memory_index.json`), estado Git y servicios verificables.
- MementoBloom es el proyecto activo; Memento funciona como herramienta de memoria instalada dentro de este proyecto.

---

## Estructura del proyecto

```text
mementobloom/
├── .agent_context/
│   ├── PROJECT_META.md
│   ├── PROJECT_CONTEXT.md
│   ├── START_CONTEXT.md
│   ├── USER_CONTEXT.md
│   ├── SECURE.md
│   └── agent/
│       ├── init.md
│       ├── agent-main.md
│       └── instructions/
│           ├── 00-core.md
│           ├── 10-context.md
│           ├── 10-personality.md
│           ├── 20-memory.md
│           ├── 30-redis-panel.md
│           ├── 40-projects.md
│           ├── 50-user-meta.md
│           └── 90-safety.md
├── tools/
│   ├── session_bootstrap.py
│   ├── project_status.py
│   ├── doctor.py
│   ├── sync_memory.py
│   ├── export_memory.py
│   ├── quick_scan.py
│   └── ...
├── projects/
│   ├── mementobloom/
│   │   └── HANDOFF_*.md
│   └── ...
├── memory/
│   └── graph/
│       └── memory_index.json
├── SESSION.md
└── .env
```

---

## Arquitectura de continuidad

```text
SESSION.md ← PROJECT_META.md ← PROJECT_CONTEXT.md ← USER_CONTEXT.md
     ↓              ↓                   ↓
 tools/session_bootstrap.py
     ↓
  handoffs + memory_index.json + estado Git + servicios
```

### Reglas de arranque (modelo-agnósticas)

1. Leer `.agent_context/PROJECT_META.md` y este archivo.
2. Leer `.agent_context/secure/USER_CONTEXT.md` si existe.
3. Leer `memory/personality/user_personality.md` para calibrar tono y estilo.
4. Ejecutar `python3 tools/bootstrap_context.py --print` para obtener contexto compacto.
5. Leer los handoffs más recientes del proyecto activo (ver `projects/mementobloom/`).
6. Verificar `git status`, último commit y cambios pendientes.
7. Verificar servicios (`sala`, `panel`, `redis`) si la tarea toca flujos del panel.
8. Continuar desde el último handoff relevante **sin pedir información ya registrada**.

---

## Variables de entorno y configuración

### Valores efectivos actuales

```bash
REDIS_HOST=192.168.18.59
REDIS_PORT=6379
SALA_HOST=127.0.0.1
SALA_PORT=8767
PANEL_HOST=127.0.0.1
PANEL_PORT=8766
REDIS_KEY=memento_panel_items:mementobloom
```

**Notas:**

- `REDIS_HOST` es **obligatorio** y no tiene fallback a `localhost`.
- Estas variables se cargan automáticamente desde `.env` en `core/services.py`.
- El panel usa `SALA_HOST`/`PANEL_HOST`; el panel y la sala ya no tienen rutas hardcodeadas.

---

## Servicios

| Servicio | Estado | URL / Host |
|----------|--------|------------|
| sala | ✅ OK | `http://127.0.0.1:8767/stats` |
| panel | ✅ OK | `http://127.0.0.1:8766/` |
| redis | ✅ OK | `192.168.18.59:6379` |

### Variabilidad por herramienta

- `doctor.py`: usa `core/health.py` → cache en `.memento_runtime/health_cache.json`
- `session_bootstrap.py`: parsea salida de `doctor.py`
- `project_status.py`: consulta directamente `doctor.py`

Conclusión operativa: la fuente fiable es la respuesta directa de `doctor.py` en modo fresco; si hay dudas, purgar la cache.

---

## Git

- **Rama principal:** `master`
- **Último commit:** `e22e51a` — `feat(status): converge panel/sala service reporting and purge stale cache`
- **Estado canónico:** `SESSION.md`
- **Handoffs:** no trackeados por `.gitignore`
- **Memoria:** no trackeada (`memory/graph/*.json` excluido)

---

## Tareas pendientes

| ID | Descripción | Estado | Sprint |
|----|-------------|--------|--------|
| T2.1 | Portabilidad `memento_install` (sed macOS/Linux) | pending | 2 |
| T2.2 | Declarar dependencias mínimas en `requirements.txt` | pending | 2 |
| T2.3 | Dockerfile + docker-compose.yml de referencia | pending | 2 |
| T2.4 | Lockfiles y procedimiento de reproducible build | pending | 2 |
| MB-Auth | Definir estrategia auth para escritura en `/api/v1/` (POST/PATCH) | completed | — |
| MB-Docs | Actualizar este documento para reflejar nueva estructura | completed | — |

> `MB-Redis` fue resuelto y **ya no es bloqueador**.

---

## Comandos útiles

```bash
# Estado del proyecto (texto)
python3 tools/project_status.py

# Estado del proyecto (JSON)
python3 tools/project_status.py --format json

# Bootstrap de sesión (texto)
python3 tools/session_bootstrap.py

# Bootstrap de sesión (JSON)
python3 tools/session_bootstrap.py --json

# Sincronizar memoria
python3 tools/sync_memory.py

# Exportar memoria
python3 tools/export_memory.py --format markdown --limit 20 --project mementobloom

# Scan rápido de handoff
python3 tools/quick_scan.py <HANDOFF_PATH>

# Diagnóstico
python3 tools/doctor.py --startup
```

---

## Reglas de seguridad

- No exponer secretos, tokens, contraseñas ni contenido de vault.
- No commitear ni pushear:
  - `.agent_context/START_CONTEXT.md`
  - `.agent_context/secure/USER_CONTEXT.md`
  - `memory/graph/*.json`
  - `.memento/`
  - `archive/`
  - `projects/*/HANDOFF_*.md`
  - datos de sesión
- No ejecutar `FLUSHALL` ni operaciones destructivas sobre Redis salvo instrucción explícita.
- No borrar memoria, Redis, handoffs ni índices salvo instrucción explícita.
- Si una operación modifica memoria, handoffs o índices, validar que el cambio sea intencional.

---

## Proyectos externos vinculados

| Proyecto | Ruta | Handoffs |
|----------|------|----------|
| m360 | `projects/m360` | 14 |
| mementobloom | `projects/mementobloom` | 0 |
| Ventas_Porta | `projects/Ventas_Porta` | 3 |

---

## Métricas actuales

- Entradas de memoria indexadas: 159
- Backups locales: 6 (último: `20260627_145339`)
- Última revisión programada: 2026-06-28T17:19:14-05:00
