from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.paths import ROOT


def run_command(args: List[str], timeout: int = 10, cwd: Optional[Path] = None) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd or ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "returncode": None}


def git_status(root: Optional[Path] = None) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(root or ROOT), "status", "--short"], timeout=5)
    lines = [line for line in result.get("stdout", "").splitlines() if line.strip()]
    return {
        "ok": result["ok"],
        "raw": result.get("stdout", ""),
        "changes": lines,
        "change_count": len(lines),
        "error": result.get("stderr", ""),
    }


def git_diff_stat(root: Optional[Path] = None) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(root or ROOT), "diff", "--stat"], timeout=5)
    return {
        "ok": result["ok"],
        "text": result.get("stdout", ""),
        "error": result.get("stderr", ""),
    }


def latest_commit(root: Optional[Path] = None) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(root or ROOT), "log", "-1", "--oneline"], timeout=5)
    parts = result.get("stdout", "").split(" ", 1) if result.get("stdout") else []
    return {
        "ok": result["ok"],
        "hash": parts[0] if parts else "",
        "message": parts[1] if len(parts) > 1 else "",
        "raw": result.get("stdout", ""),
        "error": result.get("stderr", ""),
    }


def check_ignore(path: str, root: Optional[Path] = None) -> Dict[str, Any]:
    result = run_command(["git", "-C", str(root or ROOT), "check-ignore", "-v", path], timeout=5)
    return {
        "path": path,
        "ignored": result["ok"],
        "rule": result.get("stdout", "").strip(),
        "error": result.get("stderr", "").strip() if not result["ok"] else "",
    }
