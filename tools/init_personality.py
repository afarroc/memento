#!/usr/bin/env python3
"""Inicializa el archivo de personalidad del usuario desde el template.

Uso:
    python3 tools/init_personality.py
    python3 tools/init_personality.py --force
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
EXAMPLE = WS / "memory" / "personality" / "user_personality.example.md"
TARGET = WS / "memory" / "personality" / "user_personality.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializa memoria de personalidad del usuario")
    parser.add_argument("--force", action="store_true", help="Sobrescribir archivo existente")
    args = parser.parse_args()

    if not EXAMPLE.exists():
        print(f"ERROR: no existe el template en {EXAMPLE}")
        return 1

    if TARGET.exists() and not args.force:
        print(f"Ya existe {TARGET}. Usar --force para sobrescribir.")
        return 0

    shutil.copy2(EXAMPLE, TARGET)
    print(f"Personalidad inicializada en: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
