from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.paths import ROOT, ensure_dir, rel, workspace_root


def _client_index_paths():
    """Client workspace index paths."""
    ws = workspace_root()
    return {
        "client_index": ws / "memory" / "graph" / "memory_index.json",
        "manifest": ws / "memory" / "graph" / "index_manifest.json",
    }


def default_index_path() -> Path:
    paths = _client_index_paths()
    return paths["client_index"].resolve()


def resolve_index_path(index: Optional[str] = None, workspace: Optional[Path] = None) -> Path:
    root = workspace or ROOT
    if index:
        path = Path(index).expanduser()
        if not path.is_absolute():
            path = root / path
        return path.resolve()
    return default_index_path().resolve()


def load_index(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    index_path = path or default_index_path()
    if not index_path.exists():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_index(data: Dict[str, Dict[str, Any]], path: Optional[Path] = None, compact: bool = False) -> Path:
    index_path = path or default_index_path()
    ensure_dir(index_path.parent)
    if compact:
        index_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    else:
        index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return index_path


def parse_ts(value: Any) -> datetime:
    text = str(value or "")
    normalized = text.strip().lower()
    if normalized in {"discover", "unknown", "none", ""}:
        return datetime.min
    # Aceptar ISO básico con o sin timezone: 2026-06-26T12:00:00-05:00 -> 2026-06-26T12:00:00
    if len(text) >= 19 and text[10] == "T":
        text = text[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return datetime.min


def entry_sort_key(entry: Dict[str, Any], project: Optional[str] = None) -> tuple[Any, ...]:
    ts_raw = entry.get("ts") or entry.get("timestamp") or ""
    ts = parse_ts(ts_raw)
    project_value = str(entry.get("project", ""))
    type_value = str(entry.get("type", ""))
    type_priority = {"HANDOFF": 0, "SOURCE": 1, "NOTE": 2, "CONTEXT": 3, "COMPONENT": 4}.get(type_value, 50)
    project_boost = 1 if project and project_value == project else 0
    type_boost = 1 if type_value == "HANDOFF" else 0
    return (ts, project_boost, type_boost, -type_priority, str(entry.get("id", "")))


def top_entries(index: Dict[str, Dict[str, Any]], limit: int, project: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = [entry for entry in index.values() if isinstance(entry, dict)]
    if project:
        entries = [entry for entry in entries if str(entry.get("project")) == project]
    entries.sort(key=lambda entry: entry_sort_key(entry, project=project), reverse=True)
    return entries[:limit]


def latest_handoffs(index: Dict[str, Dict[str, Any]], limit: int = 5, project: Optional[str] = None) -> List[Dict[str, Any]]:
    return [entry for entry in top_entries(index, limit * 2, project=project) if str(entry.get("type")) == "HANDOFF"][:limit]


def count_by(entries: Iterable[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get(field, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_manifest(index: Dict[str, Dict[str, Any]], path: Optional[Path] = None) -> Dict[str, Any]:
    entries = [entry for entry in index.values() if isinstance(entry, dict)]
    manifest = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(index),
        "by_type": count_by(entries, "type"),
        "by_project": count_by(entries, "project"),
        "latest_handoffs": [
            {
                "id": entry.get("id"),
                "type": entry.get("type"),
                "project": entry.get("project"),
                "ts": entry.get("ts"),
                "path": entry.get("path"),
                "summary": str(entry.get("summary", ""))[:220],
            }
            for entry in latest_handoffs(index, 5)
        ],
    }
    paths = _client_index_paths()
    manifest_path = path or paths["manifest"]
    ensure_dir(manifest_path.parent)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def portable_path(value: Any, root: Path = ROOT) -> str:
    text = str(value or "")
    if not text:
        return ""
    path = Path(text)
    try:
        return rel(path.resolve(), root)
    except Exception:
        return text
