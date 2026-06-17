#!/usr/bin/env python3
"""Panel Interactivo MementoBloom - Home del proyecto con acceso a herramientas y servicios."""

import json
import os
import socket
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PANEL_PORT", "8766"))
REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.18.59")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
SALA_PORT = int(os.environ.get("SALA_PORT", "8767"))
REDIS_KEY = os.environ.get("REDIS_KEY", "memento_panel_items")


def redis_cmd(args):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((REDIS_HOST, REDIS_PORT))
        chunks = [f"*{len(args)}\r\n".encode("utf-8")]
        for arg in args:
            encoded = str(arg).encode("utf-8")
            chunks.append(f"${len(encoded)}\r\n".encode("utf-8"))
            chunks.append(encoded)
            chunks.append(b"\r\n")
        s.sendall(b"".join(chunks))
        received = bytearray()
        while True:
            try:
                chunk = s.recv(65536)
                received.extend(chunk)
                if not chunk or received.endswith(b"\r\n"):
                    break
            except socket.timeout:
                break
        s.close()
        return {"ok": True, "data": received.decode(errors="replace")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def redis_ping():
    r = redis_cmd(["PING"])
    return r.get("ok") and "PONG" in r.get("data", "")


def get_sala_stats():
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{SALA_PORT}/stats", timeout=2) as resp:
            return json.loads(resp.read().decode())
    except:
        return {"error": "sala no disponible"}


def get_memory_stats():
    idx_path = ROOT / "memory" / "graph" / "memory_index.json"
    try:
        return json.loads(idx_path.read_text())
    except:
        return {}


def get_git_status():
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--short"],
            capture_output=True, text=True, timeout=5
        )
        return {"clean": len(result.stdout.strip()) == 0, "raw": result.stdout.strip()}
    except:
        return {"error": "git no disponible"}


def get_latest_commit():
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--oneline"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return "?"


HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MementoBloom Panel</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#08090a;color:#d4d4d4;min-height:100vh}}
header{{padding:12px 16px;background:#0f1419;border-bottom:1px solid #1f2933}}
header h1{{font-size:18px;color:#e5e7eb}}
#grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;padding:16px}}
.card{{background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px}}
.card h3{{font-size:13px;color:#6b7280;margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em}}
.card .value{{font-size:16px;color:#e5e7eb;margin-bottom:4px}}
.card .detail{{font-size:11px;color:#9ca3af}}
.status-ok{{color:#34d399}}
.status-no{{color:#f87171}}
a.btn{{display:inline-block;padding:6px 12px;background:#2563eb;color:#fff;border-radius:4px;text-decoration:none;font-size:12px;margin-right:6px;margin-top:8px}}
a.btn:hover{{background:#1d4ed8}}
</style>
</head>
<body>
<header>
<h1>🜄 MementoBloom · Panel de Control</h1>
</header>
<div id="grid">
<div class="card"><h3>Servicio Redis</h3><div class="value" id="redis-status">Verificando...</div><div class="detail">{REDIS_HOST}:{REDIS_PORT}</div></div>
<div class="card"><h3>Sala Local</h3><div class="value" id="sala-status">Verificando...</div><div class="detail">http://127.0.0.1:{SALA_PORT}</div></div>
<div class="card"><h3>Memoria</h3><div class="value" id="mem-count">Verificando...</div><div class="detail" id="mem-detail"></div></div>
<div class="card"><h3>Git</h3><div class="value" id="git-status">Verificando...</div><div class="detail" id="git-detail"></div></div>
<div class="card"><h3>Acciones rápidas</h3>
<a href="/bootstrap" class="btn">Bootstrap Context</a>
<a href="/optimize" class="btn">Optimize Agent</a>
</div>
</div>
<script>
fetch('/api/stats').then(r=>r.json()).then(d=>{{
  document.getElementById('redis-status').innerHTML = d.redis.ok ? '<span class=status-ok>● OK</span>' : '<span class=status-no>● Offline</span>';
  document.getElementById('sala-status').innerHTML = d.sala.ok ? '<span class=status-ok>● OK</span> ('+d.sala.messages+' msgs)' : '<span class=status-no>● Offline</span>';
  document.getElementById('mem-count').textContent = d.memory.entries;
  document.getElementById('mem-detail').textContent = 'HANDOFF='+d.memory.by_type.HANDOFF+' | CONTEXT='+d.memory.by_type.CONTEXT;
  document.getElementById('git-status').innerHTML = d.git.clean ? '<span class=status-ok>● Limpio</span>' : '<span class=status-no>● '+d.git.changes+' cambios</span>';
}});
</script>
</body>
</html>"""


class PanelHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == "/api/stats":
            sala = get_sala_stats()
            mem = get_memory_stats()
            git_status_raw = get_git_status()
            self._send_json({
                "redis": {"ok": redis_ping()},
                "sala": {"ok": "messages" in sala, "messages": sala.get("messages", 0)},
                "memory": {
                    "entries": len(mem),
                    "by_type": {"HANDOFF": mem.get("by_type", {}).get("HANDOFF", 0), "CONTEXT": mem.get("by_type", {}).get("CONTEXT", 0)},
                },
                "git": {"clean": git_status_raw.get("clean", False), "changes": len(git_status_raw.get("raw", "").splitlines()) if git_status_raw.get("raw") else 0},
            })
        elif self.path == "/bootstrap":
            cmd = f"python3 {ROOT}/tools/bootstrap_context.py --print"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            self._send_json({"ok": result.returncode == 0, "output": result.stdout})
        elif self.path == "/optimize":
            cmd = f"python3 {ROOT}/tools/optimize_agent.py --context"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            self._send_json({"ok": result.returncode == 0, "output": result.stdout})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"panel :: http://127.0.0.1:{PORT}")
    HTTPServer(("0.0.0.0", PORT), PanelHandler).serve_forever()