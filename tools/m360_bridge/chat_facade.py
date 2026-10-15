"""Facade sala-memento -> chat M360 (TICK-M360-0001 / M360-CHAT-005).

Adapta los productores de la sala memento (optimize_agent, memento_cli,
restore_sala, sala.py) al chat M360 sin que cambien su interfaz: reciben
el payload clásico de la sala ({type, text, source, meta, ...}) y esto lo
traduce a un mensaje M360 en el ROOM del proyecto correspondiente.

Identidad: usuario de servicio bot-memento (creado por seed_memento_chat),
autenticado por token headless en el WebSocket de chat (M360-CHAT-003).
El descubrimiento de rooms usa la API REST con la sesión del bridge.

Cliente WebSocket: stdlib puro (sin dependencia de 'websockets'), suficiente
para envío fire-and-forget de un mensaje por conexión.

Uso:
    from m360_bridge.chat_facade import ChatFacade
    f = ChatFacade.desde_env()          # lee .env
    f.enviar("hola", proyecto="mementobloom", sala="general")
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import M360Client  # noqa: E402

# Tipos de mensaje de la sala memento -> message_type del modelo M360.
# markdown/code/json viajan como 'text' (el render es cliente, igual que
# en la UI sala-memento recreada).
MAPEO_TIPOS = {
    "text": "text",
    "markdown": "text",
    "code": "text",
    "json": "text",
    "system": "system",
    "image": "image",
    "file": "file",
}


class ChatFacade:
    """Publica mensajes de la sala memento en el chat M360."""

    def __init__(self, client: M360Client, bot_token: str, ws_base: str = "ws://127.0.0.1:8000"):
        self.client = client
        self.bot_token = bot_token
        self.ws_base = ws_base.rstrip("/")
        self._cache_rooms: Dict[str, int] = {}

    @classmethod
    def desde_env(cls) -> "ChatFacade":
        base = os.environ.get("M360_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        client = M360Client(base, os.environ["M360_USERNAME"], os.environ["M360_PASSWORD"])
        client._init_session()
        token = os.environ.get("MEMENTO_BOT_TOKEN", "")
        if not token:
            raise RuntimeError("MEMENTO_BOT_TOKEN no definido (requerido para el facade headless)")
        ws = base.replace("https://", "wss://").replace("http://", "ws://")
        return cls(client, token, ws)

    # ---------- descubrimiento de rooms ----------
    def resolver_room(self, proyecto: str, sala: str = "general") -> Optional[int]:
        """ID del ROOM M360 para (proyecto, sala); cachea el resultado.

        La jerarquía sembrada es UNIVERSE memento > WORLD <proyecto> >
        ROOM <sala> (ver seed_memento_chat).
        """
        clave = f"{proyecto}/{sala}"
        if clave in self._cache_rooms:
            return self._cache_rooms[clave]
        r = self.client._get_request("/rooms/api/rooms/")
        rooms = r.get("data", r) if isinstance(r, dict) else r
        rooms = [x for x in (rooms or []) if isinstance(x, dict) and x.get("cell_type") == "ROOM"]
        # 1) match exacto por properties (sembrado), 2) por nombre
        cand = next(
            (x for x in rooms
             if (x.get("properties") or {}).get("proyecto") == proyecto
             and x.get("name") == sala),
            None,
        )
        if cand is None:
            cand = next(
                (x for x in rooms
                 if (x.get("properties") or {}).get("proyecto") == proyecto),
                None,
            )
        if cand is None:
            return None
        self._cache_rooms[clave] = cand.get("id")
        return cand.get("id")

    # ---------- envío ----------
    @staticmethod
    def _handshake_ws(host: str, port: int, path_con_query: str) -> socket.socket:
        """Handshake WebSocket (RFC 6455) mínimo. Devuelve el socket conectado."""
        clave = base64.b64encode(os.urandom(16)).decode()
        solicitud = (
            f"GET {path_con_query} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {clave}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode()
        sock = socket.create_connection((host, port), timeout=15)
        sock.sendall(solicitud)
        respuesta = sock.recv(4096).decode("latin1", errors="replace")
        if "101" not in respuesta.split("\r\n", 1)[0]:
            sock.close()
            raise RuntimeError(f"handshake WS fallido: {respuesta.splitlines()[0][:80] if respuesta else 'sin respuesta'}")
        return sock

    @staticmethod
    def _frame_texto(payload: str) -> bytes:
        """Frame de texto enmascarado cliente->servidor (máscara obligatoria)."""
        datos = payload.encode("utf-8")
        máscara = os.urandom(4)
        longitud = len(datos)
        if longitud < 126:
            cabecera = bytes([0x81, 0x80 | longitud])
        elif longitud < 65536:
            cabecera = bytes([0x81, 0x80 | 126]) + struct.pack(">H", longitud)
        else:
            cabecera = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", longitud)
        enmascarado = bytes(b ^ máscara[i % 4] for i, b in enumerate(datos))
        return cabecera + máscara + enmascarado

    @staticmethod
    def _frame_cierre() -> bytes:
        """Frame de cierre (opcode 0x88) enmascarado."""
        máscara = os.urandom(4)
        return bytes([0x88, 0x80]) + máscara

    def _enviar_ws(self, room_id: int, contenido: str, reply_to: Optional[int] = None) -> Dict[str, Any]:
        """Envía por WebSocket con token headless (identidad bot-memento).

        Cliente WS stdlib (sin dependencias): handshake + un frame de texto
        enmascarado + cierre. Fire-and-forget deliberado: la persistencia la
        confirma el servidor vía el registro del mensaje.
        """
        url = urlparse(f"{self.ws_base}/ws/chat/{room_id}/?token={self.bot_token}")
        host = url.hostname or "127.0.0.1"
        port = url.port or (443 if url.scheme == "wss" else 80)
        path = url.path + ("?" + url.query if url.query else "")
        try:
            sock = self._handshake_ws(host, port, path)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"handshake: {exc}", "room_id": room_id}
        try:
            payload: Dict[str, Any] = {"type": "message", "message": contenido}
            if reply_to:
                payload["reply_to"] = reply_to
            sock.sendall(self._frame_texto(json.dumps(payload)))
            # Leer eventos del servidor brevemente (broadcast/confirmación)
            sock.settimeout(3)
            try:
                sock.recv(4096)
            except (socket.timeout, OSError):
                pass
            sock.sendall(self._frame_cierre())
            return {"ok": True, "room_id": room_id, "via": "ws-stdlib-token"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"envío: {exc}", "room_id": room_id}
        finally:
            try:
                sock.close()
            except OSError:
                pass

    def enviar(
        self,
        texto: str,
        proyecto: str = "mementobloom",
        sala: str = "general",
        tipo: str = "text",
        reply_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Envía un mensaje de la sala al chat M360.

        Devuelve dict con ok/room_id o error estructurado.
        """
        if not (texto or "").strip() and tipo != "system":
            return {"ok": False, "error": "mensaje vacío"}
        room_id = self.resolver_room(proyecto, sala)
        if not room_id:
            return {"ok": False, "error": f"sin room para {proyecto}/{sala}", "suggestion": "Ejecutar seed_memento_chat o crear el ROOM."}
        contenido = texto if tipo != "system" else (texto or "·")
        return self._enviar_ws(room_id, contenido, reply_to)

    def enviar_batch(self, items: List[Dict[str, Any]], proyecto: str = "mementobloom", sala: str = "general") -> List[Dict[str, Any]]:
        """Envía varios mensajes (equivalente a /send-batch de la sala)."""
        return [self.enviar(it.get("text", ""), proyecto, sala, it.get("tipo", "text")) for it in items]


if __name__ == "__main__":
    f = ChatFacade.desde_env()
    r = f.enviar("prueba facade sala->M360 (M360-CHAT-005)", proyecto="mementobloom", sala="bridge-m360")
    print(json.dumps(r, ensure_ascii=False))
