# Arquitectura: Servicio de línea de producción de microformatos UPN

**Proyecto:** Administracion_UPN / mementobloom  
**Fecha:** 2026-07-19  
**Estado:** Propuesta de arquitectura basada en estándares 2026

---

## 1. Filosofía

La digitalización no es escanear. Es una **línea de producción** con etapas de preparación, captura, control de calidad, metadatos, auditoría, certificación y microformato. Cada etapa tiene modos de fallo distintos; omitir cualquiera de ellas convierte el documento en "papel digitalizado", no en un activo digital confiable.

Esta arquitectura adopta:
- **OAIS** (ISO 14721) como modelo de preservación.
- **METS + PREMIS** como contenedor de metadatos preservables.
- **Dublin Core** como perfil descriptivo interoperable.
- **PDF/A-2b** como surrogado de acceso.
- **SHA-256 + timestamp** como cadena de integridad mínima.

---

## 2. Etapas de la línea de producción

### Etapa 1 — Recepción y acondicionamiento

| Actividad | Detalle |
|---|---|
| Inspección física | Detectar grapas, clips, post-its, humedad, roturas. |
| Reparación mínima | Desgrapar, alisar pliegues, limpiar manchas superficiales. |
| Foliado | Numerar páginas físicas si no tienen numeración propia. |
| Identificación | Asignar `batch_id`, `document_id` temporal, responsable. |
| Cadena de custodia | Registro de entrada: quién recibe, fecha, estado del original. |

**Salida:** documento acondicionado + acta de recepción.

---

### Etapa 2 — Digitalización (captura)

| Actividad | Detalle |
|---|---|
| Configuración del escáner | 300 DPI mínimo, color o escala de grises según documento. |
| Captura | Una pasada por hoja; no saltarse páginas. |
| Formato bruto | JPEG o TIFF sin compresión con pérdida. |
| Verificación de secuencia | Número de páginas escaneadas = número de páginas físicas. |

**Salida:** imágenes crudas en `inbox/<batch_id>/`.

---

### Etapa 3 — Control de calidad 1 (CC1)

| Actividad | Detalle |
|---|---|
| Inspección visual | Orientación, recortes, sombras, desenfoque, páginas faltantes. |
| Métricas objetivas | Resolución, profundidad de bits, ausencia de bordes negros. |
| Umbral de rechazo | Si ≥1% de páginas fallan, se rechaza el lote completo. |
| Corrección | Deskew, denoise, recorte de márgenes sobrantes. |

**Salida:** imágenes aprobadas en `preprocessed/<batch_id>/` o lote rechazado con informe.

---

### Etapa 4 — Metadatos (descripción + preservación)

| Actividad | Detalle |
|---|---|
| Metadatos descriptivos | Dublin Core: título, creador, fecha, tipo, tema, idioma, derechos. |
| Metadatos técnicos | DPI, formato, dimensions, perfil de color. |
| Metadatos de preservación | PREMIS: objeto, evento, agente. |
| Microformato JSON | Contrato canonical del documento para consumo por agentes. |
| Nomenclatura | `upn_YYYY-MM-DD_NNN` para archivos y `documentId`. |

**Salida:** microformato JSON completo en `microformatos/<document_id>.json`.

---

### Etapa 5 — Control de calidad 2 (CC2)

| Actividad | Detalle |
|---|---|
| Validación de metadatos | Campos obligatorios presentes, valores en dominios válidos. |
| Validación de esquema | JSON válido contra schema; METS bien formado si aplica. |
| Validación de integridad | Checksum SHA-256 calculado y registrado. |
| Validación de contenido | OCR confidence ≥ umbral definido; páginas legibles. |
| Validación de accesibilidad | PDF/A-2b generado y validado con veraPDF o equivalente. |

**Salida:** documento certificado para archivado o devuelto a corrección.

---

### Etapa 6 — Auditoría y trazabilidad

