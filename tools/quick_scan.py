#!/usr/bin/env python3
from pathlib import Path
import json
import re

class QuickScan:
    def __init__(self, workspace: str):
        self.ws = Path(workspace) / "projects"
        self.output = Path(workspace) / ".memento" / "memory" / "graph"

    def scan(self, incremental_path: str = None):
        print("🜄 Scanning projects...")
        self.output.mkdir(parents=True, exist_ok=True)

        index = {}
        idx_file = self.output / "memory_index.json"
        if idx_file.exists():
            index = json.loads(idx_file.read_text())

        existing_ids = set(index.keys())
        new_count = 0

        if incremental_path:
            f = Path(incremental_path)
            if f.name.startswith("HANDOFF") and f.suffix == ".md":
                entry = self._parse_handoff(f)
                if entry and entry["id"] not in existing_ids:
                    index[entry["id"]] = entry
                    new_count = 1
            elif f.name.endswith("_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and entry["id"] not in existing_ids:
                    index[entry["id"]] = entry
                    new_count = 1
        else:
            for f in self.ws.rglob("HANDOFF*.md"):
                entry = self._parse_handoff(f)
                if entry and entry["id"] not in existing_ids:
                    index[entry["id"]] = entry
                    existing_ids.add(entry["id"])
                    new_count += 1

            for f in self.ws.rglob("*_CONTEXT.md"):
                entry = self._parse_context(f)
                if entry and entry["id"] not in existing_ids:
                    index[entry["id"]] = entry
                    existing_ids.add(entry["id"])
                    new_count += 1

        (self.output / "memory_index.json").write_text(json.dumps(index, indent=2))
        print(f"✓ Total: {len(index)} entries (nuevos: {new_count})")
    
    def _parse_handoff(self, f):
        content = f.read_text(encoding='utf-8')[:500]
        date_m = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        return {"id": f"h_{f.stem}", "type": "HANDOFF", "project": f.parent.name, 
                "ts": date_m.group(1) if date_m else "unknown", "path": str(f), "summary": content[:100]}
    
    def _parse_context(self, f):
        content = f.read_text(encoding='utf-8')[:500]
        return {"id": f"c_{f.parent.name}", "type": "CONTEXT", "project": f.parent.parent.name,
                "ts": "discover", "path": str(f), "summary": content[:100]}

if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    script_root = Path(__file__).resolve().parent.parent
    
    ws = os.environ.get("MEMENTO_WORKSPACE")
    if ws:
        ws = Path(ws).resolve()
    elif (script_root / ".git").exists():
        if (script_root.parent / "projects").exists() and not (script_root / "projects").exists():
            ws = script_root.parent.resolve()
        else:
            ws = script_root
    else:
        ws = script_root
    
    inc_path = sys.argv[1] if len(sys.argv) > 1 else None
    QuickScan(ws).scan(incremental_path=inc_path)