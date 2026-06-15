#!/usr/bin/env python3
"""MementoBloom Interactive CLI"""

import cmd
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from quick_scan import QuickScan
from context_builder import ContextBuilder
from vault_client import get_vault, get_source

class MementoCLI(cmd.Cmd):
    intro = "🜄 MementoBloom Interactive Shell - 'help' para comandos"
    prompt = "memento> "
    
    def __init__(self):
        super().__init__()
        self.cb = ContextBuilder("/Volumes/Macintosh HD - Datos/mementobloom/memory/graph/memory_index.json")
    
    def do_status(self, arg):
        """Estado del sistema de memoria"""
        status = self.cb.ready_check()
        print(f"Estado: {status}")
    
    def do_context(self, arg):
        """Ver contexto - context --project X --type HANDOFF --limit N --ready"""
        args = arg.split()
        kwargs = {}
        i = 0
        while i < len(args):
            if args[i] == "--ready":
                print(json.dumps(self.cb.ready_check(), indent=2))
                return
            elif args[i] == "--project" and i + 1 < len(args):
                kwargs["project"] = args[i + 1]
                i += 2
            elif args[i] == "--type" and i + 1 < len(args):
                kwargs["type"] = args[i + 1]
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                kwargs["limit"] = int(args[i + 1])
                i += 2
            else:
                i += 1
        
        print(self.cb.get_expanded_context(**kwargs))
    
    def do_scan(self, arg):
        """Re-escanear workspace para nuevas entradas"""
        qs = QuickScan("/Volumes/Macintosh HD - Datos")
        qs.scan()
    
    def do_vault(self, arg):
        """Ver fuentes configuradas en vault"""
        vault = get_vault()
        print("Fuentes configuradas:")
        for name, src in vault.get("sources", {}).items():
            print(f"  - {name}: {src}")
    
    def do_send(self, arg):
        """Enviar mensaje al panel - send \"mensaje\" """
        import urllib.request
        text = arg.strip().strip('"')
        if not text:
            print("Uso: send \"mensaje\"")
            return
        payload = {"type": "text", "text": f"🜄 {text}"}
        try:
            req = urllib.request.Request(
                "http://localhost:8767/send",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=5)
            print(f"✓ Enviado al panel: {text}")
        except Exception as e:
            print(f"✗ Error panel: {e}")
    
    def do_kilo(self, arg):
        """Consultar agente Kilo - kilo \"pregunta\" [-m modelo] [-s session]"""
        import subprocess
        text = arg.strip().strip('"')
        if not text:
            print("Uso: kilo \"pregunta\" [-m modelo] [-s session]")
            return
        modelo = "kilo/~openai/gpt-mini-latest"
        session_id = None
        args = arg.split()
        for i, a in enumerate(args):
            if a == "-m" and i + 1 < len(args):
                modelo = args[i + 1]
            elif a == "-s" and i + 1 < len(args):
                session_id = args[i + 1]
        kilo_path = str(Path.home() / ".local/bin/kilo")
        cmd = [kilo_path, "run", "--model", modelo]
        if session_id:
            cmd.extend(["--session", session_id])
        cmd.append(text)
        try:
            print(f"🜄 [Kilo] {text[:50]}...")
            subprocess.run(cmd, timeout=60)
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def do_autonomous(self, arg):
        """Iniciar Kilo autónomo con contexto Memento - autonomous \"pregunta\""""
        import subprocess
        text = arg.strip().strip('"')
        if not text:
            print("Uso: autonomous \"pregunta\"")
            return
        subprocess.run(["python3", "/Volumes/Macintosh HD - Datos/mementobloom/kilo_autonomous.py", text])
    
    def do_exit(self, arg):
        """Salir del CLI"""
        print("🜄 Cerrando MementoBloom...")
        return True
    
    def default(self, line):
        print(f"Comando desconocido: {line}. Usar 'help'")

if __name__ == "__main__":
    MementoCLI().cmdloop()