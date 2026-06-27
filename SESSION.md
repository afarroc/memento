{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T14:55:47.661607",
    "last_event_type": "bootstrap",
    "last_event_summary": "feat(contract): Fase 2 SESSION_CONTRACT - vistas derivadas y limpieza",
    "git_branch": "master",
    "git_commit": "a3573d1",
    "generated_at": "2026-06-27T14:55:47.661607",
    "next_review": "2026-06-28T14:55:50.939332"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "a3573d1",
      "commit_message": "feat(contract): Fase 2 SESSION_CONTRACT - vistas derivadas y limpieza",
      "pending_count": 4,
      "pending": [
        "M .agent_context/START_CONTEXT.md",
        " M SESSION.md",
        " M tools/session_render.py",
        "?? gtd_memento/"
      ]
    },
    "services": {
      "sala": "OK",
      "panel": "NO",
      "redis": "NO"
    },
    "memory": {
      "indexed_entries": 110,
      "manifest_ts": "2026-06-27T14:55:50"
    }
  },
  "pending_tasks": [
    {
      "id": "T2.1",
      "description": "Portabilidad memento_install (sed macOS/Linux)",
      "status": "pending",
      "sprint": 2
    },
    {
      "id": "T2.2",
      "description": "Declarar dependencias mínimas en requirements.txt",
      "status": "pending",
      "sprint": 2
    },
    {
      "id": "T2.3",
      "description": "Dockerfile + docker-compose.yml de referencia",
      "status": "pending",
      "sprint": 2
    },
    {
      "id": "T2.4",
      "description": "Lockfiles y procedimiento de reproducible build",
      "status": "pending",
      "sprint": 2
    },
    {
      "id": "MB-Auth",
      "description": "Definir estrategia auth para escritura en /api/v1/ (POST/PATCH)",
      "status": "pending"
    },
    {
      "id": "MB-Redis",
      "description": "Resolver disponibilidad de Redis para panel/sala",
      "status": "blocked"
    },
    {
      "id": "MB-Docs",
      "description": "Actualizar docs/PROJECT_CONTEXT.md para reflejar nueva estructura",
      "status": "pending"
    }
  ],
  "blockers": [
    "Redis no disponible localmente (localhost:6379)",
    "Múltiples scripts de arranque (requiere consolidación)"
  ],
  "forbidden_paths": [
    ".agent_context/secure/*",
    "memory/**/*.json",
    "*.env",
    ".memento/**",
    "archive/**"
  ],
  "entrypoint": "python3 tools/session_bootstrap.py"
}