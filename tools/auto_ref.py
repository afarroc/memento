import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from core.paths import rel

class AutoRefEngine:
    def __init__(self, workspace: str):
        self.ws = Path(workspace)
        self.graph_index = self.ws / "memory" / "graph"
    
    def find_next_memory(self, processed_count: int, max_batch: int = 10) -> List[Dict]:
        """Busca siguiente lote de entradas sin procesar."""
        entries = []
        seen_ids = set(self._load_index().keys())
        
        for f in self.ws.rglob("HANDOFF*.md"):
            entry = self._parse_handoff(f)
            if entry and entry["id"] not in seen_ids:
                entries.append(entry)
                seen_ids.add(entry["id"])
                if len(entries) >= max_batch:
                    return entries
        
        for f in self.ws.rglob("*_CONTEXT.md"):
            entry = self._parse_context(f)
            if entry and entry["id"] not in seen_ids:
                entries.append(entry)
                seen_ids.add(entry["id"])
                if len(entries) >= max_batch:
                    return entries
        
        return entries
        """Busca siguiente lote de entradas sin procesar."""
        entries = []
        
        # Handoffs
        for f in self.ws.rglob("HANDOFF*.md"):
            entry = self._parse_handoff(f)
            if entry and not self._exists(entry["id"]):
                entries.append(entry)
        
        # Contexts
        for f in self.ws.rglob("*_CONTEXT.md"):
            entry = self._parse_context(f)
            if entry and not self._exists(entry["id"]):
                entries.append(entry)
        
        return entries[:max_batch]
    
    def _parse_handoff(self, filepath: Path) -> Optional[Dict]:
        content = filepath.read_text(encoding='utf-8')
        date_m = re.search(r'HANDOFF - (\d{4}-\d{2}-\d{2})', filepath.name)
        proj = filepath.parent.name
        entry_id = f"handoff_{filepath.stem}"
        
        return {
            "id": entry_id,
            "type": "HANDOFF",
            "path": rel(filepath, self.ws),
            "project": proj,
            "ts": date_m.group(1) if date_m else "unknown",
            "summary": content.split('\n')[3] if len(content) > 3 else ""
        }
    
    def _parse_context(self, filepath: Path) -> Optional[Dict]:
        content = filepath.read_text(encoding='utf-8')
        proj = filepath.parent.parent.name
        entry_id = f"context_{filepath.parent.name}"
        
        return {
            "id": entry_id,
            "type": "CONTEXT",
            "path": rel(filepath, self.ws),
            "project": proj,
            "ts": "discover",
            "summary": content[:200]
        }
    
    def integrate(self, entries: List[Dict]) -> int:
        """Integra entradas al grafo."""
        self.graph_index.mkdir(parents=True, exist_ok=True)
        existing = self._load_index()
        
        for e in entries:
            existing[e["id"]] = e
        
        self._save_index(existing)
        return len(entries)
    
    def _load_index(self) -> Dict:
        idx_file = self.graph_index / "memory_index.json"
        return json.loads(idx_file.read_text()) if idx_file.exists() else {}
    
    def _save_index(self, index: Dict):
        (self.graph_index / "memory_index.json").write_text(json.dumps(index, indent=2))
    
    def _exists(self, entry_id: str) -> bool:
        return entry_id in self._load_index()