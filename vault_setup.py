#!/usr/bin/env python3
"""Vault setup - Interfaz simple para configurar credenciales"""

import json
from pathlib import Path
import sys

VAULT_PATH = Path.home() / ".memento" / "vault.json"

SOURCES = {
    "ollama": {"host": "http://localhost:11434"},
    "local_dev": {"host": "localhost", "port": 8000, "description": "Django dev server"},
    "aws": {"bucket": "your-bucket", "region": "us-east-1", "description": "S3 storage"},
    "gdrive": {"folder_id": "your-folder-id", "description": "Google Drive"},
    "email": {"smtp": "smtp.gmail.com", "port": 587, "description": "Email SMTP"}
}

def setup():
    vault = json.loads(VAULT_PATH.read_text()) if VAULT_PATH.exists() else {}
    
    print("🜄 VAULT SETUP - Configurar fuentes")
    print("=" * 40)
    
    for name, config in SOURCES.items():
        print(f"\n[{name}] {config.get('description', '')}")
        if vault.get("sources", {}).get(name):
            print(f"  ✓ Already configured")
            continue
        
        val = input(f"  Configurar? (Enter=skip, otro=aceptar): ")
        if val.strip():
            vault.setdefault("sources", {})[name] = config
            print(f"  ✓ {name} configurado")
    
    # Secrets (placeholder - sin keyring)
    print("\n--- Secrets (sin keyring) ---")
    if "secrets" not in vault:
        vault["secrets"] = {}
    
    vault["secrets"]["template"] = "***CONFIGURE***"
    vault["last_update"] = __import__('datetime').datetime.now().isoformat()
    
    VAULT_PATH.write_text(json.dumps(vault, indent=2))
    print(f"\n✓ Vault actualizado: {VAULT_PATH}")

if __name__ == "__main__":
    if "--auto" in sys.argv:
        # Auto-setup sin prompts
        vault = {"version": "1.0", "sources": SOURCES, "secrets": {}}
        VAULT_PATH.write_text(json.dumps(vault, indent=2))
        print("✓ Vault auto-configurado")
    else:
        setup()