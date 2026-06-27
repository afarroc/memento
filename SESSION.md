{
  "session": {
    "project": "mementobloom",
    "role": "asistente-gtd",
    "workspace": "/Volumes/Macintosh HD - Datos/mementobloom",
    "last_event_time": "2026-06-27T14:47:12",
    "last_event_type": "bootstrap",
    "last_event_summary": "feat(contract): implementar Fase 1 SESSION_CONTRACT",
    "git_branch": "unknown",
    "git_commit": "0f61d3e",
    "generated_at": "2026-06-27T14:47:12"
  },
  "state": {
    "git": {
      "branch": "unknown",
      "commit_hash": "0f61d3e",
      "commit_message": "feat(contract): implementar Fase 1 SESSION_CONTRACT",
      "pending_count": 2
    },
    "services": {
      "sala": {
        "ok": true,
        "status": 200,
        "data": {
          "messages": 61
        },
        "error": null,
        "url": "http://127.0.0.1:8767/stats"
      },
      "panel": {
        "ok": true,
        "status": 200,
        "data": "<!DOCTYPE html>\n<html lang=\"es\">\n<head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n<title>Dashboard</title>\n<style>\n*{margin:0;padding:0;box-sizing:border-box}\nbody{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#08090a;color:#d4d4d4;min-height:100vh}\n#content{padding:16px}\n.card{background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px;margin:8px 0}\n.card h3{font-size:13px;color:#6b7280;margin-b",
        "error": null,
        "url": "http://127.0.0.1:8766/"
      },
      "redis": {
        "ok": false,
        "detail": "[Errno 61] Connection refused",
        "host": "localhost",
        "port": 6379
      }
    },
    "memory": {
      "indexed_entries": 109,
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
  "entrypoint": "python3 tools/session_bootstrap.py"
}