#!/usr/bin/env python3
"""Panel Interactivo MementoBloom - Home del proyecto con acceso a herramientas y servicios."""

import json
import os
import socket
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PANEL_PORT", "8766"))

# Configuración de servicios con múltiples endpoints
@dataclass
class ServiceEndpoint:
    name: str
    host: str
    port: int
    type: str  # local, lan, web
    default_port: int = 0

SERVICES = {
    "redis": [
        ServiceEndpoint("local", "localhost", int(os.environ.get("REDIS_PORT", "6379")), "local"),
        ServiceEndpoint("lan", os.environ.get("REDIS_HOST", "192.168.18.59"), int(os.environ.get("REDIS_PORT", "6379")), "lan"),
    ],
    "mariadb": [
        ServiceEndpoint("lan", os.environ.get("MARIADB_HOST", "192.168.18.59"), int(os.environ.get("MARIADB_PORT", "3306")), "lan"),
        ServiceEndpoint("local", "localhost", int(os.environ.get("MARIADB_LOCAL_PORT", "3306")), "local"),
    ],
    "ssh": [
        ServiceEndpoint("lan", os.environ.get("SSH_HOST", "192.168.18.59"), int(os.environ.get("SSH_PORT", "22")), "lan"),
        ServiceEndpoint("local", "localhost", 22, "local"),
    ],
    "adb": [
        ServiceEndpoint("lan", os.environ.get("ADB_HOST", "192.168.18.59"), int(os.environ.get("ADB_PORT", "5037")), "lan"),
        ServiceEndpoint("local", "localhost", 5037, "local"),
    ],
    "sala": [
        ServiceEndpoint("local", "127.0.0.1", int(os.environ.get("SALA_PORT", "8767")), "local"),
    ],
}

def check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except:
        return False

def get_service_status(name: str) -> List[Dict[str, Any]]:
    endpoints = SERVICES.get(name, [])
    results = []
    for ep in endpoints:
        results.append({
            "name": ep.name,
            "host": ep.host,
            "port": ep.port,
            "type": ep.type,
            "ok": check_tcp(ep.host, ep.port),
        })
    return results

def get_all_services_status() -> Dict[str, Any]:
    return {name: get_service_status(name) for name in SERVICES}

def get_handoffs_list(limit: int = 20) -> List[Dict[str, Any]]:
    handoff_dir = ROOT / "projects" / "mementobloom"
    handoffs = []
    if not handoff_dir.exists():
        return handoffs
    for path in sorted(handoff_dir.glob("HANDOFF_*.md"), reverse=True)[:limit]:
        try:
            content = path.read_text()
            # Extract basic info
            first_line = content.split('\n')[0] if content else ""
            handoffs.append({
                "path": str(path.relative_to(ROOT)),
                "name": path.stem,
                "preview": (first_line + "..." if len(first_line) > 80 else first_line),
            })
        except:
            pass
    return handoffs

def get_memory_stats():
    idx_path = ROOT / "memory" / "graph" / "memory_index.json"
    try:
        data = json.loads(idx_path.read_text())
        by_type = {}
        for entry in data.values():
            t = entry.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        return {"entries": len(data), "by_type": by_type}
    except:
        return {"entries": 0, "by_type": {}}

def get_git_status():
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--short"],
            capture_output=True, text=True, timeout=5
        )
        return {"clean": len(result.stdout.strip()) == 0, "raw": result.stdout.strip()}
    except:
        return {"clean": False, "raw": ""}

def get_sala_stats():
    sala_port = int(os.environ.get("SALA_PORT", "8767"))
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{sala_port}/stats", timeout=2) as resp:
            return json.loads(resp.read().decode())
    except:
        return {"error": "sala no disponible"}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MementoBloom Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#08090a;color:#d4d4d4;min-height:100vh}
