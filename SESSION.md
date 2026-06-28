{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-28T02:07:32",
    "last_event_type": "bootstrap",
    "last_event_summary": "session: finalize recontextualization, preserve canonical state",
    "git_branch": "unknown",
    "git_commit": "8ee63ab",
    "generated_at": "2026-06-28T02:07:32"
  },
  "state": {
    "git": {
      "branch": "unknown",
      "commit_hash": "8ee63ab",
      "commit_message": "session: finalize recontextualization, preserve canonical state",
      "pending_count": 3
    },
    "services": {
      "sala": {
        "ok": true,
        "status": 200,
        "data": {
          "messages": 5
        },
        "error": null,
        "url": "http://127.0.0.1:8767/stats"
      },
      "panel": {
        "ok": true,
        "status": 200,
        "data": "<html>",
        "error": null,
        "url": "http://127.0.0.1:8766/"
      },
      "redis": {
        "ok": true,
        "detail": "+PONG",
        "host": "192.168.18.59",
        "port": 6379
      }
    },
    "memory": {
      "indexed_entries": 167,
      "manifest_ts": ""
    }
  },
  "forbidden_paths": [
    ".agent_context/secure/*",
    "memory/**/*.json",
    "*.env",
    ".memento/**",
    "archive/**"
  ],
  "entrypoint": "python3 tools/session_bootstrap.py",
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
  "completed_tasks": [
    {
      "id": "T0.1",
      "description": "Corregir panel_server.py: eliminar import roto check_tcp, agregar dataclass, parsing puerto por sys.argv",
      "status": "completed",
      "sprint": 0
    },
    {
      "id": "T0.2",
      "description": "Corregir core/paths.py: detectar workspace cliente automáticamente",
      "status": "completed",
      "sprint": 0
    },
    {
      "id": "T0.3",
      "description": "Reemplazar IPs hardcodeadas por variables de entorno con defaults neutros",
      "status": "completed",
      "sprint": 0
    },
    {
      "id": "T0.4",
      "description": "Hacer rutas en memory_index.json relativas al workspace usando core/paths.rel()",
      "status": "completed",
      "sprint": 0
    },
    {
      "id": "T0.5",
      "description": "Ejecutar selftest y doctor; capturar y resolver fallos",
      "status": "completed",
      "sprint": 0
    },
    {
      "id": "T1.1",
      "description": "Implementar prefijo de proyecto en REDIS_KEY: memento_panel_items:<proyecto>",
      "status": "completed",
      "sprint": 1
    },
    {
      "id": "T1.2",
      "description": "Agregar detección de puertos libres para Sala y Panel con fallback",
      "status": "completed",
      "sprint": 1
    },
    {
      "id": "T1.3",
      "description": "Modificar memento_install para generar .gitignore sin sobrescribir existentes",
      "status": "completed",
      "sprint": 1
    },
    {
      "id": "T1.4",
      "description": "Crear script memento-configure (CLI) para definir host Redis, puertos y proyecto",
      "status": "completed",
      "sprint": 1
    },
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
      "status": "completed",
      "sprint": null
    },
    {
      "id": "MB-Redis",
      "description": "Resolver disponibilidad de Redis para panel/sala",
      "status": "completed",
      "sprint": null
    },
    {
      "id": "MB-Docs",
      "description": "Actualizar PROJECT_CONTEXT.md con nueva estructura",
      "status": "completed",
      "sprint": null
    }
  ],
  "blockers": [
    {
      "id": "B-M360",
      "description": "M360 no disponible actualmente (connection refused). Sincronización diferida de Sprint 3 en proyecto 78.",
      "status": "active",
      "impact": "No se pueden crear tareas Sprint 3 en M360 ni validar flujo completo."
    }
  ]
}
