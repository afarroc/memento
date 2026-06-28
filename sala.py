#!/usr/bin/env python3
"""MementoBloom :: Sala Panel Server v2 — solo Redis, sin disco."""

import json
import time
import socket
import os
import re
import mimetypes
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, quote

from core.paths import detect_project_name

HTML = Path(__file__).parent / "templates" / "sala.html"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_KEY = os.environ.get("REDIS_KEY", f"memento_panel_items:{detect_project_name()}")
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
MAX_UPLOAD_SIZE = int(os.environ.get("MEMENTO_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
redis_ok = False

STYLE_PRESETS = {
    "info": {"bg": "#0b1d2e", "border": "#1f4f7a", "color": "#dcecff", "badgeBg": "#102a43"},
    "success": {"bg": "#0b261b", "border": "#1f8a5b", "color": "#dcfce7", "badgeBg": "#0f2f22"},
    "warn": {"bg": "#2a280b", "border": "#7a6a1f", "color": "#fff7cc", "badgeBg": "#2f2a0b"},
    "error": {"bg": "#2a0b0b", "border": "#7a1f1f", "color": "#ffe4e6", "badgeBg": "#2f0b0b"},
    "agent_optimizer": {"bg": "#101827", "border": "#60a5fa", "color": "#e0f2fe", "badgeBg": "#0f172a"},
    "bootstrap": {"bg": "#171325", "border": "#a78bfa", "color": "#f3e8ff", "badgeBg": "#21143a"},
    "memory": {"bg": "#0f1d18", "border": "#34d399", "color": "#dcfce7", "badgeBg": "#0b2f22"},
    "git": {"bg": "#1d160f", "border": "#f59e0b", "color": "#fef3c7", "badgeBg": "#2f220b"},
    "service": {"bg": "#0b1d2e", "border": "#38bdf8", "color": "#e0f2fe", "badgeBg": "#0f2a43"},
    "code": {"bg": "#0e1b16", "border": "#14532d", "color": "#d1fae5", "badgeBg": "#0b2f22"},
    "json": {"bg": "#230f0f", "border": "#7f1d1d", "color": "#fee2e2", "badgeBg": "#2f0b0b"},
}


def normalize_style(payload):
    style = payload.get("style")
    if isinstance(style, dict) and style:
        return style
    key = payload.get("tone") or payload.get("level") or payload.get("type") or "info"
    if key == "ok":
        key = "success"
    return dict(STYLE_PRESETS.get(key, STYLE_PRESETS["info"]))


def redis_cmd(args):
    try:
        import os
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((redis_host, redis_port))
        chunks = [f"*{len(args)}\r\n".encode("utf-8")]
        for arg in args:
            encoded = str(arg).encode("utf-8")
            chunks.append(f"${len(encoded)}\r\n".encode("utf-8"))
            chunks.append(encoded)
            chunks.append(b"\r\n")
        s.sendall(b"".join(chunks))

        received = bytearray(s.recv(65536))
        while received and not received.endswith(b"\r\n"):
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            received.extend(chunk)

        s.close()
        return {"ok": True, "out": received.decode(errors="replace")}
    except Exception as e:
        return {"ok": False, "out": str(e)}


def extract_json_objects(data):
    items = []
    i = 0
    n = len(data)
    while i < n:
        if data[i] != ord("{"):
            i += 1
            continue

        start = i
        depth = 0
        in_string = False
        escape = False
        j = start
        while j < n:
            c = data[j]
            if in_string:
                if escape:
                    escape = False
                elif c == ord("\\"):
                    escape = True
                elif c == ord('"'):
                    in_string = False
            else:
                if c == ord('"'):
                    in_string = True
                elif c == ord("{"):
                    depth += 1
                elif c == ord("}"):
                    depth -= 1
                    if depth == 0:
                        try:
                            items.append(json.loads(data[start:j + 1].decode("utf-8", errors="replace")))
                        except Exception:
                            pass
                        i = j + 1
                        break
            j += 1
        else:
            break
    return items


def redis_init():
    flush_on_start = os.environ.get("MEMENTO_SALA_FLUSH_ON_START", "").lower() in {"1", "true", "yes"}
    if not flush_on_start:
        return
    try:
        redis_cmd(["FLUSHALL"])
    except Exception:
        pass


def safe_filename(name: str) -> str:
    name = Path(name or "upload").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name or "upload"


def parse_multipart_upload(body: bytes, content_type: str) -> dict:
    match = re.search(r"boundary=(?:\"([^\"]+)\"|([^;]+))", content_type or "")
    if not match:
        return {"ok": False, "error": "multipart boundary not found"}
    boundary = (match.group(1) or match.group(2)).encode("utf-8")
    marker = b"--" + boundary
    files = []
    for raw_part in body.split(marker)[1:]:
        if raw_part in {b"--\r\n", b"--", b"--\r\n--\r\n", b"--\r\n--"}:
            continue
        if raw_part.startswith(b"--"):
            raw_part = raw_part[2:]
        if raw_part.endswith(b"\r\n"):
            raw_part = raw_part[:-2]
        if b"\r\n\r\n" not in raw_part:
            continue
        headers_blob, content = raw_part.split(b"\r\n\r\n", 1)
        headers = headers_blob.decode("utf-8", errors="replace")
        disp = ""
        ctype = ""
        for line in headers.split("\r\n"):
            lower = line.lower()
            if lower.startswith("content-disposition:"):
                disp = line
            elif lower.startswith("content-type:"):
                ctype = line.split(":", 1)[1].strip()
        filename_match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";\r\n]+)"?', disp, flags=re.I)
        if not filename_match:
            continue
        original_name = unquote(filename_match.group(1).strip())
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stored_name = f"{stamp}_{safe_filename(original_name)}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target = (UPLOAD_DIR / stored_name).resolve()
        if not str(target).startswith(str(UPLOAD_DIR.resolve())):
            continue
        target.write_bytes(content)
        files.append({
            "name": original_name,
            "size": len(content),
            "mime": ctype or mimetypes.guess_type(original_name)[0] or "application/octet-stream",
            "url": f"/uploads/{quote(stored_name)}",
            "stored_name": stored_name,
        })
    return {"ok": True, "files": files}


def serve_upload(path: str):
    name = unquote(path.replace("/uploads/", "", 1))
    target = (UPLOAD_DIR / safe_filename(name)).resolve()
    if not str(target).startswith(str(UPLOAD_DIR.resolve())) or not target.exists():
        return None, 404, None
    content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    return target.read_bytes(), 200, content_type


def get_msgs():
    if not redis_ok:
        return []
    r = redis_cmd(["lrange", os.environ.get("REDIS_KEY", "memento_panel_items"), "0", "-1"])
    if not r.get("ok"):
        return []
    items = extract_json_objects(r["out"].encode("utf-8"))
    return sorted(items, key=lambda x: x.get("id", "0"))


class H(BaseHTTPRequestHandler):
    def _send_response(self, payload, content_type="application/json", status=200):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0, proxy-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except BrokenPipeError:
            return

    def _send_json(self, data, status=200):
        self._send_response(json.dumps(data, ensure_ascii=False, indent=2), "application/json", status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return {}

    def _read_raw_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return b""
        return self.rfile.read(length)

    def _handle_system(self, payload):
        level = payload.get("level", "info")
        style = normalize_style(payload)
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        metadata = {
            "session": payload.get("session"),
            "source": source,
            "project": payload.get("project"),
            "tags": payload.get("tags", []),
            "latency_ms": payload.get("latency_ms"),
            "server": payload.get("server"),
            "io": payload.get("io"),
        }
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": payload.get("type", "system") or "system",
            "level": level,
            "text": payload.get("text") or payload.get("message") or payload.get("title") or "",
            "html": payload.get("html"),
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "files": payload.get("files", []),
                "payload": payload.get("payload"),
                "source": payload.get("source"),
                "origin": payload.get("origin"),
                "tokens": payload.get("tokens"),
                "model": payload.get("model"),
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
                "stats": metadata,
            },
            "style": style,
        }

    def _handle_text(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        files = [f for f in (payload.get("files") or []) if isinstance(f, dict)]
        file_meta = files[0] if files else None
        text = payload.get("text")
        if text is None and file_meta:
            text = file_meta.get("name", "")
        meta = {
            "files": files,
            "payload": payload.get("payload"),
            "source": source,
            "origin": origin,
            "tokens": payload.get("tokens"),
            "model": payload.get("model"),
            "request_id": payload.get("request_id"),
            "trace_id": payload.get("trace_id"),
        }
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": "text",
            "text": text or "",
            "html": payload.get("html"),
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": meta,
            "style": normalize_style(payload),
        }

    def _handle_html(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        html = payload.get("html") or payload.get("text") or ""
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": "html",
            "text": payload.get("text", ""),
            "html": html,
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "files": [f for f in (payload.get("files") or []) if isinstance(f, dict)],
                "payload": payload.get("payload"),
                "source": source,
                "origin": origin,
                "tokens": payload.get("tokens"),
                "model": payload.get("model"),
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
                "rendered": True,
            },
            "style": normalize_style(payload),
        }

    def _handle_code(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": "code",
            "text": payload.get("text", ""),
            "code": payload.get("code", ""),
            "language": payload.get("language", "text"),
            "html": payload.get("html"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "files": [f for f in (payload.get("files") or []) if isinstance(f, dict)],
                "payload": payload.get("payload"),
                "source": source,
                "origin": origin,
                "output": payload.get("output"),
                "error": payload.get("error"),
                "tokens": payload.get("tokens"),
                "model": payload.get("model"),
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
            },
            "style": normalize_style(payload),
        }


    def _handle_markdown(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": "markdown",
            "text": payload.get("text", ""),
            "html": payload.get("html"),
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "files": [f for f in (payload.get("files") or []) if isinstance(f, dict)],
                "payload": payload.get("payload"),
                "source": source,
                "origin": origin,
                "tokens": payload.get("tokens"),
                "model": payload.get("model"),
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
                "rendered": bool(payload.get("html")),
            },
            "style": normalize_style(payload),
        }

    def _handle_json(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": "json",
            "text": payload.get("text", ""),
            "html": payload.get("html"),
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "payload": payload.get("payload"),
                "source": source,
                "origin": origin,
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
            },
        }

    def _handle_file(self, payload):
        source = payload.get("source") or "assistant"
        origin = payload.get("origin") or "api"
        files = [f for f in (payload.get("files") or []) if isinstance(f, dict)]
        file_meta = None
        if payload.get("file") and isinstance(payload["file"], dict):
            file_meta = {
                "name": payload["file"].get("name"),
                "size": payload["file"].get("size"),
                "mime": payload["file"].get("mime", "application/octet-stream"),
                "ext": payload["file"].get("ext", ""),
                "url": payload["file"].get("url", ""),
            }
        if not file_meta and files:
            file_meta = files[0]
        return {
            "id": str(int(time.time() * 1000)),
            "created_at": time.strftime("%H:%M"),
            "type": payload.get("type", "file") or "file",
            "text": payload.get("text", file_meta.get("name", "") if file_meta else ""),
            "html": payload.get("html"),
            "code": payload.get("code"),
            "language": payload.get("language"),
            "pixels": payload.get("pixels", []),
            "reply_to": payload.get("reply_to"),
            "meta": {
                "files": files if files else ([file_meta] if file_meta else []),
                "payload": payload.get("payload"),
                "source": source,
                "origin": origin,
                "request_id": payload.get("request_id"),
                "trace_id": payload.get("trace_id"),
            },
        }

    def do_GET(self):
        if self.path == "/":
            self._send_response(HTML.read_bytes(), "text/html")
        elif self.path == "/messages":
            self._send_json({"messages": get_msgs()})
        elif self.path == "/stats":
            self._send_json({"messages": len(get_msgs())})
        elif self.path.startswith("/uploads/"):
            data, status, content_type = serve_upload(self.path)
            if status == 200:
                self._send_response(data, content_type or "application/octet-stream")
            else:
                self._send_json({"error": "not found"}, 404)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/upload":
            content_type = self.headers.get("Content-Type", "")
            body = self._read_raw_body()
            if len(body) > MAX_UPLOAD_SIZE:
                self._send_json({"ok": False, "error": f"file too large; max {MAX_UPLOAD_SIZE} bytes"}, 413)
                return
            result = parse_multipart_upload(body, content_type)
            self._send_json(result)
            return

        if self.path == "/send":
            payload = self._read_body()
            msg_type = payload.get("type", "text") or "text"
            if msg_type == "system":
                msg = self._handle_system(payload)
            elif msg_type == "json":
                msg = self._handle_json(payload)
            elif msg_type == "code":
                msg = self._handle_code(payload)
            elif msg_type == "markdown":
                msg = self._handle_markdown(payload)
            elif msg_type == "html":
                msg = self._handle_html(payload)
            elif msg_type == "file":
                msg = self._handle_file(payload)
            elif msg_type == "image":
                msg = self._handle_file({**payload, "type": "image"})
                msg["meta"]["files"] = msg["meta"].get("files") or []
                if msg["meta"]["files"]:
                    msg["pixels"] = [msg["meta"]["files"][0].get("url", "")]
                else:
                    msg["pixels"] = []
            else:
                msg = self._handle_text(payload)
            if redis_ok:
                redis_cmd(["rpush", os.environ.get("REDIS_KEY", "memento_panel_items"), json.dumps(msg, ensure_ascii=False)])
            self._send_json({"ok": True, "message": msg})
            return

        if self.path == "/send-batch":
            payload = self._read_body()
            items = payload.get("items") or []
            out = []
            for item in items:
                msg_type = item.get("type", "text") or "text"
                if msg_type == "system":
                    msg = self._handle_system(item)
                elif msg_type == "json":
                    msg = self._handle_json(item)
                elif msg_type == "code":
                    msg = self._handle_code(item)
                elif msg_type == "markdown":
                    msg = self._handle_markdown(item)
                elif msg_type == "html":
                    msg = self._handle_html(item)
                elif msg_type == "file":
                    msg = self._handle_file(item)
                elif msg_type == "image":
                    msg = self._handle_file({**item, "type": "image"})
                    msg["meta"]["files"] = msg["meta"].get("files") or []
                    if msg["meta"]["files"]:
                        msg["pixels"] = [msg["meta"]["files"][0].get("url", "")]
                    else:
                        msg["pixels"] = []
                else:
                    msg = self._handle_text(item)
                out.append(msg)
                if redis_ok:
                    redis_cmd(["rpush", os.environ.get("REDIS_KEY", "memento_panel_items"), json.dumps(msg, ensure_ascii=False)])
            self._send_json({"ok": True, "messages": out})
            return

        self._send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self._send_json({}, 204)

    def log_message(self, *args, **kwargs):
        return None


if __name__ == "__main__":
    from core.services import find_free_port
    redis_init()
    try:
        pong = redis_cmd(["PING"])
        redis_ok = pong.get("ok") and isinstance(pong.get("out"), str) and "PONG" in pong["out"]
    except Exception:
        redis_ok = False
    sala_port = find_free_port(8767)
    print(f"sala v2-redis :: http://localhost:{sala_port} | redis={'ok' if redis_ok else 'offline'}")
    HTTPServer(("0.0.0.0", sala_port), H).serve_forever()
