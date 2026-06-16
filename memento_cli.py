#!/usr/bin/env python3
"""MementoBloom Interactive CLI"""

import cmd
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS_ROOT = ROOT.parent if (ROOT / "projects").exists() else ROOT
sys.path.insert(0, str(ROOT))

from tools.quick_scan import QuickScan
from tools.context_builder import ContextBuilder
from vault_client import get_vault, get_source


class MementoCLI(cmd.Cmd):
    intro = "MementoBloom Interactive Shell - 'help' para comandos"
    prompt = "memento> "

    def __init__(self):
        super().__init__()
        index_path = WS_ROOT / ".memento" / "memory" / "graph" / "memory_index.json"
        self.cb = ContextBuilder(str(index_path))

    def do_status(self, arg):
        """Estado del sistema de memoria"""
        status = self.cb.ready_check()
        print(f"Estado: {status}")

    def do_bootstrap(self, arg):
        """Imprimir contexto universal modelo-agnóstico"""
        subprocess.run([sys.executable, str(ROOT / "tools" / "bootstrap_context.py"), "--print"])

    def do_session(self, arg):
        """Preparar seed y contexto local de sesión - session [--quick] [--services]"""
        cmd = [sys.executable, str(ROOT / "tools" / "session_start.py")]
        if arg.strip():
            cmd.extend(arg.split())
        subprocess.run(cmd)

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
        qs = QuickScan(str(WS_ROOT))
        qs.scan()

    def do_vault(self, arg):
        """Ver fuentes configuradas en vault"""
        vault = get_vault()
        print("Fuentes configuradas:")
        for name, src in vault.get("sources", {}).items():
            print(f"  - {name}: {src}")

    def do_agent(self, arg):
        """Generar prompt genérico con contexto Memento - agent \"pregunta\" [--limit N]"""
        try:
            tokens = shlex.split(arg)
        except ValueError:
            tokens = arg.split()

        if not tokens:
            print("Uso: agent \"pregunta\" [--limit N]")
            return

        question = tokens[0]
        extra_args = []
        i = 1
        while i < len(tokens):
            if tokens[i] == "--limit" and i + 1 < len(tokens):
                extra_args.extend([tokens[i], tokens[i + 1]])
                i += 2
            else:
                i += 1

        subprocess.run([sys.executable, str(ROOT / "tools" / "agent_prompt.py"), question, *extra_args])

    def do_send(self, arg):
        """Enviar mensaje al panel - send \"mensaje\" """
        import urllib.request

        text = arg.strip().strip('"')
        if not text:
            print("Uso: send \"mensaje\"")
            return
        payload = {"type": "text", "text": text}
        try:
            req = urllib.request.Request(
                "http://localhost:8767/send",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
            print(f"Enviado al panel: {text}")
        except Exception as e:
            print(f"Error panel: {e}")

    def do_exit(self, arg):
        """Salir del CLI"""
        print("Cerrando MementoBloom...")
        return True

    def default(self, line):
        print(f"Comando desconocido: {line}. Usar 'help'")


if __name__ == "__main__":
    MementoCLI().cmdloop()