from pathlib import Path
import json
import hashlib
from typing import Dict, List, Optional

class SeedBuilder:
    def __init__(self, workspace: str):
        self.ws = Path(workspace)
        self.seed = {}
    
    def build(self) -> Dict:
        seed_file = self.ws / "memory" / "seeds" / "system_seed.md"
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        
        raw = seed_file.read_text(encoding='utf-8') if seed_file.exists() else ""
        projects = self._discover_projects()
        
        return {
            "raw": raw,
            "projects": projects,
            "ready": False,
            "stats": {"handoffs": 0, "contexts": 0, "entries": 0}
        }
    
    def _discover_projects(self) -> List[Dict]:
        projects = []
        for p in self.ws.glob("*/HANDOFF*.md"):
            projects.append({"name": p.parent.name, "path": str(p), "type": "handoff"})
        for p in self.ws.glob("*/*_CONTEXT.md"):
            projects.append({"name": p.parent.parent.name, "path": str(p), "type": "context"})
        return list({p["name"]: p for p in projects}.values())

class SymbolCompressor:
    @staticmethod
    def hash_content(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    @staticmethod
    def compact_entry(entry: Dict) -> str:
        return f"{entry['id']}:{entry['type']}:{entry['ts'][:10]}:{SymbolCompressor.hash_content(entry['summary'])}"