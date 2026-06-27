#!/usr/bin/env python3
"""MementoBloom :: CLI de configuración (T1.4).

Permite actualizar .env o variables de entorno para Redis, Sala, Panel
sin editar código. Compatible con Fase 3.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

KEYS = {
    "redis-host": "REDIS_HOST",
    "redis-port": "REDIS_PORT",
    "sala-port": "SALA_PORT",
    "panel-port": "PANEL_PORT",
    "redis-key": "REDIS_KEY",
    "m360-base-url": "M360_BASE_URL",
    "m360-username": "M360_USERNAME",
    "m360-password": "M360_PASSWORD",
}


def read_env() -> dict[str, str]:
    return read_env_from(ENV_FILE)


def read_env_from(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip()
    return data


def write_env(values: dict[str, str]) -> None:
    existing = read_env()
    existing.update(values)
    lines = ["# MementoBloom environment\n"]
    for k, v in existing.items():
        lines.append(f"{k}={v}\n")
    ENV_FILE.write_text("".join(lines), encoding="utf-8")


def ensure_example() -> None:
    if not ENV_EXAMPLE.exists():
        ENV_EXAMPLE.write_text(
            "# MementoBloom environment example.\n"
            "# Copy to .env and fill only on local machines. Do not commit .env.\n\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Configurar MementoBloom sin editar código")
    parser.add_argument("--redis-host")
    parser.add_argument("--redis-port")
    parser.add_argument("--sala-port")
    parser.add_argument("--panel-port")
    parser.add_argument("--redis-key")
    parser.add_argument("--m360-base-url")
    parser.add_argument("--m360-username")
    parser.add_argument("--m360-password")
    parser.add_argument("--env-file", default=str(ENV_FILE))
    parser.add_argument("--show", action="store_true", help="Mostrar configuración actual")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    ensure_example()

    if args.show:
        data = read_env_from(env_path)
        if not data:
            print("(sin configuración en .env)")
        for k, v in data.items():
            print(f"{k}={v}")
        return 0

    updates: dict[str, str] = {}
    payload = {
        "redis-host": "REDIS_HOST",
        "redis-port": "REDIS_PORT",
        "sala-port": "SALA_PORT",
        "panel-port": "PANEL_PORT",
        "redis-key": "REDIS_KEY",
        "m360-base-url": "M360_BASE_URL",
        "m360-username": "M360_USERNAME",
        "m360-password": "M360_PASSWORD",
    }
    for flag, env_key in payload.items():
        value = getattr(args, flag.replace("-", "_"), None)
        if value is not None:
            updates[env_key] = value

    target = Path(args.env_file)
    existing = read_env_from(target)
    existing.update(updates)
    lines = ["# MementoBloom environment\n"]
    for k, v in existing.items():
        lines.append(f"{k}={v}\n")
    target.write_text("".join(lines), encoding="utf-8")

    if updates:
        print("Actualizado .env:")
        for k, v in updates.items():
            print(f"  {k}={v}")
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
