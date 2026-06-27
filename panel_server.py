#!/usr/bin/env python3
"""Panel Interactivo MementoBloom - Home del proyecto con acceso a herramientas y servicios."""

import json
import os
import socket
import subprocess
import sys
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.paths import ROOT, detect_project_name, workspace_root
from core.services import find_free_port

CONFIG_FILE = ROOT / "config" / "services.json"
PANEL_PORT = int(os.environ.get("PANEL_PORT", "8766"))
PORT = PANEL_PORT


def load_services_config():
    """Load services from config file, fallback to defaults."""
    config = {"services": {}, "defaults": {}}
    try:
        if CONFIG_FILE.exists():
            config = json.loads(CONFIG_FILE.read_text())
    except:
        pass
    return config

@dataclass
class ServiceEndpoint:
    name: str
    host: str
    port: int
    type: str

SERVICES = {
    "redis": [
        ServiceEndpoint("local", "localhost", int(os.environ.get("REDIS_PORT", "6379")), "local"),
        ServiceEndpoint("lan", os.environ.get("REDIS_HOST", "localhost"), int(os.environ.get("REDIS_PORT", "6379")), "lan"),
    ],
    "mariadb": [
        ServiceEndpoint("lan", os.environ.get("MARIADB_HOST", "localhost"), int(os.environ.get("MARIADB_PORT", "3306")), "lan"),
        ServiceEndpoint("local", "localhost", int(os.environ.get("MARIADB_LOCAL_PORT", "3306")), "local"),
    ],
    "ssh": [
        ServiceEndpoint("lan", os.environ.get("SSH_HOST", "localhost"), int(os.environ.get("SSH_PORT", "22")), "lan"),
        ServiceEndpoint("local", "localhost", 22, "local"),
    ],
    "adb": [
        ServiceEndpoint("lan", os.environ.get("ADB_HOST", "localhost"), int(os.environ.get("ADB_PORT", "5037")), "lan"),
        ServiceEndpoint("local", "localhost", 5037, "local"),
    ],
    "sala": [
        ServiceEndpoint("local", os.environ.get("SALA_HOST", "127.0.0.1"), int(os.environ.get("SALA_PORT", "8767")), "local"),
    ],
}

REDIS_KEY = os.environ.get("REDIS_KEY", f"memento_panel_items:{detect_project_name()}")

def check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except:
        return False

