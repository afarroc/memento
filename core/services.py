from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from core.paths import ROOT, ensure_dir, workspace_root

REDIS_HOST = os.environ.get("REDIS_HOST", os.environ.get("MEMENTO_REDIS_HOST", "192.168.18.59"))
REDIS_PORT = int(os.environ.get("REDIS_PORT", os.environ.get("MEMENTO_REDIS_PORT", "6379")))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
HEALTH_CACHE_PATH = workspace_root() / ".memento_runtime" / "health_cache.json"


def redis_ping(host: str = REDIS_HOST, port: int = REDIS_PORT, timeout: float = 0.6) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(128).decode(errors="replace")
        return {"ok": "PONG" in data, "detail": data.strip(), "host": host, "port": port}
    except OSError as exc:
        return {"ok": False, "detail": str(exc), "host": host, "port": port}


def http_json(url: str, timeout: float = 0.6) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw[:500]}
            return {"ok": 200 <= response.status < 500, "status": response.status, "data": parsed}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def http_text(url: str, timeout: float = 0.6) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        return {"ok": 200 <= response.status < 500, "status": response.status, "data": raw[:500]}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def _load_cache() -> Dict[str, Any]:
    if not HEALTH_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(HEALTH_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(data: Dict[str, Any]) -> None:
    ensure_dir(HEALTH_CACHE_PATH.parent)
    HEALTH_CACHE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _cache_valid(cache: Dict[str, Any], ttl_seconds: int) -> bool:
    checked_at = cache.get("checked_at")
    if not checked_at:
        return False
    try:
        stamp = datetime.fromisoformat(checked_at)
    except ValueError:
        return False
    return datetime.now() - stamp < timedelta(seconds=ttl_seconds)


def service_status(fresh: bool = False, cache_ttl: int = 30) -> Dict[str, Any]:
    cache = _load_cache()
    if not fresh and _cache_valid(cache, cache_ttl):
        return {**cache, "from_cache": True}

    sala = http_json(f"http://127.0.0.1:{SALA_PORT}/stats")
    panel = http_json(f"http://127.0.0.1:{PANEL_PORT}/stats")
    if not panel.get("ok"):
        panel = http_text(f"http://127.0.0.1:{PANEL_PORT}/")

    result = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "from_cache": False,
        "redis": redis_ping(),
        "sala": {
            "ok": bool(sala.get("ok")),
            "status": sala.get("status"),
            "data": sala.get("data"),
            "error": sala.get("error"),
            "url": f"http://127.0.0.1:{SALA_PORT}/stats",
        },
        "panel": {
            "ok": bool(panel.get("ok")),
            "status": panel.get("status"),
            "data": panel.get("data"),
            "error": panel.get("error"),
            "url": f"http://127.0.0.1:{PANEL_PORT}/",
        },
    }
    _save_cache(result)
    return result


def service_summary(services: Dict[str, Any]) -> str:
    redis = services.get("redis", {})
    sala = services.get("sala", {})
    panel = services.get("panel", {})
    cache_note = " cache" if services.get("from_cache") else ""
    return (
        f"Redis {'OK' if redis.get('ok') else 'NO'} at {redis.get('host', '?')}:{redis.get('port', '?')} | "
        f"Sala {'OK' if sala.get('ok') else 'NO'} at http://127.0.0.1:{SALA_PORT} | "
        f"Panel {'OK' if panel.get('ok') else 'NO'} at http://127.0.0.1:{PANEL_PORT}{cache_note}"
    )
