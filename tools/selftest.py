#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.git import check_ignore
from core.index import build_manifest, load_index, resolve_index_path, save_index
from core.paths import ROOT, rel
from tools.quick_scan import QuickScan


def run_python(args: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def test_quick_scan_empty_workspace() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        scanner = QuickScan(ws, index_path=ws / "memory" / "graph" / "memory_index.json")
        result = scanner.scan(build_manifest_output=True)
        index = load_index(Path(result["index_path"]))
        manifest = (ws / "memory" / "graph" / "index_manifest.json").exists()
        return {
            "name": "quick_scan_empty_workspace",
            "ok": result["ok"] and result["total"] == 0 and isinstance(index, dict) and manifest,
            "detail": result,
        }


def test_bootstrap_no_services() -> Dict[str, Any]:
    result = run_python(["tools/bootstrap_context.py", "--print", "--no-services", "--limit", "1"])
    return {
        "name": "bootstrap_no_services",
        "ok": result["ok"] and "# MementoBloom Bootstrap Context" in result["stdout"],
        "detail": result["stderr"] if not result["ok"] else "",
    }


def test_doctor_startup_no_services() -> Dict[str, Any]:
    result = run_python(["tools/doctor.py", "--startup", "--no-services"])
    return {
        "name": "doctor_startup_no_services",
        "ok": result["ok"] and "MementoBloom Doctor" in result["stdout"],
        "detail": result["stderr"] if not result["ok"] else "",
    }


def test_index_manifest() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        index_path = Path(tmp) / "index.json"
        save_index({"h_test": {"id": "h_test", "type": "HANDOFF", "project": "test", "ts": "2026-06-21", "path": "test.md", "summary": "test"}}, index_path)
        manifest = build_manifest(load_index(index_path), index_path.parent / "index_manifest.json")
        return {
            "name": "index_manifest",
            "ok": manifest["total"] == 1 and manifest["latest_handoffs"][0]["id"] == "h_test",
            "detail": manifest,
        }


def test_gitignore_rules() -> Dict[str, Any]:
    checks = [
        check_ignore(".agent_context/START_CONTEXT.md"),
        check_ignore(".agent_context/secure/USER_CONTEXT.md"),
        check_ignore("memory/graph/memory_index.json"),
        check_ignore("projects/mementobloom/HANDOFF_test.md"),
    ]
    ok = all(item.get("ignored") for item in checks)
    return {
        "name": "gitignore_rules",
        "ok": ok,
        "detail": checks,
    }


def test_no_hardcoded_workspace_in_core_tools() -> Dict[str, Any]:
    forbidden = "/Volumes/Macintosh HD - Datos"
    files = list((ROOT / "core").glob("*.py")) + [p for p in (ROOT / "tools").glob("*.py") if p.name != "selftest.py"]
    offenders = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if forbidden in text:
            offenders.append(rel(path))
    return {
        "name": "no_hardcoded_workspace_in_core_tools",
        "ok": not offenders,
        "detail": offenders,
    }


def test_context_retriever_search() -> Dict[str, Any]:
    from tools.context_retriever import ContextRetriever
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        index_path = ws / "memory" / "graph" / "memory_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        test_index = {
            "h_HANDOFF_2026-06-22_test": {
                "id": "h_HANDOFF_2026-06-22_test",
                "type": "HANDOFF",
                "project": "mementobloom",
                "ts": "2026-06-22",
                "path": "projects/mementobloom/HANDOFF_2026-06-22_test.md",
                "summary": "HANDOFF - Optimización de arranque completada exitosamente",
                "keywords": "mementobloom, startup, optimization, arranque"
            },
            "h_HANDOFF_2026-06-22_other": {
                "id": "h_HANDOFF_2026-06-22_other",
                "type": "HANDOFF",
                "project": "otro",
                "ts": "2026-06-21",
                "path": "projects/otro/HANDOFF_2026-06-22_other.md",
                "summary": "Otro proyecto sin relación con la búsqueda",
                "keywords": "otro, proyecto, aleatorio"
            }
        }
        save_index(test_index, index_path)

        retriever = ContextRetriever(graph_index_path=str(index_path), workspace=ws)
        
        # Test sin query (fallback a top_entries)
        context_no_query = retriever.get_context("", limit=5)
        ok_no_query = "# CONTEXT_COMPACT" in context_no_query and "h_HANDOFF_2026-06-22_test" in context_no_query

        # Test con query "optimization"
        context_query = retriever.get_context("optimization", limit=5)
        ok_query = "# CONTEXT_COMPACT" in context_query and "h_HANDOFF_2026-06-22_test" in context_query and "h_HANDOFF_2026-06-22_other" not in context_query

        # Test con query vacía
        context_empty = retriever.get_context("   ", limit=5)
        ok_empty = "# CONTEXT_COMPACT" in context_empty

        return {
            "name": "context_retriever_search",
            "ok": ok_no_query and ok_query and ok_empty,
            "detail": {"no_query": ok_no_query, "with_query": ok_query, "empty_query": ok_empty},
        }


def test_memory_index_structure() -> Dict[str, Any]:
    """Validar que memory_index.json tenga estructura homogénea, sin IDs duplicados ni tipos minúsculos."""
    index_path = resolve_index_path()
    if not index_path.exists():
        return {"name": "memory_index_structure", "ok": True, "detail": "index missing, skipped"}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"name": "memory_index_structure", "ok": False, "detail": f"invalid json: {exc}"}

    problems: List[str] = []

    if not isinstance(data, dict):
        problems.append("index root is not a dict")
    else:
        if "index" in data and isinstance(data.get("index"), list):
            problems.append("found legacy array key 'index'")
        non_dict = [key for key, value in data.items() if not isinstance(value, dict)]
        if non_dict:
            problems.append(f"non-dict entries: {non_dict[:5]}")

        ids = [value.get("id") for value in data.values() if isinstance(value, dict) and value.get("id")]
        unique_ids = set(ids)
        if len(ids) != len(unique_ids):
            from collections import Counter
            dupes = [item for item, count in Counter(ids).items() if count > 1]
            problems.append(f"duplicate ids: {dupes[:5]}")

        bad_types = []
        for value in data.values():
            if isinstance(value, dict):
                type_value = value.get("type")
                if isinstance(type_value, str) and type_value != type_value.upper():
                    bad_types.append(type_value)
        if bad_types:
            problems.append(f"lowercase types: {sorted(set(bad_types))[:5]}")

    return {
        "name": "memory_index_structure",
        "ok": not problems,
        "detail": problems,
    }


def main() -> int:
    tests = [
        test_quick_scan_empty_workspace,
        test_bootstrap_no_services,
        test_doctor_startup_no_services,
        test_index_manifest,
        test_gitignore_rules,
        test_no_hardcoded_workspace_in_core_tools,
        test_context_retriever_search,
        test_memory_index_structure,
    ]
    results = [test() for test in tests]
    failures = [result for result in results if not result.get("ok")]
    for result in results:
        state = "OK" if result.get("ok") else "FAIL"
        print(f"{state} {result['name']}")
        if not result.get("ok"):
            print(json.dumps(result.get("detail"), indent=2, ensure_ascii=False))
    print(f"Total: {len(results)} | Failures: {len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
