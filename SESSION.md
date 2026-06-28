{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T21:57:30.008310",
    "last_event_type": "bootstrap",
    "last_event_summary": "feat(sync): sync Sprint 3 tasks to M360 project 78, fix sala BrokenPipeError",
    "git_branch": "master",
    "git_commit": "7574c6a",
    "generated_at": "2026-06-27T21:57:30.008310",
    "next_review": "2026-06-28T21:57:33.286574"
  },
  "state": {
    "git": {
      "branch": "master",
      "commit_hash": "7574c6a",
      "commit_message": "feat(sync): sync Sprint 3 tasks to M360 project 78, fix sala BrokenPipeError",
      "pending_count": 2,
      "pending": [
        "M .agent_context/START_CONTEXT.md",
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
      "manifest_ts": "2026-06-27T21:57:33"
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
  "entrypoint": "python3 tools/session_bootstrap.py",
  "cleanup_log": [
    {
      "date": "2026-06-27",
      "action": "m360_cleanup",
      "deleted_projects": [
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        79
      ],
      "reason": "test projects from today, keep real project 78"
    }
  ],
  "last_m360_sync": "2026-06-27T22:25:00-05:00",
  "m360_project_id": 78,
  "m360_project_title": "MementoBloom - S-27-06"
}