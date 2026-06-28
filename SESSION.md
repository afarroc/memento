{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T20:22:08.720074",
    "last_event_type": "bootstrap",
    "last_event_summary": "chore(session): refresh project state and mark panel OK",
    "git_branch": "master",
    "git_commit": "c6dbec6",
    "generated_at": "2026-06-27T20:22:08.720074",
    "next_review": "2026-06-28T20:22:13.211071"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "c6dbec6",
      "commit_message": "chore(session): refresh project state and mark panel OK",
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
      "manifest_ts": "2026-06-27T20:22:13"
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