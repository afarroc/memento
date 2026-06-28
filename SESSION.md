{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T21:56:46.580078",
    "last_event_type": "bootstrap",
    "last_event_summary": "fix(sala): handle BrokenPipeError gracefully on client disconnect",
    "git_branch": "master",
    "git_commit": "517cd1a",
    "generated_at": "2026-06-27T21:56:46.580078",
    "next_review": "2026-06-28T21:56:50.121662"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "517cd1a",
      "commit_message": "fix(sala): handle BrokenPipeError gracefully on client disconnect",
      "pending_count": 3,
      "pending": [
        "M .agent_context/START_CONTEXT.md",
        " M SESSION.md",
        "?? .kilo.backup.20260627/"
      ]
    },
    "services": {
      "sala": "OK",
      "panel": "OK",
      "redis": "OK"
    },
    "memory": {
      "indexed_entries": 166,
      "manifest_ts": "2026-06-27T21:56:50"
    }
  },
  "pending_tasks": [
    {
      "id": "T3.1",
      "description": "Mejorar vault_manager.py: cifrado Fernet o marcar como encoding, no seguridad",
      "status": "pending",
      "sprint": 3
    },
    {
      "id": "T3.2",
      "description": "Asegurar exclusión Git de archivos sensibles en instalaciones cliente",
      "status": "pending",
      "sprint": 3
    },
    {
      "id": "T3.3",
      "description": "Validación de .env al arranque: doctor.py alerta variables críticas",
      "status": "pending",
      "sprint": 3
    },
    {
      "id": "T3.4",
      "description": "Sanitizar rutas absolutas en logs y exports",
      "status": "pending",
      "sprint": 3
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