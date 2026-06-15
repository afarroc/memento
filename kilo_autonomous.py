#!/usr/bin/env python3
"""kilo_autonomous.py - Agente Kilo autónomo con memoria MementoBloom

Uso: python3 kilo_autonomous.py "pregunta"
Carga contexto automáticamente desde memory/graph/memory_index.json
"""

import json
import subprocess
import sys
from pathlib import Path

KILO_PATH = str(Path.home() / ".local/bin/kilo")

def load_context():
    idx_path = Path("/Volumes/Macintosh HD - Datos/mementobloom/memory/graph/memory_index.json")
    if not idx_path.exists():
        return ""
    idx = json.loads(idx_path.read_text())
    lines = ["# 🜄 MEMENTO CONTEXT AUTO-LOADED"]
    for entry_id, entry in list(idx.items())[:10]:
        lines.append(f"- [{entry_id}] {entry.get('type','?')}: {entry.get('summary','')[:60]}")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 kilo_autonomous.py \"pregunta\"")
        sys.exit(1)
    
    question = sys.argv[1]
    context = load_context()
    
    # Prompt con contexto
    prompt = f"{context}\n\n ====\n\n {question}"
    
    subprocess.run([KILO_PATH, "run", "--model", "kilo/~openai/gpt-mini-latest", prompt])

if __name__ == "__main__":
    main()