| Actividad | Detalle |
|---|---|
| Bitácora de lote | Registro de quién hizo cada etapa, timestamps, resultados. |
| Eventos PREMIS | `ingest`, `fixity-check`, `validation`, `pdfa-conversion`, `ocr`. |
| Control de cambios | Diferencia entre `inbox/` y `preprocessed/` registrada. |
| Reporte de calidad | Estadísticas: % rechazo CC1, % rechazo CC2, confianza OCR promedio. |

**Salida:** informe de auditoría en `ocr/<batch_id>_audit.json`.

---

### Etapa 7 — Fedatación (certificación de integridad)

| Actividad | Detalle |
|---|---|
| Hash criptográfico | SHA-256 del surrogado de acceso (PDF/A) y del master. |
| Sello de tiempo | Timestamp RFC 3161 o equivalente confiable. |
| Identificador único | UUID o `documentId` único e irreversible. |
| Registro de certificación | JSON con hash, timestamp, agente certificador. |
| Verificabilidad | Cualquier actor puede verificar integridad sin dependencia de sistema propietario. |

**Salida:** certificado de integridad en `microformatos/<document_id>_cert.json` o dentro del microformato principal.

---

### Etapa 8 — Archivado y publicación

| Actividad | Detalle |
|---|---|
| Movimiento a carpetas finales | `acceso/`, `master/`, `ocr/` poblados. |
| Indexación | Registro en catálogo/dashboard para búsqueda. |
| Backup | Copia a medio externo o servicio de backup. |
| Publicación | URL pública si aplica; enlace desde M360 si está vinculado. |
| Notificación | Handoff actualizado; dashboard regenerado. |

**Salida:** documento archivado, descubrible y verificable.

---

## 3. Estructura de carpetas canónica

```
Documentos_Escaneados/
├── inbox/
│   └── <batch_id>/
│       └── <originales_crudos>
├── preprocessed/
│   └── <batch_id>/
│       └── <imagenes_corregidas>
├── acceso/
│   └── <document_id>.pdf
├── master/
│   └── <document_id>.tiff
├── ocr/
│   ├── <document_id>_texto.txt
│   ├── <document_id>_paginas.json
│   └── <batch_id>_audit.json
└── microformatos/
    ├── <document_id>.json
    └── <document_id>_cert.json
```

---

## 4. Microformato JSON (contrato)

```json
{
  "schemaVersion": "1.0.0",
  "documentId": "upn_YYYY-MM-DD_NNN",
  "type": "Plan de estudios | Examen | Sesion | ...",
  "source": {
    "batchId": "batch_...",
    "scanner": "...",
    "captureDate": "...",
    "captureTool": "...",
    "originalFiles": ["inbox/..."]
  },
  "dublinCore": {
    "title": "...",
    "creator": "...",
    "subject": ["..."],
    "description": "...",
    "date": "...",
    "type": "...",
    "format": "...",
    "language": "...",
    "rights": "...",
    "identifier": "..."
  },
  "processing": {
    "ocrEngine": "tesseract|pending",
    "ocrConfidence": 0.0-1.0,
    "preprocessing": ["deskew", "denoise"],
    "convertedToPdfA": true|false,
    "pdfAPath": "acceso/...",
    "masterTiffPath": "master/...",
    "checksum": {
      "sha256": "...",
      "md5": "..."
    }
  },
  "certification": {
    "fedatado": true|false,
    "certificadoPath": "microformatos/..._cert.json",
    "timestamp": "...",
    "uuid": "...",
    "hash": "...",
    "agente": "mementobloom|entidad_certificadora"
  },
  "structuredContent": {
    "pages": [
      {
        "pageNumber": 1,
        "ocrText": "...",
        "confidence": 0.0-1.0,
        "layoutType": "text|table|form|mixed",
        "fields": [
          {"name": "...", "value": "...", "confidence": 0.0-1.0}
        ]
      }
    ]
  },
  "relations": {
    "isPartOf": "Administracion_UPN",
    "cursoM360Id": null,
    "tareaM360Id": null,
    "relatedHandoff": "..."
  }
}
```

---

## 5. Integración con M360

El dashboard y la API deben vivir dentro de M360 como la app `digitalizacion`.

