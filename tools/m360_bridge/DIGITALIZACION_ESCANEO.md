# Digitalización por ESCANEO — tools para agentes LLM

`tools/m360_bridge/digitalizacion_tools.py` expone 10 herramientas de function-calling (`tool_definitions()` + `ejecutar(nombre, args)`) para que un agente opere el flujo de **digitalización de documentos físicos** contra M360 (`http://127.0.0.1:8000`). Este documento cubre el flujo ESCANEO; el born-digital vive en el README principal del bridge.

## Flujo canónico

```
digi_crear_lote_escaneo(productor, ruta_base, titular, finalidad, proyecto_destino, m360_proyecto_id)
  → digi_crear_documento(lote_id, tipo, titulo, productor, fecha_documento, folios)
    → digi_subir_imagenes_escaneo(documento_id, rutas)
      → digi_avanzar_etapa(documento_id, etapa[, avanzar_todas])
```

Lecturas (seguras): `digi_listar_lotes`, `digi_estado_lote`, `digi_estado_documento`, `digi_buscar_por_productor`.

Etapas válidas (`ETAPAS`): `preparacion, digitalizacion, qc1, preprocesamiento, metadatos, qc2, auditoria, fedatacion, certificado`.

## Reglas duras implementadas (no bypasseables sin `forzar`)

| Regla | Detalle |
|---|---|
| **Scoping de subida** | Las rutas locales deben resolver dentro de `ruta_inbox` del documento. Se abre **una vez por fd** con `O_NOFOLLOW`, se exige `st_nlink == 1` (rechaza hardlinks), `S_ISREG` (rechaza FIFOs) y la ruta canónica del fd dentro del inbox. El stream se lee del mismo fd (sin ventana TOCTOU). Errores: `RUTA_FUERA_DE_SCOPE`, `HARDLINK_NO_PERMITIDO`, `RUTA_NO_ES_ARCHIVO`, `RUTA_NO_LEIBLE`. |
| **Fecha estricta** | `fecha_documento` debe cumplir `^\d{4}-\d{2}-\d{2}$` (`20261014` y week-dates se rechazan pese a que `date.fromisoformat` los acepta). El payload recibe la fecha **normalizada**, no el input crudo. |
| **Timeout ≠ fallo** | Subidas y avance de etapa devuelven `TIMEOUT_ESTADO_DESCONOCIDO` (nunca error duro) con instrucción de verificar antes de reintentar: un retry a ciegas duplica páginas o re-ejecuta la cascada OCR. |
| **Verificación real** | La subida se confirma re-leyendo el documento (`document_id` coincidente); el avance de etapa verifica el registro en `lote.etapas` (`documento`, `etapa`, `estado == "ok"`). Semántica: `verificado: True` (registrada), `False` (GET ok, sin registro), `None` (no se pudo verificar — la etapa PUEDE haberse ejecutado; NO reintentar). |
| **Anti-duplicado de lotes** | Reutiliza solo lotes del mismo productor **abiertos** (`preparacion`/`digitalizacion`), creados en las **últimas 48h** y con `ruta_base` existente en disco. Advierte (`advertencia_reutilizacion`) cuando había candidatos descartados por antigüedad/ruta. |
| **Coerción de booleanos** | `ejecutar` acepta solo bool real, `"true"/"false"` o 1/0 en parámetros booleanos; cualquier otro valor → `ARG_BOOL_INVALIDO`. `{"confirmar": "false"}` **no** ejecuta borrados. |

## Herramientas de borrado (DESTRUCTIVAS)

`digi_eliminar_documento` / `digi_eliminar_lote` siguen el protocolo **previsualizar → confirmar**:

1. **Sin `confirmar`**: devuelve `{requiere_confirmacion: true, ...}` con la identidad del objetivo (y para lotes: lista y conteo de documentos afectados + etapas). **No borra.**
2. **Con `confirmar: true`**: verifica existencia, borra, y confirma con un 404 posterior (`eliminado: true`).

Guardas adicionales:

| Guarda | Comportamiento |
|---|---|
| Lote/documento **certificado** | Exige `forzar: true` **+ `motivo`** (no vacío). La primitiva `api_v1_delete_lote` rechaza certificados con **409** salvo `forzar`, para que ningún caller futuro evite la guarda. |
| **Etapas en vuelo** (`fin` vacío) | Rechaza con `ETAPAS_EN_PROGRESO` (documento o lote): borrar a mitad de OCR/PDF/A corrompe el pipeline. |
| **Idempotencia** | Objetivo inexistente (404 auténtico de DRF) → `ya_no_existia: true`. Un 404 de ruta/pk inválido → error `*_NO_ENCONTRADO`. Fallos transitorios → `LECTURA_FALLO` (reintentar). |
| **Archivos persistentes** | El DELETE de la API es **DB-only** (DRF `destroy`): las imágenes en `ruta_inbox`/`ruta_preprocessed`/`ruta_master`/`ruta_acceso` **permanecen en disco**. Toda respuesta de borrado incluye `advertencia_filesystem` con las rutas a limpiar manualmente. La vista web de M360 (`eliminar_documento`) sí limpia filesystem; el DELETE de API no. |

## Comportamientos verificados de la API de M360 (no documentados oficialmente)

| Hallazgo | Impacto |
|---|---|
| **El metadata OPTIONS miente**: los endpoints de digitalización listan solo PUT, pero **DELETE funciona** (204). La ausencia de `DELETE` en la introspección NO implica que esté prohibido. | El bridge expone `api_v1_delete_document`/`api_v1_delete_lote`. |
| `?offset=` es **ignorado**; las listas devuelven **listas peladas sin `meta` de conteo**. | No se puede paginar ni detectar truncamiento servidor-side: las ventanas usan `max_total` con flag `truncated` (limitación conocida documentada). |
| `?search=` es **ignorado** en documentos. | `buscar_por_productor` filtra client-side sobre la ventana. |
| `ruta_base`/`ruta_inbox` son **rutas locales** (disco del servidor M360, co-localizado). | El scoping de subida usa `ruta_inbox` como raíz válida. |
| Estados de lote observados: `preparacion`, `digitalizacion`, `certificado`. | Reutilización y guardas se basan en estos. |
| `EtapaPipeline` con `fin` vacío = etapa en vuelo. | Base del bloqueo `ETAPAS_EN_PROGRESO`. |
| Sesión: vistas de app se autentican por cookie+CSRF; `_post_vista` **no** envía Bearer (evita fuga en redirects cross-host) y hace fail-closed ante páginas de login/error. Re-intenta una vez en 401/403 (solo cuerpos en memoria). |

## Referencias

- README principal del bridge (born-digital, diagnóstico).
- Repo M360 (servidor): `projects/Management360/` (app `digitalizacion/`).
