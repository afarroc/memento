# Linea de produccion de digitalizacion y microformatos — Proyecto UPN

**Proyecto:** Administracion_UPN / mementobloom  
**Alcance:** pipeline end-to-end desde captura por escaner hasta microformato JSON preservable.  
**Base:** mejores hallazgos 2026 en pipelines de digitalizacion institucional + docSchema + Dublin Core + PDF/A + METS/PREMIS.

---

## 1. Estandares adoptados

| Capa | Estandar | Rol en el pipeline |
|---|---|---|
| Formato de archivo accesible | PDF/A-2b (ISO 19005-2) | Surrogado de difusion; autocontenido, fuentes incrustadas, sin dependencias externas. |
| Formato de archivo preservable | TIFF (sin compresion con perdida) | Master de preservacion cuando se requiera maxima fidelidad. |
| Metadatos descriptivos | Dublin Core (DCMI / ES) + perfil UPN | Identificacion, descubrimiento, interoperabilidad con repositorios institucionales. |
| Metadatos tecnicos / preservacion | PREMIS (v3) | Agentia, formato, checksum, acciones de preservacion. |
| Contenedor de empaquetado | METS (Metadata Encoding and Transmission Standard) | Agrupa binarios + metadatos descriptivos + administrativos + estructurales. |
| Microformato de trabajo | JSON legible por agentes (inspirado en docSchema) | Contrato canonical entre etapas del pipeline; apto para ingestion por LLM/agentes. |

---

## 2. Pipeline de produccion

### 2.1 Captura (scanlib / HP Easy Scan)

Herramienta preferida: `scanlib` (ImageCaptureCore) sin `brew`.

```bash
# Listar dispositivo
python3 -m scanlib list

# Captura a JPEG 300 DPI color (trabajo intermedio)
python3 -m scanlib scan \
  -s 0 \
  -d "/Volumes/Macintosh HD - Datos/otros_proyectos/Administracion_UPN/Documentos_Escaneados/inbox" \
  -p "upn_YYYY-MM-DD_pXXX" \
  --dpi 300 \
  --color-mode color \
  --format jpeg \
  --jpeg-quality 95
```

Reglas:
- Cerrar HP Easy Scan / Image Capture antes de usar CLI.
- Un documento = una carpeta `inbox/<doc_id>/`.
- No procesar hasta completar la captura de todas las paginas.

### 2.2 Preprocesamiento

Objetivo: normalizar imagen para OCR y conversiones posteriores.

Pasos automaticos (Python + Pillow + OpenCV):
1. **Deskew** (`opencv-python` minAreaRect).
2. **Denoise** (`medianBlur` 3x3).
3. **Deshacer warping** si el documento esta doblado (opcional, solo si se detecta perspectiva > 3 grados).
4. **Resize** a 300 DPI equivalente si la captura fue a menor resolucion.
5. **Validacion de calidad**: rechazar si blur score (Laplacian variance) < 100.

### 2.3 Conversion a preservacion / acceso

```bash
# Acceso (PDF/A-2b)
# Usar PyMuPDF / pypdf para combinar imagenes en PDF/A con XMP metadata.
# Validar con veraPDF o Acrobat Preflight cuando sea posible.

# Preservacion (TIFF master)
# Conservar solo si el documento es patrimonio/tesis/acta oficial.
```

Regla: todo documento que ingresa a repositorio debe tener al menos PDF/A-2b.

### 2.4 OCR y extraccion de texto

Stack preferido (sin `brew`):
- OCR primario: Tesseract si esta disponible, si no `pytesseract` desde entorno portable.
- Alternativa agentica: multimodal LLM sobre imagen para documentos con tablas/manuscritos.

Salida OCR: `ocr_text.txt` + `ocr_confidence.json` por pagina.

### 2.5 Generacion de microformato JSON

Cada documento escaneado produce un registro en `microformatos/<doc_id>.json` con esta estructura:

```json
{
  "schemaVersion": "1.0.0",
  "documentId": "upn_2026-07-19_001",
  "type": "DocumentoEscaneado",
  "source": {
    "scanner": "HP Ink Tank 310 series",
    "captureDate": "2026-07-19T20:45:00-05:00",
    "captureTool": "scanlib 1.3.1",
    "originalFiles": [
      "inbox/upn_2026-07-19_p001.jpg",
      "inbox/upn_2026-07-19_p002.jpg"
    ]
  },
  "dublinCore": {
    "title": "...",
    "creator": "...",
    "subject": ["..."],
    "description": "...",
    "date": "2026-07-19",
    "type": "Documento administrativo",
    "format": "image/jpeg",
    "language": "es",
    "rights": "Derechos reservados UPN",
    "identifier": "upn_2026-07-19_001"
  },
  "processing": {
    "ocrEngine": "tesseract",
    "ocrConfidence": 0.96,
    "preprocessing": ["deskew", "denoise"],
    "convertedToPdfA": true,
    "pdfAPath": "acceso/upn_2026-07-19_001.pdf",
    "masterTiffPath": "master/upn_2026-07-19_001.tiff",
    "checksum": {
      "md5": "...",
      "sha256": "..."
    }
  },
  "structuredContent": {
    "pages": [
      {
        "pageNumber": 1,
        "ocrText": "...",
        "confidence": 0.97,
        "layoutType": "text|table|form|mixed",
        "fields": [
          {"name": "campo", "value": "...", "confidence": 0.99}
        ]
      }
    ]
  },
  "relations": {
    "isPartOf": "Administracion_UPN",
    "relatedHandoff": "projects/Administracion_UPN/handoffs/HANDOFF_2026-07-19_...md"
  }
}
```

