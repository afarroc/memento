{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T21:15:21.963663",
    "last_event_type": "bootstrap",
    "last_event_summary": "chore(deps): declare min requirements, add requirements-dev, update pyproject extras",
    "git_branch": "master",
    "git_commit": "04fcd06",
    "generated_at": "2026-06-27T21:15:21.963663",
    "next_review": "2026-06-28T21:15:24.658861"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "04fcd06",
      "commit_message": "chore(deps): declare min requirements, add requirements-dev, update pyproject extras",
      "pending_count": 8,
      "pending": [
        "M SESSION.md",
        "?? .dockerignore",
        "?? Dockerfile",
        "?? compose.yml.docker-reference.md",
        "?? docker-compose.yml",
        "?? gtd_memento/",
        "?? memento_install.bak.20260627",
        "?? projects/m360/context/"
      ]
    },
    "services": {
      "sala": "NO",
      "panel": "NO",
      "redis": "OK"
    },
    "memory": {
      "indexed_entries": 162,
      "manifest_ts": "2026-06-27T21:15:24"
    }
  },
  "pending_tasks": [
    {
      "id": "T2.1",
      "description": "Portabilidad memento_install (sed macOS/Linux)",
      "status": "completed",
      "sprint": 2
    },
    {
      "id": "T2.2",
      "description": "Declarar dependencias mínimas en requirements.txt",
      "status": "completed",
      "sprint": 2
    },
    {
      "id": "T2.3",
      "description": "Dockerfile + docker-compose.yml de referencia",
      "status": "completed",
      "sprint": 2
    },
    {
      "id": "T2.4",
      "description": "Lockfiles y procedimiento de reproducible build",
      "status": "completed",
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
      "status": "completed"
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