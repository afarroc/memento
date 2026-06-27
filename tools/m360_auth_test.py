#!/usr/bin/env python3
"""Prueba de autenticación para escritura en /api/v1/ (M360).

Uso:
    python3 tools/m360_auth_test.py
    M360_API_KEY=test python3 tools/m360_auth_test.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import workspace_root
from tools.m360_bridge.client import M360Client


def main() -> int:
    ws = workspace_root()
    env_path = ws / ".env"
    env: Dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")

    base_url = env.get("M360_BASE_URL", "http://127.0.0.1:8000")
    username = env.get("M360_USERNAME", "su")
    password = env.get("M360_PASSWORD", "")
    api_key = os.environ.get("M360_API_KEY", env.get("M360_API_KEY", ""))

    client = M360Client(base_url=base_url, username=username, password=password)

    print(f"Base URL : {base_url}")
    print(f"Username : {username}")
    print(f"API Key  : {'(set)' if api_key else '(missing)'}")
    print()

    health = client.api_v1_health()
    print(f"Health   : {health.get('status', 'error')}")

    projects = client.api_v1_list_projects(limit=1)
    data = projects.get("data") or []
    project_id = data[0]["id"] if data else None
    print(f"Project  : {project_id}")

    payload = {"title": "mementobloom auth test", "description": "auto", "project_id": project_id}
    result = client.api_v1_create_task(title=payload["title"], project_id=project_id or 0, description=payload["description"])

    status = result.get("status")
    ok = result.get("ok", False)
    http_error = result.get("http_error")
    print(f"Create   : status={status} ok={ok} http_error={http_error}")

    if http_error == 403:
        print("AUTH EXPECTED: write rejected without/invalid API key")
        return 0
    if not ok and http_error in (401, 403):
        print("AUTH EXPECTED: write rejected by M360 auth")
        return 0
    if ok or result.get("id"):
        print("AUTH OK: write accepted")
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
