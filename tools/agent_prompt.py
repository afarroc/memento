#!/usr/bin/env python3
"""tools/agent_prompt.py - Prompt genérico con contexto MementoBloom

Uso:
    python3 tools/agent_prompt.py "pregunta" [--limit 10]

Este script no invoca ningún agente externo. Genera un prompt neutral con
memoria reciente para que cualquier modelo, CLI o asistente lo consuma.
"""

import argparse
import json
import sys
from pathlib import Path

from core.paths import workspace_root

INDEX_PATH = workspace_root() / "memory" / "graph" / "memory_index.json"


def load_context(limit: int) -> str:
    if not INDEX_PATH.exists():
        return "# MEMENTO CONTEXT AUTO-LOADED\n- memory/graph/memory_index.json no existe todavía."

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    entries = [e for e in index.values() if isinstance(e, dict)]
    entries.sort(key=lambda e: str(e.get("ts", "")), reverse=True)
    lines = ["# MEMENTO CONTEXT AUTO-LOADED"]
    for entry in entries[:limit]:
        summary = str(entry.get("summary", "")).replace("\n", " ")[:120]
        lines.append(
            f"- [{entry.get('id', '?')}] {entry.get('type', '?')} | "
            f"project={entry.get('project', '?')} | ts={entry.get('ts', '?')} | {summary}"
        )
    return "\n".join(lines)


def build_prompt(question: str, context: str) -> str:
    return (
        "# Rol\n"
        "Actúa como agente de continuidad del proyecto MementoBloom.\n\n"
        "# Contexto cargado\n"
        f"{context}\n\n"
        "# Pregunta o tarea\n"
        f"{question}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generar prompt con contexto MementoBloom")
    parser.add_argument("prompt", help="Pregunta o tarea para el agente")
    parser.add_argument("--limit", type=int, default=10, help="Cantidad de entradas de memoria a incluir")
    args = parser.parse_args()

    context = load_context(args.limit)
    print(build_prompt(args.prompt, context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
