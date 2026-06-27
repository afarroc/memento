{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T17:01:23.409877",
    "last_event_type": "bootstrap",
    "last_event_summary": "fix(panel): use SALA_HOST env in sala endpoint and stats URL",
    "git_branch": "master",
    "git_commit": "0cf47fc",
    "generated_at": "2026-06-27T17:01:23.409877",
    "next_review": "2026-06-28T17:01:25.351000"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "0cf47fc",
      "commit_message": "fix(panel): use SALA_HOST env in sala endpoint and stats URL",
      "pending_count": 4,
      "pending": [
        "M SESSION.md",
        " M core/services.py",
        " M tools/project_status.py",
        "?? gtd_memento/"
      ]
    },
    "services": {
      "sala": "OK",
      "panel": "OK",
      "redis": "OK"
    },
    "memory": {
      "indexed_entries": 111,
      "manifest_ts": "2026-06-27T17:01:25"
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