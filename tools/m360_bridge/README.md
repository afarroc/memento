# M360 Bridge — diagnóstico y uso

## Diagnóstico: `python3 tools/m360_bridge/client.py task show 385` no produce salida

**Causa raíz:** `tools/m360_bridge/client.py` define la clase `M360Client`, pero **no expone una CLI**.  
Por lo tanto, invocarlo como `python3 tools/m360_bridge/client.py task show ...` ejecuta el módulo sin parser ni `if __name__ == "__main__":`, y el proceso termina sin imprimir nada.

**Estado del servidor M360 confirmado:**
- Health: `http://127.0.0.1:8000/api/v1/health/` → `{"status":"ok"}`
- CSRF: `http://127.0.0.1:8000/api/csrf/` → `200` + token
- Credenciales en `.env` cargadas correctamente

## Forma correcta de usar el bridge

Desde código Python:
```python
from tools.m360_bridge.client import M360Client

client = M360Client(
    base_url="http://127.0.0.1:8000",
    username="su",
    password="...",
)
resp = client.api_v1_get_task(385)
print(resp)
```

Si necesitás una CLI rápida, usá `python3 tools/m360_bridge/sync.py` o creá un script ad-hoc; no modifiques `client.py` para agregar argparse sin ticket explícito, porque ese archivo es la base compartida del bridge.

## Nota para no repetir este error

- `client.py` = librería/base del bridge.
- `sync.py` = sincronizador de sprints.
- Si el objetivo es “leer/ver tareas desde CLI”, el acceso debe hacerse por lectura directa del estado local o por un script específico; no por `client.py` como si fuera CLI.
