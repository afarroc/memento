from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json

@dataclass
class MemoryNode:
    id: str
    entry_type: str
    project: str
    timestamp: str
    summary: str
    content: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    vector: Optional[List[float]] = None
    importance: float = 0.0
    
    def to_compact(self) -> str:
        return f"{self.id}|{self.entry_type}|{self.timestamp}|{hash(self.summary)%10000}"

@dataclass  
class MemoryEdge:
    source: str
    target: str
    weight: float = 1.0
    relationship: str = "references"

class MemoryGraph:
    def __init__(self, index_path: str):
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: List[MemoryEdge] = []
        self.index_path = index_path
    
    def add_node(self, node: MemoryNode):
        self.nodes[node.id] = node
    
    def link(self, source: str, target: str, weight: float = 1.0):
        self.edges.append(MemoryEdge(source, target, weight))
    
    def save(self):
        data = {
            "nodes": {k: {"id": v.id, "type": v.entry_type, "project": v.project, 
                         "ts": v.timestamp, "summary": v.summary, "tags": v.tags}
                       for k, v in self.nodes.items()},
            "edges": [{"src": e.source, "tgt": e.target, "weight": e.weight} for e in self.edges]
        }
        with open(self.index_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        try:
            with open(self.index_path, 'r') as f:
                data = json.load(f)
            for nid, ndata in data.get("nodes", {}).items():
                self.nodes[nid] = MemoryNode(
                    id=ndata["id"], entry_type=ndata["type"],
                    project=ndata["project"], timestamp=ndata["ts"],
                    summary=ndata["summary"], tags=ndata.get("tags", [])
                )
        except FileNotFoundError:
            pass