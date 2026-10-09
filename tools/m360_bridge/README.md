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

## Creación de cursos, módulos y lecciones

```python
from tools.m360_bridge.client import M360Client

client = M360Client(
    base_url="http://127.0.0.1:8000",
    username="su",
    password="...",
)

# Curso base
client.api_v1_create_course(
    title="Comunicación 1",
    project_id=27,
    career_id=1,
    cycle_id=1,
    category_id=1,
    level="beginner",
    price=0,
    duration_hours=80,
    is_published=False,
    is_featured=False,
    tutor_id=2,
    description="Curso de Comunicación 1 para Administración.",
    short_description="Texto académico expositivo.",
    codigo="COM-201",
    creditos=5,
    ht=4,
    hp=2,
    hl=0,
    pc=0,
    requisitos="Ninguno",
    naturaleza="teorico-practico",
    competencia_general="Pensamiento creativo y crítico...",
    componentes="",
    sumilla="Curso teórico-práctico...",
    logro_curso="Producir un texto académico expositivo.",
    sistema_evaluacion="T1 15%, T2 15%, T3 15%, T4 15%, Final 40%, Sustitutoria semana 17.",
    bibliografia="Úcar, P. y Olalla, A. (2013). Español escrito: idea y redacción.",
)

# Módulo/unidad
client.api_v1_create_module(
    course_id=10,
    title="Unidad I: Estrategia de comprensión de lectura",
    description="Al finalizar la unidad...",
    order=1,
    logro_unidad="Procesa información adecuatamente...",
)

# Lección/semana
client.api_v1_create_lesson(
    module_id=39,
    title="Semana 1: Introducción a los cursos virtuales",
    lesson_type="text",
    order=1,
    duration_minutes=60,
    is_free=False,
    content="Contenido...",
    logro_semana="...",
    saberes_esenciales="...",
    actividades="...",
    trabajo_campo="...",
)

# Publicar
client.api_v1_update_course(course_id=10, is_published=True)

# Actualizar lección
client.api_v1_update_lesson(
    lesson_id=152,
    content="Contenido generado desde investigación web académica o pipeline de digitalización M360...",
    logro_semana="Identifica los elementos del curso virtual...",
    saberes_esenciales="Introducción a los cursos virtuales",
    actividades="Revisa la guía del curso, presenta tu primer foro...",
    trabajo_campo="No aplica.",
    lesson_type="text",
    quiz_questions=[...],
)
```

Reglas:
- Usar SIEMPRE `description` y `bibliografia`; no crear items vacíos.
- `career_id`, `cycle_id` y `category_id` son recomendados (opcionales en el modelo); el backend acepta NULL.
- Si el curso queda sin publicar, asegurar visibilidad para superusuarios/staff.
- Para poblar contenido de lecciones, usar `api_v1_update_lesson` con `content`, `logro_semana`, `saberes_esenciales`, `actividades` y `trabajo_campo`. El método aplica allowlist de campos; kwargs fuera de la lista se descartan en silencio.
- Las lecciones evaluativas deben definirse como `lesson_type='quiz'` y poblarse con `quiz_questions`.
- Para extraer contenido oficial de PDFs, usar el pipeline de digitalización M360: preprocesamiento + OCR Tesseract/Vision, disponible en `digitalizacion/services/` del proyecto Management360.

## Digitalización — recursos transversales del pipeline M360

La app `digitalizacion` es un recurso transversal de M360: sirve a cualquier proyecto, no es exclusiva de Administracion_UPN ni de ningún curso.  
El bridge expone métodos para consumir ese pipeline desde Python.

### Procedimientos

Existen **dos procedimientos oficiales**:

| Procedimiento | Entrada | Vía | Modo endpoint |
|---|---|---|---|
| **Born-digital / archivo existente** | PDF, DOCX, XLSX, etc. | `digi_ingestar_lote` | `existing` |
| **Escaneo** | Original físico | Flujo web de recepción (`recepcion.html`) | — |

Regla: ambos procedimientos comparten el mismo modelo de datos y microformato JSON, pero **no comparten etapas intermedias**. Born-digital no pasa por deskew/denoise/OCR forzado. Escaneo no pasa por characterisation ni antivirus. El endpoint de carga vía bridge solo acepta modo `existing`: `scan` responde 400 ("Modo scan no permitido en este endpoint") y debe usar el flujo web.

```python
from tools.m360_bridge.client import M360Client

client = M360Client(
    base_url="http://127.0.0.1:8000",
    username="su",
    password="...",
)

# Born-digital / archivo existente
resp = client.digi_ingestar_lote(
    folder_path="/ruta/a/la/carpeta/documentos",
    nombre_lote="Lote born-digital oficial",
    metadata_proyecto={"origen": "carpeta_upn", "ciclo": "01"},
)
print(resp["ok"], resp["lote_id"], len(resp["documentos"]))
```

Métodos disponibles:
- `digi_ingestar_lote(folder_path, nombre_lote=None, metadata_proyecto=None)`: registra archivos born-digital existentes como documentos del lote vía endpoint con modo `existing`. La characterisation, extracción de metadatos embebidos, antivirus y fixity sobre originales las ejecuta el backend de M360.
- `digi_cargar_lote(folder_path, nombre_lote=None, metadata_proyecto=None)`: alias de compatibilidad de `digi_ingestar_lote`.
- `api_v1_digi_cargar_lote(nombre_lote, ruta_base, modo="existing", created_by_id=None, metadata_proyecto=None, ruta_fuente=None)`: variante directa contra el endpoint `POST /api/v1/digitalizacion/lotes/cargar/`. `ruta_fuente` es obligatorio en el endpoint; si se omite, se envía igual a `ruta_base`.
- `digi_validar_documento(file_path)`: validación local aún NO implementada; devuelve `ok: False` con `validacion_no_implementada`. No usar como gate de ingesta hasta que exista checksum/characterisation real.

Endpoint M360 usado:
- `POST /api/v1/digitalizacion/lotes/cargar/`
- Payload obligatorio: `nombre_lote`, `ruta_fuente`, `ruta_base`, `modo` (`existing`), `created_by_id`, `metadata_proyecto`.

Notas:
- Para carga desde carpeta, el endpoint copia los archivos a `<ruta_base>/inbox/<document_id>/`.
- `document_id` se trunca a 60 caracteres y se desduplica globalmente.
- El tipo de documento se infiere por nombre (`silabo`, `evaluacion`, `material`, `plan_estudios`, `certificado`, `documento`).
- El pipeline posterior (preprocesamiento, OCR, PDF/A, checksums, certificado) se ejecuta desde la UI o por llamadas a `PipelineDigitalizacion` en M360.
- Born-digital: no se ejecutan deskew/denoise/OCR forzado. Se ejecutan characterisation, extracción de metadatos embebidos, antivirus, fixity sobre originales.
- Digitalización es independiente de la app cursos; el bridge solo opera lotes y documentos digitalizados.

## Nota para no repetir este error

- `client.py` = librería/base del bridge.
- `sync.py` = sincronizador de sprints.
- Si el objetivo es “leer/ver tareas desde CLI”, el acceso debe hacerse por lectura directa del estado local o por un script específico; no por `client.py` como si fuera CLI.
