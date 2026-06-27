{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T17:40:36.816104",
    "last_event_type": "bootstrap",
    "last_event_summary": "fix(gitignore): allow PROJECT_CONTEXT.md while keeping START/USER_CONTEXT.md ignored, sync PROJECT_CONTEXT.md and SESSION.md",
    "git_branch": "master",
    "git_commit": "01e8f7f",
    "generated_at": "2026-06-27T17:40:36.816104",
    "next_review": "2026-06-28T17:40:41.547732"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "01e8f7f",
      "commit_message": "fix(gitignore): allow PROJECT_CONTEXT.md while keeping START/USER_CONTEXT.md ignored, sync PROJECT_CONTEXT.md and SESSION.md",
      "pending_count": 5,
      "pending": [
        "M .env.example",
        " M SESSION.md",
        " M tools/m360_bridge/client.py",
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
      "indexed_entries": 161,
      "manifest_ts": "2026-06-27T17:40:41"
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