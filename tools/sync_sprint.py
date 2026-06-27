"""CLI: sincronizar sprints de gtd_memento -> M360."""
from __future__ import annotations

import sys
from pathlib import Path

from m360_bridge.sync import M360Sync, infer_sprint_spec


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    sprint_id = "SPRINT_0"
    project_id = None
    for i, arg in enumerate(argv):
        if arg.startswith("--sprint="):
            sprint_id = arg.split("=", 1)[1]
        elif arg == "--sprint" and i + 1 < len(argv):
            sprint_id = argv[i + 1]
        elif arg.startswith("--project-id="):
            project_id = int(arg.split("=", 1)[1])
        elif arg == "--project-id" and i + 1 < len(argv):
            project_id = int(argv[i + 1])

    if not sprint_id:
        print("Uso: python3 tools/sync_sprint.py --sprint SPRINT_X [--project-id ID]")
        return 1

    sync = M360Sync()
    print(f"Sincronizando {sprint_id} -> M360 ...")
    result = sync.sync_sprint(sprint_id, project_id=project_id)
    print(f"Resultado: ok={result.ok} errors={result.errors}")
    for detail in result.details:
        print(f"  - {detail}")
    return 0 if result.errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
