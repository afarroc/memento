{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T20:14:10.603409",
    "last_event_type": "bootstrap",
    "last_event_summary": "feat(agent): restore automatic .kilo/agents/agent-main.md sync in session_start.py",
    "git_branch": "master",
    "git_commit": "202e123",
    "generated_at": "2026-06-27T20:14:10.603409",
    "next_review": "2026-06-28T20:14:14.923843"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "202e123",
      "commit_message": "feat(agent): restore automatic .kilo/agents/agent-main.md sync in session_start.py",
      "pending_count": 2,
      "pending": [
        "?? gtd_memento/",
        "?? projects/m360/context/"
      ]
    },
    "services": {
      "sala": "OK",
      "panel": "OK",
      "redis": "OK"
    },
    "memory": {
      "indexed_entries": 162,
      "manifest_ts": "2026-06-27T20:14:14"
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
      "status": "completed"
    },
    {
      "id": "MB-Redis",
      "description": "Resolver disponibilidad de Redis para panel/sala",
      "status": "completed"
    },
    {
      "id": "MB-Docs",
      "description": "Actualizar docs/PROJECT_CONTEXT.md para reflejar nueva estructura",
      "status": "pending"
    }
  ],
  "blockers": [],
  "forbidden_paths": [
    ".agent_context/secure/*",
    "memory/**/*.json",
    "*.env",
    ".memento/**",
    "archive/**"
  ],
  "entrypoint": "python3 tools/session_bootstrap.py"
}