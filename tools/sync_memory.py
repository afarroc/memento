#!/usr/bin/env python3
"""Sincroniza entradas de memoria entre .memento/memory/graph/ y memory/graph/"""

import json
from pathlib import Path

from core.paths import workspace_root

WS = workspace_root()
MEMENTO = WS / ".memento" / "memory" / "graph" / "memory_index.json"
MEMORY = WS / "memory" / "graph" / "memory_index.json"

def load(path):
    with open(path) as f:
        return json.load(f)

def save(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

memento = load(MEMENTO)
memory = load(MEMORY)

# Encontrar claves que están en memento pero no en memory
faltantes = {k: v for k, v in memento.items() if k not in memory}
print(f"Entradas en .memento que faltan en memory/: {len(faltantes)}")
for k in sorted(faltantes.keys()):
    print(f"  + {k}")

# Merge: memory absorbe las entradas de memento
memory.update(faltantes)
save(MEMORY, memory)
print(f"Memory actualizado: {len(memory)} entradas totales")