### 5.1 App Django `digitalizacion`

```
Management360/
├── digitalizacion/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── templates/digitalizacion/dashboard.html
│   └── management/commands/
│       └── sync_microformatos.py
```

### 5.2 Modelo principal

```python
class MicroformatoDigital(models.Model):
    document_id = models.CharField(max_length=64, unique=True)
    batch_id = models.CharField(max_length=64, db_index=True)
    tipo = models.CharField(max_length=128)
    titulo = models.CharField(max_length=255)
    creador = models.CharField(max_length=255)
    fecha_documento = models.DateField(null=True, blank=True)
    ruta_inbox = models.CharField(max_length=512)
    ruta_preprocessed = models.CharField(max_length=512)
    ruta_acceso = models.CharField(max_length=512, blank=True)
    ruta_master = models.CharField(max_length=512, blank=True)
    ruta_microformato = models.CharField(max_length=512)
    ruta_certificado = models.CharField(max_length=512, blank=True)
    checksum_sha256 = models.CharField(max_length=128, blank=True)
    ocr_engine = models.CharField(max_length=64, default='pending')
    ocr_confidence = models.FloatField(null=True, blank=True)
    converted_to_pdf_a = models.BooleanField(default=False)
    fedatado = models.BooleanField(default=False)
    uuid = models.CharField(max_length=64, blank=True, db_index=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    proyecto_m360 = models.ForeignKey('projects.Project', null=True, blank=True, on_delete=models.SET_NULL)
    curso_m360 = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.SET_NULL)
    tarea_m360 = models.ForeignKey('tasks.Task', null=True, blank=True, on_delete=models.SET_NULL)
    json_completo = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 5.3 API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/digitalizacion/microformatos/` | Lista paginada con filtros |
| GET | `/api/v1/digitalizacion/microformatos/{document_id}/` | Detalle + JSON |
| POST | `/api/v1/digitalizacion/microformatos/` | Alta manual desde pipeline |
| PATCH | `/api/v1/digitalizacion/microformatos/{document_id}/` | Actualizar estado OCR/PDF/A |
| GET | `/api/v1/digitalizacion/dashboard/` | Datos para dashboard |
| GET | `/digitalizacion/` | Dashboard HTML |

### 5.4 Filtros del dashboard

- Por tipo de documento.
- Por estado OCR (`pending`, `tesseract`, etc.).
- Por PDF/A (`true`/`false`).
- Por curso M360 vinculado.
- Por lote/batch.
- Búsqueda por título o `documentId`.

---

## 6. Pipeline automatizable (futuro)

```
[Inbox watcher]
    ↓
[Clasificador de tipo de documento]
    ↓
[Preparación: deskew + denoise]
    ↓
[OCR / IDP]
    ↓
[Extracción de campos estructurados]
    ↓
[Validación reglas + HITL]
    ↓
[Generación PDF/A-2b]
    ↓
[Cálculo checksum + timestamp]
    ↓
[Certificación / fedatación]
    ↓
[Registro en M360 + dashboard]
```

Para orquestación futura se recomienda evaluar **Dagster** o **Celery** con workers separados por etapa, manteniendo METS/PREMIS como capa de metadatos preservables.

---

## 7. Gobernanza

| Rol | Responsabilidad |
|---|---|
| Operador de digitalización | Preparación, escaneo, CC1. |
| Especialista metadata | Dublin Core, PREMIS, microformato JSON. |
| Auditor | CC2, validación de esquema, reporte de calidad. |
| Fedatario | Hash, timestamp, certificado de integridad. |
| Tutor / responsable UPN | Aprobación final, vinculación a curso M360. |

---

## 8. Próximos pasos

1. Crear la app `digitalizacion` dentro de M360.
2. Migrar los microformatos JSON actuales al modelo Django.
3. Servir el dashboard desde `/digitalizacion/`.
4. Implementar CC2 automatizada (validación JSON schema + PDF/A check).
5. Agregar certificación SHA-256 + timestamp a la etapa de fedatación.