Este JSON es el **microformato canonical** del pipeline.

### 2.6 Validacion y control de calidad

Checklist por documento:
- [ ] Imagenes capturadas sin cortes ni sombras.
- [ ] OCR confidence promedio >= 0.90 en paginas de texto.
- [ ] PDF/A validado (veraPDF o similar).
- [ ] Microformato JSON esquema valido (ver seccion 4).
- [ ] Checksum calculado y registrado.
- [ ] Nomenclatura respeta `upn_YYYY-MM-DD_NNN`.
- [ ] Dublin Core completo para tipo de documento.

### 2.7 Archivado

Estructura final en el proyecto UPN:

```
/Volumes/Macintosh HD - Datos/otros_proyectos/Administracion_UPN/
├── Documentos_Escaneados/
│   ├── inbox/             # Captura cruda
│   ├── preprocessed/      # Imagenes corregidas
│   ├── acceso/            # PDF/A-2b
│   ├── master/            # TIFF (si aplica)
│   ├── ocr/               # txt + json por pagina
│   └── microformatos/     # JSON canonical por doc
└── handoffs/              # Registros de cierre/sesion
```

Regla: nada sale de `inbox` sin microformato y checksum.

---

## 3. Reglas de nomenclatura

| Elemento | Patron |
|---|---|
| Documento | `upn_YYYY-MM-DD_NNN.ext` |
| Carpeta de trabajo | `upn_YYYY-MM-DD_NNN/` |
| Microformato | `upn_YYYY-MM-DD_NNN.json` |
| Handoff | `HANDOFF_YYYY-MM-DD_<tema>.md` |

`NNN` es secuencia correlativa por dia en el proyecto UPN.

---

## 4. Esquema JSON minimo (contrato)

El microformato debe validar contra este contrato:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UPNScannedDocument",
  "type": "object",
  "required": ["schemaVersion", "documentId", "type", "source", "dublinCore", "processing"],
  "properties": {
    "schemaVersion": {"type": "string"},
    "documentId": {"type": "string", "pattern": "^upn_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{3}$"},
    "type": {"type": "string"},
    "source": {
      "type": "object",
      "required": ["captureDate", "originalFiles"],
      "properties": {
        "captureDate": {"type": "string", "format": "date-time"},
        "originalFiles": {"type": "array", "items": {"type": "string"}},
        "scanner": {"type": "string"},
        "captureTool": {"type": "string"}
      }
    },
    "dublinCore": {
      "type": "object",
      "required": ["title", "creator", "date", "type", "identifier"],
      "properties": {
        "title": {"type": "string"},
        "creator": {"type": "string"},
        "subject": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"},
        "date": {"type": "string"},
        "type": {"type": "string"},
        "format": {"type": "string"},
        "language": {"type": "string"},
        "rights": {"type": "string"},
        "identifier": {"type": "string"}
      }
    },
    "processing": {
      "type": "object",
      "required": ["ocrEngine", "checksum"],
      "properties": {
        "ocrEngine": {"type": "string"},
        "ocrConfidence": {"type": "number", "minimum": 0, "maximum": 1},
        "convertedToPdfA": {"type": "boolean"},
        "pdfAPath": {"type": "string"},
        "masterTiffPath": {"type": "string"},
        "checksum": {
          "type": "object",
          "required": ["sha256"],
          "properties": {
            "md5": {"type": "string"},
            "sha256": {"type": "string"}
          }
        }
      }
    },
    "structuredContent": {
      "type": "object",
      "properties": {
        "pages": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pageNumber", "ocrText"],
            "properties": {
              "pageNumber": {"type": "integer"},
              "ocrText": {"type": "string"},
              "confidence": {"type": "number"},
              "layoutType": {"type": "string"},
              "fields": {"type": "array"}
            }
          }
        }
      }
    }
  }
}
```

---

## 5. Integracion con mementobloom

- Cada microformato JSON se indexa en `memory/graph/memory_index.json` como entry tipo `MICROFORMATO` con project=`Administracion_UPN`.
- El handoff de sesion cita el/los `documentId` generados.
- El tutor-cursos puede consumir `microformatos/*.json` para construir modulos/lecciones desde contenido OCR validado.

---

## 6. Troubleshooting corto

- `scanlib list` vacio: cerrar apps HP, reconectar USB, reintentar.
- OCR < 90%: revisar deskew/denoise; para manuscritos usar VLM multimodal.
- PDF/A rechazado: validar con veraPDF; si tiene transparencias complejas usar PDF/A-2b.
- Checksum no cuadra: recalcular sobre `preprocessed/` (no sobre `inbox/` si se edito).
- JSON invalido: validar contra el esquema de la seccion 4 antes de archivar.

---

## 7. Referencias

- ISO 19005-2 (PDF/A-2)
- Dublin Core Metadata Element Set v1.1
- METS / PREMIS (Library of Congress)
- docSchema (piwi-ai) — modelo de schema JSON para documentos
- scanlib (amottola) — CLI multiplataforma sin brew
- Vidya / IPUMS / NEURO.AI — pipelines academicos de digitalizacion
