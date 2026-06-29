#!/usr/bin/env python3
"""Vault integration for MementoBloom"""

import json
from pathlib import Path

VAULT_PATH = Path.home() / ".memento" / "vault.json"

def get_vault() -> dict:
    if VAULT_PATH.exists():
        return json.loads(VAULT_PATH.read_text())
    return {}

def get_credential(name: str) -> str:
    vault = get_vault()
    secret = vault.get("secrets", {}).get(name, {})
    value = secret.get("value", "")
    # Decode base64 if encrypted
    if secret.get("encrypted") and value:
        import base64
        try:
            value = base64.b64decode(value).decode()
        except Exception:
            pass
    return value

def get_source(name: str) -> dict:
    vault = get_vault()
    return vault.get("sources", {}).get(name, {})

if __name__ == "__main__":
    print("🜄 Vault Sources:")
    for name, src in get_vault().get("sources", {}).items():
        print(f"  - {name}: {src}")