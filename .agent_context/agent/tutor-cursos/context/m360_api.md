# context/m360_api.md — Mapeo a tools/m360_bridge/client.py

Cliente: `tools/m360_bridge/client.py` (carga credenciales y API key desde `.env` de Management360).

## Métodos relevantes para el tutor
| Acción | Método en client.py |
|--------|---------------------|
| Listar cursos | `api_v1_list_courses(**params)` |
| Crear curso | `api_v1_create_course(title, project_id=0, **kwargs)` |
| Actualizar curso | `api_v1_update_course(course_id, **kwargs)` |
| Borrar curso | `api_v1_delete_course(course_id)` |
| Listar categorías | `api_v1_list_course_categories(**params)` |
| Crear categoría | `api_v1_create_course_category(name, **kwargs)` |
| Listar tareas/proyectos | `api_v1_list_tasks`, `api_v1_list_projects` |

## Base URL y auth
- `M360_BASE_URL` (por defecto `http://127.0.0.1:8000`).
- Lectura (GET): abierta. Escritura: `Authorization: Bearer <M360_API_KEY>` (del `.env`).
- Para módulos/lecciones no hay endpoint v1 dedicado en el bridge → usar SQL directo o `requests` a la API interna de M360 si existe.

## Ejemplo
```python
from tools.m360_bridge import client
c = client.M360BridgeClient()
course = c.api_v1_create_course(title="UPN Comunicación 1", slug="upn-comunicacion-1", is_published=True)
print(course["id"])
```