header{padding:12px 16px;background:#0f1419;border-bottom:1px solid #1f2933}
header h1{font-size:18px;color:#e5e7eb}
nav{padding:8px 16px;background:#0f1419;border-bottom:1px solid #1f2933;display:flex;gap:8px;flex-wrap:wrap}
nav a{padding:4px 10px;background:#111318;color:#d4d4d4;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none}
nav a:hover{background:#1a1f27}
nav a.active{background:#2563eb;color:#fff}
#grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;padding:16px}
.card{background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px}
.card h3{font-size:13px;color:#6b7280;margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em}
.card .value{font-size:16px;color:#e5e7eb;margin-bottom:4px}
.card .detail{font-size:11px;color:#9ca3af}
.status-ok{color:#34d399}
.status-no{color:#f87171}
a.btn{display:inline-block;padding:6px 12px;background:#2563eb;color:#fff;border-radius:4px;text-decoration:none;font-size:12px;margin-right:6px;margin-top:8px}
a.btn:hover{background:#1d4ed8}
#handoff-list{margin-top:8px;font-size:11px}
#handoff-list a{display:block;color:#60a5fa;text-decoration:none;margin:4px 0}
</style>
</head>
<body>
<header>
<h1>🜄 MementoBloom · Panel de Control</h1>
</header>
<nav>
<a href="/" class="active">Dashboard</a>
<a href="/services">Servicios</a>
<a href="/handoffs">Handoffs</a>
</nav>
<div id="content">
<div id="grid">
<div class="card"><h3>Servicio Redis</h3><div class="value" id="redis-status">Verificando...</div><div class="detail">Instancias: local, lan</div></div>
<div class="card"><h3>Sala Local</h3><div class="value" id="sala-status">Verificando...</div><div class="detail">http://127.0.0.1:8767</div></div>
<div class="card"><h3>Memoria</h3><div class="value" id="mem-count">Verificando...</div><div class="detail" id="mem-detail"></div></div>
<div class="card"><h3>Git</h3><div class="value" id="git-status">Verificando...</div><div class="detail" id="git-detail"></div></div>
</div>
</div>
<script>
fetch('/api/stats').then(r=>r.json()).then(d=>{{
  document.getElementById('redis-status').innerHTML = d.services.redis.some(s=>s.ok) ? '<span class=status-ok>● OK</span>' : '<span class=status-no>● Offline</span>';
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

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except:
            return {}

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_html(HTML_TEMPLATE)
        elif self.path == "/services":
            services = get_all_services_status()
            html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Servicios</title>
<style>body{margin:0;padding:16px;background:#08090a;color:#d4d4d4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.card{background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px;margin:8px 0}
h3{margin:0 0 8px 0;color:#e5e7eb}
.status-ok{color:#34d399}.status-no{color:#f87171}
table{width:100%;border-collapse:collapse;margin-bottom:8px}
td{padding:4px 8px;color:#9ca3af;border-bottom:1px solid #1f2933}
.btn{padding:4px 8px;background:#2563eb;color:#fff;border:none;border-radius:4px;font-size:11px;cursor:pointer;margin:0 2px}
.btn:hover{background:#1d4ed8}
.btn.danger{background:#ef4444}
.btn.danger:hover{background:#dc2626}
</style></head><body>
<nav style="padding:8px 16px;background:#0f1419;display:flex;gap:8px">
<a href="/" style="padding:4px 10px;background:#111318;color:#d4d4d4;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Dashboard</a>
<a href="/services" style="padding:4px 10px;background:#2563eb;color:#fff;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Servicios</a>
<a href="/handoffs" style="padding:4px 10px;background:#111318;color:#d4d4d4;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Handoffs</a>
</nav>
<div style="padding:16px">"""
            for name, endpoints in services.items():
                html += f"<div class='card'><h3>{name.upper()}</h3><table>"
                for ep in endpoints:
                    status = "● OK" if ep["ok"] else "● Offline"
                    html += f"<tr><td>{ep['type']}</td><td>{status}</td><td>{ep['host']}:{ep['port']}</td>"
                    html += f"<td><button class='btn' onclick='testSvc(\"{name}\",\"{ep['name']}\")'>Test</button>"
                    if not ep["ok"]:
                        html += f"<button class='btn' onclick='startSvc(\"{name}\")'>Start</button>"
                    html += "</td></tr>"
                html += "</table></div>"
            html += """</div>
<script>
function testSvc(svc,ep){fetch('/api/service/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({service:svc,endpoint:ep})}).then(r=>r.json()).then(d=>alert(d.ok?'OK':'Offline'))}
function startSvc(svc){fetch('/api/service/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({service:svc})}).then(r=>r.json()).then(d=>alert(d.output||d.error))}
</script></body></html>"""
            self._send_html(html)
        elif self.path == "/handoffs":
            handoffs = get_handoffs_list()
            html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Handoffs</title>
<style>body{margin:0;padding:16px;background:#08090a;color:#d4d4d4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
a{color:#60a5fa;text-decoration:none;display:block;padding:8px 0;border-bottom:1px solid #1f2933}
</style></head><body>
<nav style="padding:8px 16px;background:#0f1419;display:flex;gap:8px">
<a href="/" style="padding:4px 10px;background:#111318;color:#d4d4d4;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Dashboard</a>
<a href="/services" style="padding:4px 10px;background:#111318;color:#d4d4d4;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Servicios</a>
<a href="/handoffs" style="padding:4px 10px;background:#2563eb;color:#fff;border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">Handoffs</a>
</nav>
<h2 style="color:#e5e7eb;padding:16px 0 8px 16px;margin:0">Handoffs recientes</h2>"""
            for h in handoffs:
                html += f'<a href="/handoffs/{h["name"]}">{h["name"]}</a>'
            html += "</body></html>"
            self._send_html(html)
        elif self.path.startswith("/handoffs/HANDOFF_"):
            name = self.path.split("/")[-1]
            path = ROOT / "projects" / "mementobloom" / f"{name}.md"
            if path.exists():
                content = path.read_text()
                # Simple HTML escape
                content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{name}</title>"
                html += '<style>body{margin:0;padding:16px;background:#08090a;color:#d4d4d4;font-family:monospace;font-size:13px;white-space:pre-wrap}</style></head><body>'
                html += content + "</body></html>"
                self._send_html(html)
            else:
                self._send_json({"error": "handoff no encontrado"}, 404)
        elif self.path == "/api/stats":
            services = get_all_services_status()
            sala = get_sala_stats()
            mem = get_memory_stats()
            git_status_raw = get_git_status()
            self._send_json({
                "services": services,
                "sala": {"ok": "messages" in sala, "messages": sala.get("messages", 0)},
                "memory": mem,
                "git": {"clean": git_status_raw.get("clean", False), "changes": len(git_status_raw.get("raw", "").splitlines()) if git_status_raw.get("raw") else 0},
            })
        elif self.path == "/api/services":
            self._send_json(get_all_services_status())
        elif self.path == "/api/handoffs":
            self._send_json(get_handoffs_list())
        elif self.path == "/api/service/start":
            # POST expected with service name in body
            import urllib.request
            payload = self._read_body()
            svc = payload.get("service", "")
            if svc == "sala":
                result = subprocess.run([sys.executable, str(ROOT / "tools" / "sala.py")], capture_output=True, text=True)
                self._send_json({"ok": True, "output": "sala started"})
            elif svc == "redis-flush":
                # ONLY flush if explicitly requested
                redis_cmd(["FLUSHALL"])
                self._send_json({"ok": True, "output": "redis flushed"})
            else:
                self._send_json({"ok": False, "error": "service not supported"})
        elif self.path == "/api/service/test":
            payload = self._read_body()
            svc = payload.get("service", "")
            ep = payload.get("endpoint", "lan")
            services = get_all_services_status()
            if svc in services:
                for s in services[svc]:
                    if s["name"] == ep:
                        self._send_json({"ok": s["ok"], "service": svc, "endpoint": ep})
                        return
            self._send_json({"ok": False, "error": "not found"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/service/start":
            payload = self._read_body()
            svc = payload.get("service", "")
            if svc == "sala":
                subprocess.Popen([sys.executable, str(ROOT / "tools" / "sala.py")])
                self._send_json({"ok": True, "output": "sala started"})
            elif svc == "redis-flush":
                redis_cmd(["FLUSHALL"])
                self._send_json({"ok": True, "output": "redis flushed"})
            else:
                self._send_json({"ok": False, "error": "service not supported"})
        elif self.path == "/api/service/test":
            payload = self._read_body()
            svc = payload.get("service", "")
            ep_name = payload.get("endpoint", "lan")
            services = get_all_services_status()
            if svc in services:
                for s in services[svc]:
                    if s["name"] == ep_name:
                        self._send_json({"ok": s["ok"], "service": svc, "endpoint": ep_name})
                        return
            self._send_json({"ok": False, "error": "not found"})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    print(f"panel :: http://127.0.0.1:{PORT}")
    HTTPServer(("0.0.0.0", PORT), PanelHandler).serve_forever()