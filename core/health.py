from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from core.git import check_ignore, git_diff_stat, git_status, latest_commit
from core.index import build_manifest, count_by, default_index_path, load_index, resolve_index_path, top_entries
from core.paths import ROOT, rel
from core.services import service_status

PROJECT_META = ROOT / ".agent_context" / "PROJECT_META.md"
USER_CONTEXT = ROOT / ".agent_context" / "secure" / "USER_CONTEXT.md"
START_CONTEXT = ROOT / ".agent_context" / "START_CONTEXT.md"
AGENT_INIT = ROOT / ".agent_context" / "agent" / "init.md"
AGENT_SEED = ROOT / ".agent_context" / "agent" / "agent-main.md"


def startup_health(index_path: Optional[Path] = None, check_services: bool = True, fresh_health: bool = False) -> Dict[str, Any]:
    index_file = resolve_index_path(str(index_path) if index_path else None)
    index = load_index(index_file)
    services = service_status(fresh=fresh_health) if check_services else {"checked": False, "reason": "services disabled"}

    project_meta_ignored = check_ignore(rel(PROJECT_META)) if PROJECT_META.exists() else {"ignored": False, "rule": ""}
    user_context_ignored = check_ignore(rel(USER_CONTEXT)) if USER_CONTEXT.exists() else {"ignored": True, "rule": "optional"}

    health = {
        "project_meta_exists": PROJECT_META.exists(),
        "project_meta_tracked": not bool(project_meta_ignored.get("ignored")),
        "user_context_optional": True,
        "start_context_optional": True,
        "agent_init_exists": AGENT_INIT.exists(),
        "agent_seed_exists": AGENT_SEED.exists(),
        "memory_index_exists": index_file.exists(),
        "memory_index_empty": not bool(index),
        "services_checked": bool(check_services),
    }
    health["ok"] = all(
        [
            health["project_meta_exists"],
            health["project_meta_tracked"],
            health["agent_init_exists"],
            health["agent_seed_exists"],
            health["memory_index_exists"],
        ]
    )
    return {
        "ok": health["ok"],
        "health": health,
        "git": {
            "latest": latest_commit(),
            "status": git_status(),
            "diff_stat": git_diff_stat(),
        },
        "memory": {
            "index_path": rel(index_file),
            "entries": len(index),
            "by_type": count_by(index.values(), "type"),
            "by_project": count_by(index.values(), "project"),
            "latest_handoffs": top_entries(index, 5),
        },
        "services": services,
    }


def ensure_memory_manifest(index_path: Optional[Path] = None) -> Dict[str, Any]:
    index_file = resolve_index_path(str(index_path) if index_path else None)
    index = load_index(index_file)
    return build_manifest(index, index_file.parent / "index_manifest.json")
