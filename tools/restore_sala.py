#!/usr/bin/env python3
"""Restaura mensajes desde <body>.html a Redis."""

import json
import re
import socket
import os
from pathlib import Path

BODY_HTML = Path(__file__).resolve().parent.parent / "<body>.html"
REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.18.59")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_KEY = os.environ.get("REDIS_KEY", "memento_panel_items")


def redis_cmd(args):
    redis_host = os.environ.get("REDIS_HOST", "192.168.18.59")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((REDIS_HOST, REDIS_PORT))
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
    """Normaliza texto eliminando HTMLrips comunes pero conservando estructura."""
    if not text:
        return ""
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Remover etiquetas HTML pero conservar contenido
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_body_html(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex: detectar cada mensaje por su div inicial y capturar hasta el </div> de cierre del bloque
    msg_pattern = re.compile(
        r'<div class="msg ([^"]+)"(.*?)>(.*?)</div>(?=\s*<div class="msg\b|$)',
        re.DOTALL,
    )

    messages = []
    for idx, match in enumerate(msg_pattern.finditer(content)):
        classes = match.group(1)
        attrs = match.group(2)
        inner = match.group(3)

        if "client" in classes.split():
            source = "client"
        elif "assistant" in classes.split():
            source = "assistant"
        else:
            source = "unknown"

        parts = classes.split()
        msg_type = next((p for p in parts if p in {"text", "system", "markdown", "html", "json", "code", "file", "image"}), "text")

        # Tiempo
        tm = re.search(r'<span class="time">([^<]+)</span>', inner)
        created_at = tm.group(1).strip() if tm else "00:00"

        # Reply button data
        reply_id = reply_text = reply_source = ""
        rid = re.search(r'data-reply-id="([^"]+)"', attrs)
        rtext = re.search(r'data-reply-text="(.+?)"(?:\s+data-reply-source=)', attrs)
        rsrc = re.search(r'data-reply-source="([^"]+)"', attrs)
        if rid:
            reply_id = rid.group(1)
        if rtext:
            reply_text = rtext.group(1)
        if rsrc:
            reply_source = rsrc.group(1)

        reply_to = None
        if reply_id:
            reply_to = {"id": reply_id, "text": reply_text or "", "source": reply_source or source}

        # Archivos adjuntos desde chips
        files = []
        for href, name, size in re.findall(
            r'<div class="chip"><a href="(/uploads/[^"]+)"\s+target="_blank"[^>]*>([^<]+)</a><span[^>]*>([^<]+)</span></div>',
            inner,
        ):
            files.append({"name": name, "size": size.replace("B", ""), "url": href})

        # EXTRACCIÓN DE CONTENIDO RENDERIZADO
        built_text = ""

        if msg_type == "html":
            # Extraer contenido html-content si existe
            html_content_m = re.search(r'<div class="content html-content">(.*)', inner, re.DOTALL)
            if html_content_m:
                built_text = html_content_m.group(1).strip()
            else:
                # Extraer todo el contenido del div
                content_m = re.search(r'<div class="content">(.*?)</div>', inner, re.DOTALL)
                if content_m:
                    built_text = content_m.group(1).strip()

        elif msg_type == "markdown":
            # Extraer desde env-block renderizado + content
            env_text = ""
            env_m = re.search(r'<div class="env-block">.*?<div class="content">(.*?)</div>\s*</div>', inner, re.DOTALL)
            if env_m:
                env_text = env_m.group(1).strip()

            content_m = re.search(r'<div class="content">(.*?)</div>\s*<div class="meta-line">', inner, re.DOTALL)
            if content_m:
                content_text = content_m.group(1).strip()
            else:
                # Buscar último content antes de meta-line
                content_m = re.findall(r'<div class="content">(.*?)</div>', inner, re.DOTALL)
                content_text = content_m[-1].strip() if content_m else ""

            if env_text:
                built_text = f"<environment_details>\n{env_text}\n</environment_details>\n\n{content_text}"
            else:
                built_text = content_text

        elif msg_type == "system":
            # Extraer texto fuerte dentro de content
            content_m = re.search(r'<div class="content"><strong>(.*?)</strong></div>', inner, re.DOTALL)
            if content_m:
                built_text = content_m.group(1).strip()
            else:
                content_m = re.search(r'<div class="content">(.*?)</div>', inner, re.DOTALL)
                if content_m:
                    built_text = content_m.group(1).strip()

        elif msg_type == "file":
            # Texto del mensaje + metadata de archivos
            content_m = re.search(r'<div class="content">(.*?)</div>', inner, re.DOTALL)
            if content_m:
                built_text = content_m.group(1).strip()

        else:  # text, code, json, image
            content_m = re.search(r'<div class="content">(.*?)</div>', inner, re.DOTALL)
            if content_m:
                built_text = content_m.group(1).strip()

        # Limpiar HTML del texto extraído
        built_text = normalize_text(built_text)

        # Quitar línea "source: ..." que viene del meta-line
        built_text = re.sub(r'\nsource:\s*(client|assistant|api)\s*·\s*origin:\s*\w+\s*$', '', built_text).strip()

        # Estilo por defecto según tipo
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
            "reply_to": reply_to,
            "meta": {
                "files": files if files else [],
                "source": source,
                "origin": "restore",
            },
        }

        # Limpiar campos vacíos
        for key in ("style", "reply_to", "html"):
            if not message.get(key):
                message.pop(key, None)
        if not files:
            message["meta"].pop("files", None)
        if not message["text"]:
            message["text"] = ""

        messages.append(message)

    return messages


def main():
    print("=== Restauración de sala desde <body>.html ===")
    print(f"Archivo fuente: {BODY_HTML}")

    # Verificar Redis
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

    # Parsear
    print("Parseando <body>.html...")
    messages = parse_body_html(BODY_HTML)
    print(f"Mensajes extraídos: {len(messages)}")

    if not messages:
        print("No se encontraron mensajes.")
        return

    # Preview
    for i, msg in enumerate(messages[:10]):
        text_preview = (msg.get("text") or "")[:70].replace("\n", " ")
        print(f"  {i}: [{msg.get('type')}] {text_preview}...")

    # Restaurar (sin flush para no borrar historial existente)
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
