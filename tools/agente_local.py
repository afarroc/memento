from flask import Flask, jsonify, request
from flask_cors import CORS
from tkinter import Tk, filedialog
from pathlib import Path
import hmac
import os
import platform
import subprocess
import threading

def load_dotenv(path: Path):
    """Loader mínimo de .env sin dependencias externas."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

# .env configurable por variable de entorno; por defecto el .env del repo memento.
_env_default = Path(__file__).resolve().parent.parent / ".env"
_env_override = os.environ.get("AGENT_LOCAL_ENV")
for _env_path in ([Path(_env_override)] if _env_override else []) + [_env_default]:
    load_dotenv(_env_path)

app = Flask(__name__)
# Orígenes locales permitidos para desarrollo; no exponer a red externa.
_DEFAULT_ORIGINS = [
    os.environ.get("AGENT_ORIGIN", "http://127.0.0.1:8000"),
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS(app, origins=_DEFAULT_ORIGINS, supports_credentials=True)

token = os.environ.get("AGENT_LOCAL_TOKEN")
if not token:
    raise RuntimeError(
        "AGENT_LOCAL_TOKEN no está definido en .env. "
        "Definilo en /Volumes/Macintosh HD - Datos/projects/Management360/.env "
        "o en mementobloom/.env."
    )
print("AGENT_LOCAL_TOKEN cargado:", bool(token))

# Tk solo como fallback; en macOS usamos osascript para evitar fallos de WindowServer.
try:
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
except Exception:
    root = None

@app.route("/ping")
def ping():
    return jsonify({"ok": True})

# Serializa el diálogo nativo: un solo osascript a la vez.
# Evita N procesos bloqueados con clientes concurrentes.
_dialog_lock = threading.Lock()

def _choose_folder_macos():
    script = 'POSIX path of (choose folder)'
    with _dialog_lock:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None

def _choose_folder_tk():
    if root is None:
        raise RuntimeError("tkinter root no disponible")
    ruta = filedialog.askdirectory(title="Selecciona una carpeta")
    return ruta or None

@app.route("/seleccionar-carpeta")
def seleccionar_carpeta():
    client_token = request.headers.get("X-Agent-Token")
    if not client_token or not hmac.compare_digest(client_token, token):
        return jsonify({"error": "Unauthorized"}), 401
    if os.environ.get("AGENT_TEST_MODE") == "1":
        ruta_test = Path(os.environ.get("AGENT_TEST_FOLDER", "/tmp/test-folder"))
        if not ruta_test.is_dir():
            return jsonify({"error": f"test_folder_no_existe: {ruta_test}", "test_mode": True}), 500
        return jsonify({"ruta": str(ruta_test), "test_mode": True})

    last_error = None
    if platform.system() == "Darwin":
        try:
            ruta = _choose_folder_macos()
            if ruta:
                return jsonify({"ruta": ruta})
        except Exception as exc:
            last_error = exc

    try:
        ruta = _choose_folder_tk()
        return jsonify({"ruta": ruta})
    except Exception as exc:
        app.logger.error("filedialog_failed: %s", exc)
        return jsonify({"error": "filedialog_failed"}), 500

# Respaldo explícito de CORS por origen local, por si flask-cors no lo adjunta.
@app.after_request
def _add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in _DEFAULT_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT, PATCH")
        response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Agent-Token")
        response.headers.setdefault("Vary", "Origin")
    return response

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)
