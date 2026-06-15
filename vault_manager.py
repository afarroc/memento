#!/usr/bin/env python3
"""Vault Manager - Credenciales (sin keyring dependency)"""

import json
from pathlib import Path
from datetime import datetime
import base64

class Vault:
    def __init__(self, config_path: str = None):
        self.home = Path.home() / ".memento"
        self.home.mkdir(exist_ok=True)
        self.config_path = Path(config_path) if config_path else self.home / "vault.json"
        self.config = self._load()
    
    def _load(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"sources": {}, "secrets": {}, "version": "1.0"}
    
    def save(self):
        self.config_path.write_text(json.dumps(self.config, indent=2))
    
    def set_secret(self, key: str, value: str, encrypted: bool = False):
        """Guarda secreto (marca para encriptar en el futuro)."""
        if encrypted:
            value = base64.b64encode(value.encode()).decode()
        self.config["secrets"][key] = {"value": value, "encrypted": encrypted}
        self.save()
        print(f"✓ Secret '{key}' saved")
    
    def get_secret(self, key: str) -> str:
        """Recupera secreto."""
        s = self.config.get("secrets", {}).get(key, {})
        if s.get("encrypted"):
            return base64.b64decode(s["value"].encode()).decode()
        return s.get("value", "")
    
    def set_source(self, name: str, config: dict):
        self.config["sources"][name] = config
        self.save()
    
    def get_source(self, name: str) -> dict:
        return self.config.get("sources", {}).get(name, {})

def init_vault():
    vault = Vault()
    vault.config = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "sources": {
            "vscode": {"workspace": "/Volumes/Macintosh HD - Datos/mementobloom"},
            "local_dev": {"host": "localhost", "port": 8000, "protocol": "http"},
            "ollama": {"host": "http://localhost:11434"},
            "aws_s3": {"bucket": None, "region": "us-east-1"},
            "gdrive": {"folder_id": None}
        },
        "secrets": {}
    }
    vault.save()
    return vault

if __name__ == "__main__":
    import sys
    v = Vault()
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_vault()
        print(f"✓ Vault initialized at {v.config_path}")
    else:
        print(json.dumps(v.config, indent=2))