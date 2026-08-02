#!/usr/bin/env python3
"""Restaura mensajes desde <body>.html a Redis."""

import json
import re
import socket
import os
from pathlib import Path

from core.paths import detect_project_name

BODY_HTML = Path(__file__).resolve().parent.parent / "<body>.html"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_KEY = os.environ.get("REDIS_KEY", f"memento_panel_items:{detect_project_name()}")

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for raw_line in _env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def redis_cmd(args, host=None, port=None):
    if host is None:
        host = REDIS_HOST
    if port is None:
        port = REDIS_PORT
    redis_password = os.environ.get("REDIS_PASSWORD")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((host, port))
    if redis_password:
        s.sendall(f"*2\r\n$4\r\nAUTH\r\n${len(redis_password)}\r\n{redis_password}\r\n".encode("utf-8"))
        auth_resp = s.recv(128).decode(errors="replace")
        if not auth_resp.startswith("+OK"):
            s.close()
            return "AUTH failed"
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
    return received.decode(errors="replace")


def redis_push(msg_json):
    try:
        redis_cmd(["RPUSH", REDIS_KEY, msg_json])
        return True
    except Exception as e:
        print(f"Error enviando a Redis: {e}")
        return False


def normalize_text(text):
    if not text:
        return ""
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_body_html(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Estructura real: <div class="msg assistant text" style="...">
    # Regex para dividir bloques por </div><div class="msg
    msg_pattern = re.compile(
        r'<div\s+class="msg\s+([^"]+)"[^>]*>([\s\S]*?)</div>(?=\s*<div\s+class="msg|$)',
    )

    messages = []
    for idx, match in enumerate(msg_pattern.finditer(content)):
        classes = match.group(1)
        inner = match.group(2)

        class_list = classes.split()
        if "client" in class_list:
            source = "client"
        elif "assistant" in class_list:
            source = "assistant"
        else:
            source = "unknown"

        msg_type = next((p for p in class_list if p in {"text", "system", "markdown", "html", "json", "code", "file", "image"}), "text")

        # Tiempo: <span class="time">12:37</span>
        tm = re.search(r'<span\s+class="time">([^<]+)</span>', inner)
        created_at = tm.group(1).strip() if tm else "00:00"

        # Reply: data-reply-text="..."
        reply_id = None
        reply_text = ""
        reply_source = source
        rid = re.search(r'data-reply-id="([^"]+)"', inner)
        rtext = re.search(r'data-reply-text="([^"]*)"', inner)
        rsrc = re.search(r'data-reply-source="([^"]+)"', inner)
        if rid:
            reply_id = rid.group(1)
        if rtext:
            reply_text = rtext.group(1)
        if rsrc:
            reply_source = rsrc.group(1)

        reply_to = None
        if reply_id:
            reply_to = {"id": reply_id, "text": reply_text, "source": reply_source}

        # Files: <a href="/uploads/...">name</a>
        files = []
        for m in re.finditer(r'<a\s+href="(/uploads/[^"]+)"[^>]*>([^<]+)</a>', inner):
            files.append({"name": m.group(2), "url": m.group(1), "size": "0"})

        # Contenido: <div class="content">...</div> o <div class="content"><strong>...</strong></div>
        built_text = ""
        content_match = re.search(r'<div\s+class="content">(.*?)</div>', inner, re.DOTALL)
        if content_match:
            built_text = content_match.group(1).strip()

        # Quitar HTML tags y strong de system
        built_text = re.sub(r'<strong>(.*?)</strong>', r'\1', built_text)
        built_text = normalize_text(built_text)

        # Estilo
        style = {}
        if msg_type == "markdown":
            style = {"bg": "#101827", "border": "#60a5fa", "color": "#e0f2fe", "badgeBg": "#0f172a", "badgeColor": "#bfdbfe"}
        elif msg_type == "system":
            style = {"bg": "#0b1d2e", "border": "#1f4f7a", "color": "#dcecff", "badgeBg": "#102a43"}
        elif msg_type == "html":
            style = {"bg": "#0f1524", "border": "#1e3a8a", "color": "#93c5fd", "badgeBg": "#0f1524"}
        elif msg_type == "code":
            style = {"bg": "#0e1b16", "border": "#14532d", "color": "#6ee7b7", "badgeBg": "#0e1b16"}
        elif msg_type == "json":
            style = {"bg": "#230f0f", "border": "#7f1d1d", "color": "#fca5a5", "badgeBg": "#230f0f"}
        elif source == "client":
            style = {"bg": "#0b2f22", "border": "#34d399", "color": "#dcfce7", "badgeBg": "#0b2f22"}
        else:
            style = {"bg": "#101827", "border": "#60a5fa", "color": "#e0f2fe", "badgeBg": "#0f172a"}

        message = {
            "id": reply_id or f"restored_{idx}",
            "created_at": created_at,
            "type": msg_type,
            "text": built_text,
            "style": style,
            "meta": {
                "source": source,
                "origin": "restore",
            },
        }
        if reply_to:
            message["reply_to"] = reply_to
        if files:
            message["meta"]["files"] = files

        # Solo agregar mensajes con contenido significativo
        if built_text.strip() or files:
            messages.append(message)

    return messages


def main():
    print("=== Restauración de sala desde <body>.html ===")
    print(f"Archivo fuente: {BODY_HTML}")

    try:
        pong = redis_cmd(["PING"])
        if "PONG" in pong:
            print(f"Redis conectado: {REDIS_HOST}:{REDIS_PORT}")
        else:
            print(f"Redis respondió sin PONG: {pong}")
            return
    except Exception as e:
        print(f"No se pudo conectar a Redis: {e}")
        return

    print("Parseando <body>.html...")
    messages = parse_body_html(BODY_HTML)
    print(f"Mensajes extraídos: {len(messages)}")

    if not messages:
        print("No se encontraron mensajes.")
        return

    for i, msg in enumerate(messages[:10]):
        text_preview = (msg.get("text") or "")[:70].replace("\n", " ")
        print(f"  {i}: [{msg.get('type')}] {text_preview}...")

    print("Restaurando mensajes en Redis...")
    ok = fail = 0
    for msg in messages:
        if redis_push(json.dumps(msg, ensure_ascii=False)):
            ok += 1
        else:
            fail += 1

    print(f"Restaurados: {ok} | Fallos: {fail}")
    try:
        count = redis_cmd(["LLEN", REDIS_KEY])
        print(f"Total en cola Redis ({REDIS_KEY}): {count.strip()}")
    except Exception:
        pass

    print("Listo. Refresca http://127.0.0.1:8767")


if __name__ == "__main__":
    main()