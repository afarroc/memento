#!/usr/bin/env python3
"""Crea ticket en M360 para atender informe de optimización TaxiLima2026.

Uso:
    python3 tools/create_optimizacion_ticket.py
    M360_USERNAME=user M360_PASSWORD=pass M360_API_KEY=key python3 tools/create_optimizacion_ticket.py

Configuración requerida:
    M360_USERNAME: usuario M360
    M360_PASSWORD: contraseña M360
    M360_API_KEY: API key para escritura (Bearer)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.m360_bridge.client import M360Client


def main() -> int:
    username = os.environ.get("M360_USERNAME")
    password = os.environ.get("M360_PASSWORD")
    api_key = os.environ.get("M360_API_KEY")

    if not username or not password:
        print("ERROR: Faltan variables de entorno M360_USERNAME y M360_PASSWORD")
        print("Uso: M360_USERNAME=user M360_PASSWORD=pass python3 tools/create_optimizacion_ticket.py")
        return 1

    base_url = os.environ.get("M360_BASE_URL", "http://127.0.0.1:8000")
    client = M360Client(base_url=base_url, username=username, password=password)

    title = "TAXI-OPT-001: Optimizar arquitectura de simulación TaxiLima2026"
    description = (
        "Atender informe de optimización arquitectónica de TaxiLima2026 (2026-08-23).\n\n"
        "Objetivos:\n"
        "1. Migrar a Mesa-Frames con backend Polars para escalabilidad a 10^5+ agentes\n"
        "2. Optimizar espacio discreto con shuffle_do() y cache de propiedades\n"
        "3. Crear capa de orquestación desacoplada entre simulación y reglas de negocio\n"
        "4. Preparar arquitectura multijuegos con estado compartido autoritativo\n\n"
        "Documentación: projects/TaxiLima2026/docs/optimizacion_arquitectura.md\n"
        "Proyecto M360: TaxiLima2026 (ID 23)\n"
    )

    try:
        result = client.create_task(
            title=title,
            project_id=23,
            description=description,
            important=True,
        )
        print(f"Ticket creado: {result}")
        return 0
    except Exception as exc:
        print(f"Error creando ticket: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())