def redis_cmd(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect((SERVICES["redis"][1].host, SERVICES["redis"][1].port))
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

def get_service_status(name: str) -> List[Dict[str, Any]]:
    return [{"name": ep.name, "host": ep.host, "port": ep.port, "type": ep.type, "ok": check_tcp(ep.host, ep.port)} for ep in SERVICES.get(name, [])]

def get_all_services_status() -> Dict[str, Any]:
    return {name: get_service_status(name) for name in SERVICES}

def get_handoffs_list(limit: int = 20) -> List[Dict[str, Any]]:
    ws = workspace_root()
    handoff_dir = ws / "projects" / ws.name
    handoffs = []
    if not handoff_dir.exists():
        return handoffs
    for path in sorted(handoff_dir.glob("HANDOFF_*.md"), reverse=True)[:limit]:
        try:
            content = path.read_text()
            first_line = content.split('\n')[0] if content else ""
            handoffs.append({"path": str(path.relative_to(ws)), "name": path.stem, "preview": first_line[:80]})
        except:
            pass
    return handoffs

def get_memory_stats():
    ws = workspace_root()
    idx_path = ws / ".memento" / "memory" / "graph" / "memory_index.json"
    if not idx_path.exists():
        idx_path = ws / "memory" / "graph" / "memory_index.json"
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
        ws = workspace_root()
        result = subprocess.run(["git", "-C", str(ws), "status", "--short"], capture_output=True, text=True, timeout=5)
        return {"clean": len(result.stdout.strip()) == 0, "raw": result.stdout.strip()}
    except:
        return {"clean": False, "raw": ""}

def get_sala_stats():
    sala_host = os.environ.get("SALA_HOST", "127.0.0.1")
    sala_port = int(os.environ.get("SALA_PORT", "8767"))
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://{sala_host}:{sala_port}/stats", timeout=2) as resp:
            return json.loads(resp.read().decode())
    except:
        return {"error": "sala no disponible"}

# Base HTML template with integrated navbar
def render_page(content: str, title: str, active: str = "dashboard") -> str:
    nav_items = [("/", "Dashboard"), ("/services", "Servicios"), ("/handoffs", "Handoffs"), ("/config", "Config")]
    nav_html = '<header style="padding:12px 16px;background:#0f1419;border-bottom:1px solid #1f2933"><h1 style="font-size:18px;color:#e5e7eb">🜄 MementoBloom · Panel de Control</h1></header><nav style="padding:8px 16px;background:#0f1419;border-bottom:1px solid #1f2933;display:flex;gap:8px;flex-wrap:wrap">'
    for href, label in nav_items:
        is_active = "active" if href.strip("/") == active else ""
        bg = "#2563eb" if is_active else "#111318"
        color = "#fff" if is_active else "#d4d4d4"
        nav_html += f'<a href="{href}" style="padding:4px 10px;background:{bg};color:{color};border:1px solid #1f2933;border-radius:4px;font-size:12px;text-decoration:none">{label}</a>'
    nav_html += '</nav>'
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#08090a;color:#d4d4d4;min-height:100vh}}
#content{{padding:16px}}
.card{{background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px;margin:8px 0}}
.card h3{{font-size:13px;color:#6b7280;margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em}}
.status-ok{{color:#34d399}}.status-no{{color:#f87171}}
.btn{{padding:4px 8px;background:#2563eb;color:#fff;border:none;border-radius:4px;font-size:11px;cursor:pointer;margin:0 2px}}
.btn:hover{{background:#1d4ed8}}
table{{width:100%;border-collapse:collapse;margin-bottom:8px}}
td{{padding:4px 8px;color:#9ca3af;border-bottom:1px solid #1f2933}}
</style>
</head>
<body>{nav_html}<div id="content">{content}</div></body>
</html>"""

class PanelHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except:
            return {}

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            services = get_all_services_status()
            sala = get_sala_stats()
            mem = get_memory_stats()
            git = get_git_status()
            
            # Dashboard grid con semáforos
            content = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">'
            for svc_name, endpoints in services.items():
                ok_count = sum(1 for e in endpoints if e["ok"])
                total = len(endpoints)
                status_dot = "● OK" if ok_count > 0 else "● Offline"
                status_cls = "status-ok" if ok_count > 0 else "status-no"
                content += f'<div class="card"><h3>{svc_name.upper()}</h3><div style="font-size:16px;color:#e5e7eb;margin-bottom:4px"><span class="{status_cls}">{status_dot}</span></div><div style="font-size:11px;color:#9ca3af">{ok_count}/{total} instancias activas</div></div>'
            
            # Stats cards
            content += f'<div class="card"><h3>Sala</h3><div style="font-size:16px;color:#e5e7eb;margin-bottom:4px"><span class="{"status-ok" if "messages" in sala else "status-no"}">● {"OK" if "messages" in sala else "Offline"}</span></div><div style="font-size:11px;color:#9ca3af">{sala.get("messages",0)} mensajes</div></div>'
            content += f'<div class="card"><h3>Memoria</h3><div style="font-size:16px;color:#e5e7eb;margin-bottom:4px">{mem["entries"]}</div><div style="font-size:11px;color:#9ca3af">HANDOFF={mem["by_type"].get("HANDOFF",0)} | CONTEXT={mem["by_type"].get("CONTEXT",0)}</div></div>'
            content += f'<div class="card"><h3>Git</h3><div style="font-size:16px;color:#e5e7eb;margin-bottom:4px"><span class="{"status-ok" if git["clean"] else "status-no"}">● {"Limpio" if git["clean"] else str(len(git["raw"].splitlines()))+" cambios"}</span></div></div>'
            content += '</div><div style="margin-top:16px"><a href="/services" class="btn">Ver todos los servicios</a></div>'
            
            self._send_html(render_page(content, "Dashboard", "dashboard"))
            
        elif self.path == "/services":
            services = get_all_services_status()
            content = ""
            for svc_name, endpoints in services.items():
                content += f'<div class="card"><h3>{svc_name.upper()}</h3><table>'
                for ep in endpoints:
                    status = "● OK" if ep["ok"] else "● Offline"
                    status_cls = "status-ok" if ep["ok"] else "status-no"
                    content += f"<tr><td>{ep['type']}</td><td><span class='{status_cls}'>{status}</span></td><td>{ep['host']}:{ep['port']}</td>"
                    content += f"<td><button class='btn' onclick='testSvc(\"{svc_name}\",\"{ep['name']}\")'>Test</button>"
                    if not ep["ok"]:
                        content += f"<button class='btn' onclick='startSvc(\"{svc_name}\")'>Start</button>"
                    content += "</td></tr>"
                content += "</table></div>"
            content += '<script>'
            content += 'function testSvc(svc,ep){fetch("/api/service/test",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({service:svc,endpoint:ep})}).then(r=>r.json()).then(d=>alert(d.ok?"OK":"Offline"))}'
            content += 'function startSvc(svc){fetch("/api/service/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({service:svc})}).then(r=>r.json()).then(d=>alert(d.output||d.error))}'
            content += '</script>'
            self._send_html(render_page(content, "Servicios", "services"))
            
        elif self.path == "/handoffs":
            handoffs = get_handoffs_list()
            content = '<h2 style="color:#e5e7eb;margin-bottom:12px">Handoffs recientes</h2>'
            for h in handoffs:
                content += f'<a href="/handoffs/{h["name"]}" style="display:block;color:#60a5fa;text-decoration:none;padding:8px 0;border-bottom:1px solid #1f2933">{h["name"]}</a>'
            self._send_html(render_page(content, "Handoffs", "handoffs"))
            
        elif self.path == "/config":
            config = load_services_config()
            content = '<h2 style="color:#e5e7eb;margin-bottom:12px">Configuración de servicios</h2>'
            content += '<p style="color:#9ca3af;margin-bottom:16px">Edita el archivo <code>config/services.json</code> o usa el API.</p>'
            content += '<form id="svcForm" style="background:#111318;border:1px solid #1f2933;border-radius:8px;padding:16px">'
            content += '<div style="margin-bottom:8px"><label style="color:#d4d4d4;display:block;margin-bottom:4px">Servicio</label>'
            content += '<input name="name" required style="width:100%;padding:8px;background:#0a0c10;color:#e5e7eb;border:1px solid #374151;border-radius:4px">'
            content += '</div>'
            content += '<div style="margin-bottom:8px"><label style="color:#d4d4d4;display:block;margin-bottom:4px">Host</label>'
            content += '<input name="host" required style="width:100%;padding:8px;background:#0a0c10;color:#e5e7eb;border:1px solid #374151;border-radius:4px">'
            content += '</div>'
            content += '<div style="margin-bottom:8px"><label style="color:#d4d4d4;display:block;margin-bottom:4px">Puerto</label>'
            content += '<input name="port" type="number" required style="width:100%;padding:8px;background:#0a0c10;color:#e5e7eb;border:1px solid #374151;border-radius:4px">'
            content += '</div>'
            content += '<div style="margin-bottom:8px"><label style="color:#d4d4d4;display:block;margin-bottom:4px">Tipo</label>'
            content += '<select name="type" style="width:100%;padding:8px;background:#0a0c10;color:#e5e7eb;border:1px solid #374151;border-radius:4px">'
            content += '<option value="local">local</option><option value="lan">lan</option><option value="web">web</option>'
            content += '</select></div>'
            content += '<button type="submit" class="btn">Guardar servicio</button></form>'
            content += '<script>'
            content += 'document.getElementById("svcForm").onsubmit=e=>{e.preventDefault();fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))).then(r=>r.json()).then(d=>alert(d.ok?"Guardado":"Error"))}'
            content += '</script>'
            self._send_html(render_page(content, "Config", "config"))
            
        elif self.path.startswith("/handoffs/HANDOFF_"):
            name = self.path.split("/")[-1]
            ws = workspace_root()
            path = ws / "projects" / ws.name / f"{name}.md"
            if path.exists():
                content = path.read_text().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                self._send_html(render_page(f'<h2 style="color:#e5e7eb;margin-bottom:12px">{name}</h2><pre style="white-space:pre-wrap;word-wrap:break-word">{content}</pre>', name))
            else:
                self._send_json({"error": "handoff no encontrado"}, 404)
                
        elif self.path == "/api/stats":
            self._send_json({
                "services": get_all_services_status(),
                "sala": {"ok": "messages" in get_sala_stats(), "messages": get_sala_stats().get("messages", 0)},
                "memory": get_memory_stats(),
                "git": {"clean": get_git_status().get("clean", False), "changes": len(get_git_status().get("raw", "").splitlines())},
            })
        elif self.path == "/api/services":
            self._send_json(get_all_services_status())
        elif self.path == "/api/handoffs":
            self._send_json(get_handoffs_list())
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
        elif self.path == "/api/config":
            payload = self._read_body()
            svc_name = payload.get("name", "")
            svc_host = payload.get("host", "")
            svc_port = payload.get("port", "")
            svc_type = payload.get("type", "lan")
            
            if svc_name and svc_host and svc_port:
                config = load_services_config()
                if "services" not in config:
                    config["services"] = {}
                config["services"][svc_name] = {
                    "description": f"Added service {svc_name}",
                    "endpoints": [{"name": svc_type, "host": svc_host, "port": int(svc_port), "type": svc_type}]
                }
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                CONFIG_FILE.write_text(json.dumps(config, indent=2))
                self._send_json({"ok": True, "output": f"service {svc_name} added"})
            else:
                self._send_json({"ok": False, "error": "missing fields"})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    port = PANEL_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    else:
        port = find_free_port(port)
    print(f"panel :: http://127.0.0.1:{port}")
    HTTPServer(("0.0.0.0", port), PanelHandler).serve_forever()