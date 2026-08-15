#!/usr/bin/env python3
"""MementoBloom :: Generador de config/services.json desde variables de entorno.

Genera un archivo local de servicios sin hardcodear IPs/hosts específicos.
Si no hay variables definidas, usa defaults neutros (localhost / puertos estándar).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "services.json"


def _env(key: str, fallback: str) -> str:
    return os.environ.get(key, fallback)


def generate(workspace: Path | None = None) -> dict:
    root = workspace or ROOT
    redis_host = _env("REDIS_HOST", "localhost")
    redis_port = _env("REDIS_PORT", "6379")
    mariadb_host = _env("MARIADB_HOST", "localhost")
    mariadb_port = _env("MARIADB_PORT", "3306")
    ssh_host = _env("SSH_HOST", "localhost")
    ssh_port = _env("SSH_PORT", "22")
    adb_host = _env("ADB_HOST", "localhost")
    adb_port = _env("ADB_PORT", "5037")
    sala_port = _env("SALA_PORT", "8767")
    panel_port = _env("PANEL_PORT", "8766")

    def _remote_endpoint(host: str, port: str, name: str) -> dict:
        return {"name": name, "host": host, "port": int(port), "type": "remote"}

    redis_endpoints = [{"name": "local", "host": "localhost", "port": 6379, "type": "local"}]
    if redis_host not in {"localhost", "127.0.0.1"}:
        redis_endpoints.append(_remote_endpoint(redis_host, redis_port, "env"))

    mariadb_endpoints = [{"name": "local", "host": "localhost", "port": 3306, "type": "local"}]
    if mariadb_host not in {"localhost", "127.0.0.1"}:
        mariadb_endpoints.append(_remote_endpoint(mariadb_host, mariadb_port, "env"))

    ssh_endpoints = [{"name": "local", "host": "localhost", "port": 22, "type": "local"}]
    if ssh_host not in {"localhost", "127.0.0.1"}:
        ssh_endpoints.append(_remote_endpoint(ssh_host, ssh_port, "env"))

    adb_endpoints = [{"name": "local", "host": "localhost", "port": 5037, "type": "local"}]
    if adb_host not in {"localhost", "127.0.0.1"}:
        adb_endpoints.append(_remote_endpoint(adb_host, adb_port, "env"))

    return {
        "services": {
            "redis": {
                "description": "Redis message queue for sala",
                "endpoints": redis_endpoints,
            },
            "mariadb": {
                "description": "MariaDB database server",
                "endpoints": mariadb_endpoints,
            },
            "ssh": {
                "description": "SSH access server",
                "endpoints": ssh_endpoints,
            },
            "adb": {
                "description": "Android Debug Bridge",
                "endpoints": adb_endpoints,
            },
            "sala": {
                "description": "MementoBloom chat room",
                "endpoints": [
                    {"name": "local", "host": "127.0.0.1", "port": int(sala_port), "type": "local"}
                ],
            },
            "panel": {
                "description": "MementoBloom dashboard",
                "endpoints": [
                    {"name": "local", "host": "127.0.0.1", "port": int(panel_port), "type": "local"}
                ],
            },
        },
        "defaults": {
            "redis_host": redis_host,
            "redis_port": int(redis_port),
            "redis_key": _env("REDIS_KEY", "memento_panel_items"),
            "mariadb_host": mariadb_host,
            "mariadb_port": int(mariadb_port),
            "sala_port": int(sala_port),
            "panel_port": int(panel_port),
            "note": "Generado automaticamente por tools/generate_services_config.py. No hardcodear credenciales ni IPs privadas aqui.",
        },
    }


def write_config(path: Path | None = None) -> dict:
    target = path or DEFAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    data = generate()
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generar config/services.json sin secretos")
    parser.add_argument("--force", action="store_true", help="Sobrescribir archivo existente")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace root (default: repo root)")
    parser.add_argument("--path", "-o", default=str(DEFAULT_PATH), help="Ruta de salida")
    parser.add_argument("--json", action="store_true", help="Imprimir JSON generado")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve() if args.workspace else ROOT
    data = generate(workspace=workspace)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    target = Path(args.path)
    if target.exists() and not args.force:
        print(f"No se generó: {target} ya existe. Usar --force para sobrescribir")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generado: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
