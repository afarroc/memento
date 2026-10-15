"""Herramientas (tools) de digitalización del pipeline M360 para agentes LLM.

Diseñado según mejores prácticas de tool-calling (validadas 2026-10-10):
- Nombres verb_noun, snake_case, ≤64 chars.
- Descripciones con cuándo usar Y cuándo NO usar.
- Schemas estrictos: required explícito, enums para categóricos, format hints.
- Respuestas estructuradas con next_steps para guiar al agente.
- Errores estructurados {error_code, message, suggestion} — nunca excepciones crudas.
- Separación read (seguras) / write (efecto en datos; requieren confirmación del operador humano).

Dos procedimientos oficiales (NO mezclar):
- ESCANEO: físico → lote registrado (sin ruta_fuente) → imágenes por upload → etapas.
- BORN-DIGITAL: archivo ya digital → ingesta con ruta_fuente (modo=existing).

Este móduloimplementa el camino ESCANEO íntegro por API:
  1. digi_crear_lote_escaneo      → POST /api/v1/digitalizacion/lotes/ (sin ruta_fuente)
  2. digi_crear_documento         → POST /api/v1/digitalizacion/documentos/
  3. digi_subir_imagenes_escaneo  → POST multipart (sesión) a /digitalizacion/procesar/<id>/
  4. digi_avanzar_etapa           → POST (sesión) a /digitalizacion/procesar/<id>/
Y lecturas: digi_listar_lotes, digi_estado_lote, digi_estado_documento, digi_buscar_por_productor.

Uso:
    from tools.m360_bridge.digitalizacion_tools import DigitalizacionTools
    tools = DigitalizacionTools(client)   # client = M360Client autenticado
    tools.crear_lote_escaneo(productor="Majorel", ruta_base="...")
"""

from __future__ import annotations

import fcntl
import mimetypes
import os
import re
import stat as stat_module
import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ArchivoModificado(OSError):
    """El archivo cambió de tamaño entre la validación y el stream.

    Hereda de OSError para que _post_vista la capture como network_error y
    falle ruidoso (nunca truncar silenciosamente el cuerpo multipart).
    """


def _es_404_no_existe(resp: Any) -> bool:
    """True solo si el 404 es el 'no existe' auténtico de DRF.

    Un 404 también aparece ante pk mal tipado o ruta inexistente (p.ej.
    base_url apuntando a un host sin las rutas de digitalización): tratar
    esos como 'ya no existía' enmascararía errores de input/config como
    éxito. Se exige el detail de DRF ("No X matches the given query").
    """
    if not (isinstance(resp, dict) and resp.get("http_error") == 404):
        return False
    detail = str(resp.get("detail") or resp.get("raw") or "").lower()
    return "matches the given query" in detail or "not found" in detail


def _es_fallo_transitorio(resp: Any) -> bool:
    """True si la respuesta es un fallo que justifica reintento (no un 404).

    network_error/timeout/401/403 en un pre-check NO deben reportarse como
    'no encontrado': el agente podría crear duplicados atribuyendo a un ID
    inexistente lo que fue un corte de red o sesión expirada.
    """
    if not isinstance(resp, dict):
        return False
    if resp.get("network_error") or resp.get("timeout"):
        return True
    return resp.get("http_error") in (401, 403)


def _ruta_de_fd(fd: int) -> str:
    """Ruta canónica del archivo abierto en `fd` (F_GETPATH o /proc).

    En macOS fcntl(F_GETPATH) DEVUELVE los bytes de la ruta (no rellena el
    buffer en el sitio); en Linux cae al fallback /proc/self/fd.
    """
    try:
        r = fcntl.fcntl(fd, fcntl.F_GETPATH, bytearray(1024))
        if isinstance(r, (bytes, bytearray)):
            return bytes(r).split(b"\0", 1)[0].decode("utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    return os.path.realpath(f"/proc/self/fd/{fd}")


def _abrir_escaneo(ruta: str, inbox_res: Path):
    """Abre un escaneo y lo valida POR FD (no por nombre).

    Devuelve (fd, nombre, ctype). El fd queda abierto; el llamador lo cierra.

    Defensa contra bypass del scoping:
    - O_NOFOLLOW: rechaza symlink como componente final (abrir falla).
    - st_nlink == 1: rechaza hardlinks (resolve() no los sigue, así que un
      hardlink dentro del inbox apuntando a ~/.env pasaría un check por
      nombre; por fd se detecta).
    - ruta canónica del FD (F_GETPATH) verificada contra inbox_res.
    - S_ISREG: rechaza FIFOs/devices.
    El stream se lee desde ESTE fd: no hay ventana TOCTOU entre validar y
    leer (el contenido leído es el del inodo validado).
    """
    try:
        fd = os.open(ruta, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError as exc:
        raise ValueError(f"NO_EXISTE: {ruta}") from exc
    except OSError as exc:
        raise ValueError(f"NO_LEGIBLE: {ruta} ({exc})") from exc
    try:
        st = os.fstat(fd)
        if not stat_module.S_ISREG(st.st_mode):
            raise ValueError(f"NO_ARCHIVO: {ruta} no es un archivo regular")
        if st.st_nlink != 1:
            raise ValueError(f"HARDLINK: {ruta} tiene {st.st_nlink} enlaces; solo se permiten archivos con un único enlace")
        ruta_real = _ruta_de_fd(fd)
        real_res = Path(ruta_real).resolve()
        if real_res != inbox_res and not real_res.is_relative_to(inbox_res):
            raise ValueError(f"FUERA_DE_SCOPE: {ruta} resuelve a {ruta_real}, fuera del inbox")
        ctype = mimetypes.guess_type(ruta)[0] or "application/octet-stream"
        return fd, Path(ruta).name, ctype
    except Exception:
        os.close(fd)
        raise


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _validar_fecha_iso(fecha: Optional[str]) -> str:
    """Valida una fecha ISO 8601 ESTRICTA (YYYY-MM-DD).

    Devuelve la fecha normalizada o lanza ValueError. Crítico: este valor se
    interpola en document_id y luego en rutas de inbox/preprocessed, y se
    envía al payload de M360 (donde DRF solo acepta el formato con guiones).
    El regex limita el formato ANTES de fromisoformat, que en Python 3.11+
    también acepta YYYYMMDD y fechas de semana (2026-W42-3).
    """
    if not fecha:
        return datetime.now(timezone.utc).date().isoformat()
    texto = str(fecha).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        raise ValueError(
            f"fecha_documento '{fecha}' no es ISO 8601 estricto (YYYY-MM-DD); "
            "leer la fecha impresa del documento y normalizarla antes de catalogar"
        )
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError as exc:
        raise ValueError(
            f"fecha_documento '{fecha}' no es una fecha real (YYYY-MM-DD válido); "
            "verificar el valor leído del documento"
        ) from exc


def _generar_document_id(productor: str, fecha: Optional[str] = None) -> str:
    """Convención: <productor-normalizado>_<YYYYMMDD>_<8 hex únicos>.

    Formato análogo al de UPN (upn_YYYY-MM-DD_NNN) pero con el productor real.
    El sufijo usa 8 hex (no 3): con 3 hex la colisión por cumpleaños supera el
    50% con ~75 documentos del mismo productor el mismo día, y un document_id
    colisionado fusiona inbox/preprocessed de documentos distintos.
    """
    prod = re.sub(r"[^a-z0-9]+", "-", _norm(productor)).strip("-") or "doc"
    fecha_part = _validar_fecha_iso(fecha).replace("-", "")
    doc_id = f"{prod}_{fecha_part}_{uuid.uuid4().hex[:8]}"
    # Segunda pasada de sanitizado: conserva el separador '_' (formato canónico
    # <prod>_<fecha>_<suffix>) y elimina cualquier otro carácter ajeno a
    # [a-z0-9_-] — defensa contra valores inesperados en las partes.
    return re.sub(r"[^a-z0-9_-]", "", doc_id)


class DigitalizacionTools:
    """Tools de digitalización para agentes, envueltas sobre M360Client."""

    # Etapas del pipeline en orden (de views.pipeline_order)
    ETAPAS = [
        "preparacion", "digitalizacion", "qc1", "preprocesamiento",
        "metadatos", "qc2", "auditoria", "fedatacion", "certificado",
    ]

    def __init__(self, client: Any) -> None:
        self.client = client

    # ==================== WRITE (efecto en datos) ====================

    def crear_lote_escaneo(
        self,
        productor: str,
        ruta_base: str,
        titular: str = "",
        finalidad: str = "",
        proyecto_destino: str = "",
        m360_proyecto_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Crea un lote de digitalización por PROCEDIMIENTO DE ESCANEO.

        Usar cuando se van a digitalizar documentos FÍSICOS de un mismo
        productor (empresa emisora). NO usar para archivos ya digitales
        (para eso existe la ingesta born-digital con ruta_fuente).

        El lote se crea SIN ruta_fuente: las imágenes entran después por
        upload en la preparación del documento.

        Args:
            productor: Empresa emisora de los documentos (del documento físico).
            ruta_base: Carpeta raíz de trabajo del pipeline (debe existir en disco).
            titular: Titular del archivo personal.
            finalidad: Para qué se digitaliza (se guarda en metadata).
            proyecto_destino: Proyecto memento destino.
            m360_proyecto_id: ID del proyecto M360 destino.

        Returns:
            {ok, lote_id, nombre, siguiente_paso} o {error_code, message, suggestion}.
        """
        productor = (productor or "").strip()
        ruta_base = (ruta_base or "").strip()
        if not productor:
            return self._err("PRODUCTOR_REQUERIDO", "Falta el productor (empresa emisora).", "Leer la empresa del documento físico antes de crear el lote.")
        if not ruta_base:
            return self._err("RUTA_BASE_REQUERIDA", "Falta ruta_base (carpeta de trabajo del pipeline).", "Usar la carpeta _pipeline del proyecto, ej. .../documentos_trabajo/_pipeline/")
        # Anti-duplicado por productor: verificar lotes existentes con el mismo
        # productor en metadata (evita lotes duplicados para la misma empresa).
        # La API no soporta offset (verificado 2026-10-14): se pide una ventana
        # amplia y se reporta truncamiento; si el listado pudo quedar incompleto
        # NO se reutiliza ningún lote (se crea uno nuevo con advertencia).
        prod_norm = _norm(productor)
        listado = self.listar_lotes(max_total=1000)
        if not listado.get("ok"):
            return listado
        existentes = listado.get("lotes", [])
        truncado = listado.get("truncated", False)
        abiertos = ("preparacion", "digitalizacion")
        # Cota de reutilización: solo lotes ABIERTOS del mismo productor,
        # creados en las últimas 48h y con ruta_base viva en disco. Reutilizar
        # un lote viejo (o con ruta movida/archivada) archiva documentos nuevos
        # bajo rutas muertas y descarta la metadata del llamador.
        limite = datetime.now(timezone.utc) - timedelta(hours=48)

        def _reutilizable(l: Dict[str, Any]) -> bool:
            if _norm(str(l.get("productor") or "")) != prod_norm:
                return False
            if (l.get("estado") or "") not in abiertos:
                return False
            created = str(l.get("created_at") or "")
            if not created:
                return False
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                return False
            if dt < limite:
                return False
            ruta = (l.get("ruta_base") or "").strip()
            return bool(ruta) and Path(ruta).exists()

        candidatos = [l for l in existentes if _norm(str(l.get("productor") or "")) == prod_norm and (l.get("estado") or "") in abiertos]
        repetido = next((l for l in candidatos if _reutilizable(l)), None)
        if repetido:
            metadata_descartada = [
                k
                for k, v in {
                    "titular": titular,
                    "finalidad": finalidad,
                    "proyecto_destino": proyecto_destino,
                    "m360_proyecto_id": m360_proyecto_id,
                }.items()
                if v
            ]
            resp: Dict[str, Any] = {
                "ok": True,
                "lote_id": repetido["id"],
                "nombre": repetido["nombre"],
                "productor": productor,
                "duplicado_evitado": True,
                "siguiente_paso": f"Lote existente reutilizado (estado='{repetido.get('estado')}'). Crear documento con digi_crear_documento(lote_id={repetido['id']}, ...).",
            }
            if metadata_descartada:
                resp["advertencia"] = (
                    f"Metadata no aplicada al reutilizar el lote {repetido['id']}: {metadata_descartada}. "
                    "Los documentos nuevos quedan bajo la ruta_base del lote existente."
                )
            return resp
        prod_slug = re.sub(r"[^a-z0-9]+", "-", _norm(productor)).strip("-")
        nombre = f"trabajo-{prod_slug}"
        metadata = {
            "titular": titular,
            "productor": productor,
            "finalidad": finalidad,
            "proyecto_destino": proyecto_destino,
            "m360_proyecto_id": m360_proyecto_id,
        }
        payload = {
            "nombre": nombre,
            "ruta_base": ruta_base,
            "metadata_proyecto": {k: v for k, v in metadata.items() if v},
            "estado": "preparacion",
        }
        r = self.client._request_json("/api/v1/digitalizacion/lotes/", payload, method="POST")
        if self._es_error_resp(r):
            return self._err("CREAR_LOTE_FALLO", f"El endpoint rechazó la creación: {str(r)[:200]}", "Verificar credenciales M360 y que ruta_base sea carpeta válida en el servidor.")
        return {
            "ok": True,
            "lote_id": r.get("id"),
            "nombre": r.get("nombre") or nombre,
            "productor": productor,
            "duplicado_evitado": False,
            "siguiente_paso": f"Crear el primer documento del lote con digi_crear_documento(lote_id={r.get('id')}, ...).",
            **(
                {"advertencia": "Anti-duplicado NO concluyente: el listado de lotes volvió truncado. Verificar antes de subir imágenes."}
                if truncado
                else {}
            ),
            **(
                {"advertencia_reutilizacion": f"Existían {len(candidatos)} lote(s) abierto(s) del mismo productor pero se creó uno nuevo (fuera de la ventana de 48h o con ruta_base inexistente en disco)."}
                if candidatos
                else {}
            ),
        }

    def crear_documento(
        self,
        lote_id: int,
        tipo: str,
        titulo: str,
        productor: str,
        fecha_documento: Optional[str] = None,
        folios: Optional[int] = None,
        subject: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Crea (cataloga) un documento dentro de un lote de escaneo.

        Usar tras crear el lote, antes de subir imágenes. El tipo documental
        sale del documento físico (certificado, contrato, liquidación…).

        Args:
            lote_id: ID del lote (de crear_lote_escaneo).
            tipo: Tipo documental real del documento (ej. "certificado").
            titulo: Título descriptivo (ej. "Certificado de trabajo — <empresa>").
            productor: Empresa emisora (va al campo creator).
            fecha_documento: Fecha de emisión ISO 8601 (YYYY-MM-DD) si el documento la tiene.
            folios: Número de páginas/folios del físico.
            subject: Etiquetas; por defecto [tipo, productor].

        Returns:
            {ok, documento_id, document_id, siguiente_paso} o error estructurado.
        """
        lote = self._get(f"/api/v1/digitalizacion/lotes/{lote_id}/")
        if self._es_error_resp(lote):
            return self._err("LOTE_NO_ENCONTRADO", f"No se pudo leer el lote {lote_id}: {str(lote)[:200]}", "Verificar el ID con digi_listar_lotes().")
        ruta_base = (lote.get("ruta_base") or "").strip()
        if not ruta_base:
            return self._err("LOTE_SIN_RUTA_BASE", f"El lote {lote_id} no tiene ruta_base.", "Editar el lote para asignar su carpeta de trabajo del pipeline.")
        try:
            fecha_norm = _validar_fecha_iso(fecha_documento)
        except ValueError as exc:
            return self._err("FECHA_INVALIDA", str(exc), "Pasar fecha_documento en formato YYYY-MM-DD (leída del documento físico).")
        document_id = _generar_document_id(productor, fecha_norm)
        payload: Dict[str, Any] = {
            "lote": lote_id,
            "document_id": document_id,
            "tipo": (tipo or "").strip(),
            "titulo": (titulo or "").strip(),
            "creator": (productor or "").strip(),
            "ruta_inbox": str(Path(ruta_base) / "inbox" / document_id),
            "ruta_preprocessed": str(Path(ruta_base) / "preprocessed" / document_id),
            "ingest_mode": "scan",
            "language": "es",
            "subject": subject or [t for t in [(tipo or "").strip(), (productor or "").strip()] if t],
        }
        # Enviar la fecha NORMALIZADA, no el input crudo: si el llamador pasó
        # " 2026-10-14 " el payload debe llevar el valor canónico validado.
        if fecha_documento:
            payload["fecha_documento"] = fecha_norm
        if folios:
            payload["folios"] = folios
        r = self.client._request_json("/api/v1/digitalizacion/documentos/", payload, method="POST")
        doc_id = r.get("id") if isinstance(r, dict) else None
        if not doc_id:
            return self._err("CREAR_DOCUMENTO_FALLO", f"El endpoint rechazó la creación: {str(r)[:300]}", "Revisar campos obligatorios (lote, document_id, tipo, titulo).")
        return {
            "ok": True,
            "documento_id": doc_id,
            "document_id": r.get("document_id") or document_id,
            "lote_id": lote_id,
            "siguiente_paso": f"Subir las imágenes del escaneo con digi_subir_imagenes_escaneo(documento_id={doc_id}, rutas=[...]).",
        }

    def subir_imagenes_escaneo(self, documento_id: int, rutas: List[str]) -> Dict[str, Any]:
        """Sube imágenes del escaneo al inbox del documento (upload multipart).

        Usar después de crear el documento. Las imágenes van a
        <ruta_base>/inbox/<document_id>/ y quedan listas para la etapa
        de digitalización (imágenes → PDF).

        Args:
            documento_id: ID del documento.
            rutas: Rutas locales de las imágenes/PDF escaneados.

        Returns:
            {ok, archivos, inbox} o error estructurado.
        """
        rutas = [r for r in (rutas or []) if r]
        if not rutas:
            return self._err("RUTAS_REQUERIDAS", "No se recibieron rutas de imágenes.", "Pasar la lista de archivos escaneados, ej. ['/ruta/pag1.jpg'].")
        doc = self._get(f"/api/v1/digitalizacion/documentos/{documento_id}/")
        if self._es_error_resp(doc):
            return self._err("DOCUMENTO_NO_ENCONTRADO", f"No se pudo leer el documento {documento_id}: {str(doc)[:200]}", "Verificar ID con digi_estado_lote().")
        # SCOPING (seguridad): cada archivo se abre UNA vez con O_NOFOLLOW y
        # se valida POR FD (nlink==1 anti-hardlink, ruta canónica del fd dentro
        # del inbox, archivo regular). El stream se lee desde ese mismo fd, así
        # que no hay ventana TOCTOU entre validar y leer. Sin esto, un agente
        # inducido podría exfiltrar cualquier archivo local (p.ej. el .env de
        # credenciales) dentro del flujo normal, incluso vía hardlink.
        inbox = (doc.get("ruta_inbox") or "").strip()
        if not inbox:
            return self._err("DOCUMENTO_SIN_INBOX", f"El documento {documento_id} no tiene ruta_inbox definida.", "Revisar el lote y la catalogación del documento antes de subir imágenes.")
        try:
            inbox_res = Path(inbox).resolve()
        except OSError as exc:
            return self._err("INBOX_NO_RESOLVIBLE", f"No se pudo resolver ruta_inbox: {exc}", "Verificar que la ruta sea válida en disco.")
        items = []
        problemas = {"NO_EXISTE": [], "NO_LEGIBLE": [], "NO_ARCHIVO": [], "HARDLINK": [], "FUERA_DE_SCOPE": []}
        for r in rutas:
            try:
                items.append(_abrir_escaneo(r, inbox_res))
            except ValueError as exc:
                clave, _, detalle = str(exc).partition(":")
                problemas.setdefault(clave, []).append(detalle.strip())
        if problemas["NO_EXISTE"]:
            return self._err("ARCHIVOS_NO_ENCONTRADOS", f"No existen {len(problemas['NO_EXISTE'])} archivo(s): {problemas['NO_EXISTE'][:3]}", "Verificar rutas locales de las imágenes escaneadas.")
        if problemas["NO_LEGIBLE"]:
            return self._err("RUTA_NO_LEIBLE", f"{len(problemas['NO_LEGIBLE'])} ruta(s) no se pueden abrir: {problemas['NO_LEGIBLE'][:3]}", "Verificar permisos; si es un symlink final, se rechaza por diseño (O_NOFOLLOW).")
        if problemas["NO_ARCHIVO"]:
            return self._err("RUTA_NO_ES_ARCHIVO", f"{len(problemas['NO_ARCHIVO'])} ruta(s) no son archivos regulares: {problemas['NO_ARCHIVO'][:3]}", "Pasar solo archivos de imagen/PDF.")
        if problemas["HARDLINK"]:
            return self._err("HARDLINK_NO_PERMITIDO", f"{len(problemas['HARDLINK'])} archivo(s) con enlaces múltiples (hardlinks): {problemas['HARDLINK'][:3]}", "Copiar los escaneos como archivos nuevos dentro del inbox; los hardlinks se rechazan para evitar exfiltración por enlace.")
        if problemas["FUERA_DE_SCOPE"]:
            return self._err(
                "RUTA_FUERA_DE_SCOPE",
                f"{len(problemas['FUERA_DE_SCOPE'])} ruta(s) fuera del inbox del documento ({inbox}): {problemas['FUERA_DE_SCOPE'][:3]}",
                "Mover los escaneos a la carpeta inbox del documento antes de subirlos; no se permiten rutas externas.",
            )
        r = self._post_archivos_vista(f"/digitalizacion/procesar/{documento_id}/", items)
        if r.get("timeout"):
            return {
                "ok": False,
                "error_code": "TIMEOUT_ESTADO_DESCONOCIDO",
                "message": f"La subida excedió el tiempo límite ({r.get('reason', '')}). No se sabe si el servidor recibió todos los archivos.",
                "suggestion": f"NO reintentar a ciegas (duplica páginas). La API no expone inventario de inbox: comparar manualmente los archivos locales con el contenido real de {inbox} y re-subir SOLO los que falten.",
            }
        if r.get("http_error") or r.get("network_error"):
            return self._err("SUBIDA_FALLO", f"Falló la subida: {str(r)[:200]}", "Verificar sesión M360 activa y que los archivos sean legibles.")
        # Verificar por lectura (el POST a vista redirige; la verdad es el estado)
        doc2 = self._get(f"/api/v1/digitalizacion/documentos/{documento_id}/")
        if self._es_error_resp(doc2):
            return self._err(
                "VERIFICACION_FALLO",
                f"Subida reportada por el servidor pero no se pudo verificar el documento: {str(doc2)[:200]}",
                "Verificar manualmente el estado del documento antes de avanzar etapas.",
            )
        # Comparación directa (sin truthiness): si document_id viene vacío en
        # cualquiera de los dos lados, la comparación lo detecta en vez de
        # saltarse la verificación silenciosamente.
        if doc2.get("document_id") != doc.get("document_id"):
            return self._err("VERIFICACION_DISCREPANTE", "El documento devuelto no coincide con el enviado.", "Revisar sesión/estado en M360 y reintentar la verificación.")
        return {
            "ok": True,
            # Semántica honesta: la API no expone inventario de inbox, así que
            # "subida_reportada" = el servidor aceptó el POST y el documento
            # sigue leyéndose; NO es prueba de que las imágenes aterrizaron.
            "subida_reportada": True,
            "archivos": [nombre for _, nombre, _ in items],
            "inbox": doc2.get("ruta_inbox") or inbox,
            "advertencia": "Sin verificación de inventario (la API no lo expone): confirmar visualmente que las páginas quedaron en el inbox antes de avanzar etapas.",
            "siguiente_paso": f"Avanzar la etapa de digitalización con digi_avanzar_etapa(documento_id={documento_id}, etapa='digitalizacion').",
        }

    def avanzar_etapa(self, documento_id: int, etapa: str, avanzar_todas: bool = False) -> Dict[str, Any]:
        """Ejecuta/avanza una etapa del pipeline sobre un documento.

        Usar cuando las imágenes ya están en el inbox. Con avanzar_todas=False
        (default) ejecuta SOLO la etapa indicada; con True, la vista ejecuta
        el resto del pipeline en cascada (puede tardar minutos por OCR).

        Args:
            documento_id: ID del documento.
            etapa: Una de ETAPAS (preparacion, digitalizacion, qc1,
                preprocesamiento, metadatos, qc2, auditoria, fedatacion, certificado).
            avanzar_todas: ejecutar también las etapas siguientes en cascada.

        Returns:
            {ok, etapa, estado} o error estructurado.
        """
        if etapa not in self.ETAPAS:
            return self._err("ETAPA_INVALIDA", f"Etapa '{etapa}' no existe.", f"Usar una de: {self.ETAPAS}")
        r = self._post_form_vista(
            f"/digitalizacion/procesar/{documento_id}/",
            {"etapa": etapa, "avanzar": "1" if avanzar_todas else "0"},
            timeout=300,
        )
        if r.get("timeout"):
            return {
                "ok": False,
                "error_code": "TIMEOUT_ESTADO_DESCONOCIDO",
                "message": f"El POST de etapa excedió 300s ({r.get('reason', '')}); el servidor puede haber ejecutado (o seguir ejecutando) la etapa en cascada.",
                "suggestion": "NO reintentar a ciegas. Verificar el registro de etapas con digi_estado_lote (etapas_resumen) antes de reintentar; reintentar re-ejecuta la etapa.",
            }
        if r.get("http_error") or r.get("network_error"):
            return self._err("ETAPA_FALLO", f"Falló el avance de etapa: {str(r)[:200]}", "Verificar sesión M360 activa y el estado del documento.")
        doc = self._get(f"/api/v1/digitalizacion/documentos/{documento_id}/")
        if self._es_error_resp(doc):
            return self._err(
                "VERIFICACION_FALLO",
                f"Etapa '{etapa}' enviada pero no se pudo verificar el estado del documento: {str(doc)[:200]}",
                "Verificar con digi_estado_documento antes de continuar con la siguiente etapa.",
            )
        # Verificación real: el registro de etapas vive en el lote (etapas[]).
        # La API no expone endpoint por (documento, etapa): se trae el lote
        # completo (documentos + todas las etapas) para verificar UN registro.
        # Trade-off aceptado (no hay alternativa server-side); si el volumen
        # crece, verificar una vez por documento en vez de por etapa.
        # etapa_verificada: True=registrada ok | False=GET ok pero sin registro
        # | None=no se pudo leer el lote (NO confundir con False: la etapa
        # puede haberse ejecutado y el agente no debe reintentar).
        lote_id = doc.get("lote")
        etapa_verificada = None
        if isinstance(lote_id, int):
            lote = self._get(f"/api/v1/digitalizacion/lotes/{lote_id}/")
            if isinstance(lote, dict) and not self._es_error_resp(lote):
                etapa_verificada = any(
                    isinstance(e, dict)
                    and e.get("documento") == documento_id
                    and e.get("etapa") == etapa
                    and e.get("estado") == "ok"
                    for e in (lote.get("etapas") or [])
                )
        resp: Dict[str, Any] = {
            "ok": True,
            "documento_id": documento_id,
            "etapa": etapa,
            "verificado": etapa_verificada,
            "siguiente_paso": f"Verificar con digi_estado_documento(documento_id={documento_id}) y continuar con la siguiente etapa de: {self.ETAPAS}",
        }
        if etapa_verificada is False:
            resp["advertencia"] = f"No se encontró registro de etapa '{etapa}' con estado ok para el documento {documento_id}; revisar el lote antes de reintentar."
        elif etapa_verificada is None:
            resp["advertencia"] = "No se pudo leer el registro de etapas del lote (fallo de red/lectura): la etapa PUEDE haberse ejecutado. Verificar con digi_estado_lote antes de reintentar; reintentar re-ejecuta."
        return resp

    # ==================== READ (seguras) ====================

    def listar_lotes(self, max_total: int = 1000) -> Dict[str, Any]:
        """Lista lotes de digitalización (id, nombre, estado, productor).

        Usar para descubrir IDs de lotes antes de operar sobre ellos.
        max_total acota la ventana pedida al servidor. La API de
        digitalización devuelve listas peladas SIN meta de conteo (verificado
        2026-10-14), por lo que `truncated` solo puede detectar que la ventana
        volvió llena — un cap silencioso del servidor por debajo de max_total
        no es detectable: limitación conocida, documentada para el agente.
        """
        r = self.client._get_request(f"/api/v1/digitalizacion/lotes/?limit={max_total}")
        if self._es_error_resp(r):
            return {"ok": False, "error_code": "LISTAR_LOTES_FALLO", "message": str(r)[:200], "suggestion": "Verificar sesión M360 y reintentar."}
        data = self.client._unwrap_list(r)
        lotes = [
            {
                "id": l.get("id"),
                "nombre": l.get("nombre"),
                "estado": l.get("estado"),
                "productor": (l.get("metadata_proyecto") or {}).get("productor"),
                "ruta_base": l.get("ruta_base"),
                "created_at": l.get("created_at"),
                "documentos": l.get("documentos") and len(l["documentos"]) or 0,
            }
            for l in data
            if isinstance(l, dict)
        ]
        return {
            "ok": True,
            "total": len(lotes),
            "ventana": max_total,
            "truncated": len(data) >= max_total,
            "lotes": lotes,
        }

    def estado_lote(self, lote_id: int) -> Dict[str, Any]:
        """Estado de un lote: documentos, etapas por documento y folios."""
        lote = self._get(f"/api/v1/digitalizacion/lotes/{lote_id}/")
        if self._es_error_resp(lote):
            return self._err("LOTE_NO_ENCONTRADO", f"No se pudo leer el lote {lote_id}: {str(lote)[:200]}", "Verificar con digi_listar_lotes().")
        docs = lote.get("documentos") or []
        # Resumen de etapas por documento: hace verificable el estado del
        # pipeline desde esta tool (antes el docstring lo prometía pero la
        # respuesta no lo incluía, y la verificación de avanzar_etapa no era
        # ejecutable por el agente).
        etapas_por_doc: Dict[Any, List[Dict[str, Any]]] = {}
        for e in (lote.get("etapas") or []):
            if not isinstance(e, dict):
                continue
            doc_key = e.get("documento")
            if doc_key is None:
                continue
            etapas_por_doc.setdefault(doc_key, []).append(
                {"etapa": e.get("etapa"), "estado": e.get("estado"), "fin": e.get("fin")}
            )
        return {
            "ok": True,
            "lote": {"id": lote.get("id"), "nombre": lote.get("nombre"), "estado": lote.get("estado"), "ruta_base": lote.get("ruta_base")},
            "documentos": [
                {
                    "id": d.get("id"),
                    "document_id": d.get("document_id"),
                    "titulo": d.get("titulo"),
                    "tipo": d.get("tipo"),
                    "creator": d.get("creator"),
                    "fecha_documento": d.get("fecha_documento"),
                    "folios": d.get("folios"),
                    "checksum_sha256": d.get("checksum_sha256"),
                    "ocr_confidence": d.get("ocr_confidence"),
                    "ruta_acceso": d.get("ruta_acceso"),
                    "etapas": etapas_por_doc.get(d.get("id"), []),
                }
                for d in docs if isinstance(d, dict)
            ],
        }

    def estado_documento(self, documento_id: int) -> Dict[str, Any]:
        """Estado detallado de un documento (metadatos, checksum, OCR, rutas)."""
        doc = self._get(f"/api/v1/digitalizacion/documentos/{documento_id}/")
        if self._es_error_resp(doc):
            return self._err("DOCUMENTO_NO_ENCONTRADO", f"No se pudo leer el documento {documento_id}: {str(doc)[:200]}", "Verificar ID con digi_estado_lote().")
        campos = ["id", "document_id", "titulo", "tipo", "creator", "fecha_documento", "subject",
                  "checksum_sha256", "ocr_engine", "ocr_confidence", "ingest_mode",
                  "ruta_inbox", "ruta_preprocessed", "ruta_acceso", "ruta_master", "folios"]
        return {"ok": True, "documento": {k: doc.get(k) for k in campos}}

    def buscar_por_productor(self, productor: str, max_total: int = 1000) -> Dict[str, Any]:
        """Busca documentos digitalizados cuyo emisor (creator) coincida.

        Usar para verificar si un productor ya tiene respaldo documental
        antes de crear lotes duplicados. La búsqueda es client-side sobre una
        ventana de max_total documentos (la API ignora ?search= y devuelve
        listas peladas sin meta de conteo — verificado 2026-10-14), por lo que
        transfiere registros completos aunque solo se usen creator/titulo:
        trade-off aceptado hasta que la API soporte filtro/proyección
        server-side. Si vuelve llena, `truncated=True` advierte que pueden
        existir coincidencias fuera de la ventana (misma limitación conocida
        que digi_listar_lotes).
        """
        r = self.client._get_request(f"/api/v1/digitalizacion/documentos/?limit={max_total}")
        if self._es_error_resp(r):
            return {"ok": False, "error_code": "BUSCAR_FALLO", "message": str(r)[:200], "suggestion": "Verificar sesión M360 y reintentar."}
        data = self.client._unwrap_list(r)
        clave = _norm(productor)
        matches = [
            {"id": d.get("id"), "titulo": d.get("titulo"), "creator": d.get("creator"),
             "tipo": d.get("tipo"), "fecha_documento": d.get("fecha_documento"),
             "checksum_sha256": d.get("checksum_sha256"), "lote_id": d.get("lote")}
            for d in data
            if isinstance(d, dict) and clave and clave in _norm(str(d.get("creator") or "") + " " + str(d.get("titulo") or ""))
        ]
        resp: Dict[str, Any] = {"ok": True, "productor": productor, "escaneados": len(data), "ventana": max_total, "coincidencias": len(matches), "documentos": matches}
        if len(data) >= max_total:
            resp["truncated"] = True
            resp["advertencia"] = f"Ventana truncada en {max_total} documentos; pueden existir coincidencias fuera de ella."
        return resp

    # ==================== DELETE (destructivas, con guardas) ====================

    def _leer_o_error(self, path: str, etiqueta: str, sugerencia: str) -> Dict[str, Any]:
        """GET que distingue 404 auténtico de fallos transitorios/de ruta.

        Devuelve {"recurso": <dict>} o {"error": self._err(...)}. Nunca
        clasifica un corte de red como 'no encontrado'.
        """
        r = self._get(path)
        if _es_404_no_existe(r):
            return {"no_existe": True}
        if _es_fallo_transitorio(r):
            return {"error": self._err("LECTURA_FALLO", f"No se pudo leer {etiqueta} (fallo transitorio): {str(r)[:200]}", "Reintentar; si persiste, verificar sesión M360 (posible re-login).")}
        if self._es_error_resp(r):
            return {"error": self._err(f"{etiqueta.upper().replace(' ', '_')}_NO_ENCONTRADO", f"No se pudo leer {etiqueta}: {str(r)[:200]}", sugerencia)}
        return {"recurso": r}

    @staticmethod
    def _rutas_fisicas_persistentes(recurso: Dict[str, Any]) -> List[str]:
        """Rutas en disco que sobreviven al borrado DB-only (DRF destroy).

        La app M360 tiene una vista propia que SÍ limpia filesystem; el DELETE
        de la API borra solo filas. Se enumeran para que el operador limpie.
        """
        claves = ("ruta_inbox", "ruta_preprocessed", "ruta_master", "ruta_acceso")
        return [str(recurso.get(k)) for k in claves if (recurso.get(k) or "").strip()]

    def eliminar_documento(self, documento_id: int, confirmar: bool = False, forzar: bool = False, motivo: str = "") -> Dict[str, Any]:
        """Elimina un documento digitalizado. OPERACIÓN DESTRUCTIVA IRREVERSIBLE.

        Sin `confirmar=True` NO borra: devuelve previsualización. Guardas:
        - documento en lote certificado exige `forzar=True` + `motivo` (la
          protección de eliminar_lote no cubre el borrado documento a documento).
        - rechaza si el documento tiene etapas en vuelo (fin IS NULL).
        - advierte que el borrado es DB-only: los archivos físicos persisten.
        """
        if not isinstance(documento_id, int):
            return self._err("ID_INVALIDO", f"documento_id debe ser int, recibido {type(documento_id).__name__}.", "Pasar el ID numérico del documento.")
        lec = self._leer_o_error(f"/api/v1/digitalizacion/documentos/{documento_id}/", "documento", "Verificar ID con digi_estado_lote().")
        if "error" in lec:
            return lec["error"]
        if lec.get("no_existe"):
            return {"ok": True, "documento_id": documento_id, "ya_no_existia": True, "message": "El documento ya estaba eliminado."}
        doc = lec["recurso"]
        lote_id = doc.get("lote")
        estado_lote = None
        etapas_en_vuelo = []
        if isinstance(lote_id, int):
            lec_lote = self._leer_o_error(f"/api/v1/digitalizacion/lotes/{lote_id}/", "lote del documento", "Verificar el lote con digi_listar_lotes().")
            if "error" in lec_lote:
                return lec_lote["error"]
            if not lec_lote.get("no_existe"):
                lote = lec_lote["recurso"]
                estado_lote = lote.get("estado")
                etapas_en_vuelo = [
                    e.get("etapa") for e in (lote.get("etapas") or [])
                    if isinstance(e, dict) and e.get("documento") == documento_id and not e.get("fin")
                ]
        if estado_lote == "certificado" and not forzar:
            return {
                "ok": False,
                "requiere_confirmacion": True,
                "requiere_forzado": True,
                "documento_id": documento_id,
                "document_id": doc.get("document_id"),
                "titulo": doc.get("titulo"),
                "lote_id": lote_id,
                "estado_lote": estado_lote,
                "suggestion": "El documento pertenece a un lote CERTIFICADO (archivo legal). Requiere forzar=True y motivo explícito para borrarlo.",
            }
        if estado_lote == "certificado" and not (motivo or "").strip():
            return self._err("MOTIVO_REQUERIDO", "Borrar documentos de un lote certificado exige motivo.", "Pasar motivo (quién lo solicita y por qué) junto con forzar=True.")
        if etapas_en_vuelo:
            return self._err(
                "ETAPAS_EN_PROGRESO",
                f"El documento {documento_id} tiene etapas en vuelo: {etapas_en_vuelo}. Borrar ahora puede corromper el pipeline.",
                "Esperar a que las etapas terminen (fin registrado) o cancelar el procesamiento antes de borrar.",
            )
        rutas = self._rutas_fisicas_persistentes(doc)
        previsualizacion: Dict[str, Any] = {
            "ok": False,
            "requiere_confirmacion": True,
            "documento_id": documento_id,
            "document_id": doc.get("document_id"),
            "titulo": doc.get("titulo"),
            "creator": doc.get("creator"),
            "lote_id": lote_id,
            "estado_lote": estado_lote,
            "suggestion": "Repetir con confirmar=True tras verificar que el documento es basura/duplicado. El borrado es irreversible y en producción.",
        }
        if rutas:
            previsualizacion["advertencia_filesystem"] = (
                "El borrado elimina solo el registro: estos archivos físicos PERSISTEN en el servidor y requieren limpieza manual: "
                + ", ".join(rutas)
            )
        if not confirmar:
            return previsualizacion
        r = self.client.api_v1_delete_document(documento_id)
        if self._es_error_resp(r):
            return self._err("ELIMINAR_DOCUMENTO_FALLO", f"DELETE rechazado: {str(r)[:200]}", "Verificar permisos de sesión M360.")
        verif = self._get(f"/api/v1/digitalizacion/documentos/{documento_id}/")
        if _es_404_no_existe(verif):
            resp: Dict[str, Any] = {"ok": True, "eliminado": True, "documento_id": documento_id, "document_id": doc.get("document_id"), "message": "Registro eliminado (verificado por 404 posterior)."}
            if motivo:
                resp["motivo"] = motivo
            if rutas:
                resp["advertencia_filesystem"] = "Archivos físicos aún presentes en el servidor (limpieza manual pendiente): " + ", ".join(rutas)
            return resp
        return self._err(
            "ELIMINAR_NO_CONFIRMADO",
            f"DELETE devolvió éxito pero el documento {documento_id} aún responde: {str(verif)[:150]}",
            "Verificar manualmente el estado del documento.",
        )

    def eliminar_lote(self, lote_id: int, confirmar: bool = False, forzar: bool = False, motivo: str = "") -> Dict[str, Any]:
        """Elimina un lote completo (CASCADA: documentos + etapas).

        OPERACIÓN DESTRUCTIVA IRREVERSIBLE. Sin `confirmar=True` no borra:
        devuelve previsualización con el conteo de documentos afectados. Un
        lote certificado exige `forzar=True` + `motivo`. Rechaza etapas en
        vuelo. Advierte que el borrado es DB-only (archivos persisten).
        """
        if not isinstance(lote_id, int):
            return self._err("ID_INVALIDO", f"lote_id debe ser int, recibido {type(lote_id).__name__}.", "Pasar el ID numérico del lote.")
        lec = self._leer_o_error(f"/api/v1/digitalizacion/lotes/{lote_id}/", "lote", "Verificar con digi_listar_lotes().")
        if "error" in lec:
            return lec["error"]
        if lec.get("no_existe"):
            return {"ok": True, "lote_id": lote_id, "ya_no_existia": True, "message": "El lote ya estaba eliminado."}
        lote = lec["recurso"]
        docs = [d for d in (lote.get("documentos") or []) if isinstance(d, dict)]
        estado = lote.get("estado")
        if estado == "certificado" and not forzar:
            return {
                "ok": False,
                "requiere_confirmacion": True,
                "requiere_forzado": True,
                "lote_id": lote_id,
                "nombre": lote.get("nombre"),
                "estado": estado,
                "documentos_afectados": len(docs),
                "etapas_registradas": len(lote.get("etapas") or []),
                "suggestion": "El lote está CERTIFICADO (documentos con valor de archivo/legal). Requiere forzar=True y motivo explícito para borrarlo.",
            }
        if estado == "certificado" and not (motivo or "").strip():
            return self._err("MOTIVO_REQUERIDO", "Borrar un lote certificado exige motivo.", "Pasar motivo (quién lo solicita y por qué) junto con forzar=True.")
        en_vuelo = [e.get("etapa") for e in (lote.get("etapas") or []) if isinstance(e, dict) and not e.get("fin")]
        if en_vuelo:
            return self._err(
                "ETAPAS_EN_PROGRESO",
                f"El lote {lote_id} tiene etapas en vuelo: {sorted(set(en_vuelo))}. Borrar ahora puede corromper el pipeline.",
                "Esperar a que las etapas terminen (fin registrado) antes de borrar el lote.",
            )
        rutas: List[str] = []
        for d in docs:
            rutas.extend(self._rutas_fisicas_persistentes(d))
        previsualizacion: Dict[str, Any] = {
            "ok": False,
            "requiere_confirmacion": True,
            "lote_id": lote_id,
            "nombre": lote.get("nombre"),
            "estado": estado,
            "documentos_afectados": len(docs),
            "etapas_registradas": len(lote.get("etapas") or []),
            "documentos": [{"id": d.get("id"), "document_id": d.get("document_id"), "titulo": d.get("titulo")} for d in docs],
            "suggestion": "Repetir con confirmar=True tras verificar. El borrado del lote elimina EN CASCADA todos sus documentos y etapas.",
        }
        if rutas:
            previsualizacion["advertencia_filesystem"] = (
                "El borrado elimina solo registros: estos archivos físicos PERSISTEN en el servidor y requieren limpieza manual: "
                + ", ".join(rutas[:10]) + (" …" if len(rutas) > 10 else "")
            )
        if not confirmar:
            return previsualizacion
        r = self.client.api_v1_delete_lote(lote_id, forzar=True)
        if self._es_error_resp(r):
            return self._err("ELIMINAR_LOTE_FALLO", f"DELETE rechazado: {str(r)[:200]}", "Verificar permisos de sesión M360.")
        verif = self._get(f"/api/v1/digitalizacion/lotes/{lote_id}/")
        if _es_404_no_existe(verif):
            resp: Dict[str, Any] = {"ok": True, "eliminado": True, "lote_id": lote_id, "nombre": lote.get("nombre"), "documentos_eliminados": len(docs), "message": "Lote y cascada eliminados (verificado por 404 posterior)."}
            if motivo:
                resp["motivo"] = motivo
            if rutas:
                resp["advertencia_filesystem"] = "Archivos físicos aún presentes en el servidor (limpieza manual pendiente): " + ", ".join(rutas[:10]) + (" …" if len(rutas) > 10 else "")
            return resp
        return self._err(
            "ELIMINAR_NO_CONFIRMADO",
            f"DELETE devolvió éxito pero el lote {lote_id} aún responde: {str(verif)[:150]}",
            "Verificar manualmente el estado del lote.",
        )

    # ==================== Especificación para LLM ====================

    def tool_definitions(self) -> List[Dict[str, Any]]:
        """Esquemas de herramientas para function-calling (OpenAI/Anthropic)."""
        common_err = "En caso de error devuelve {error_code, message, suggestion}."
        return [
            {
                "type": "function",
                "function": {
                    "name": "digi_crear_lote_escaneo",
                    "description": (
                        "Crea un lote de digitalización por procedimiento de ESCANEO (documentos físicos) "
                        "para un productor (empresa emisora). NO usar para archivos ya digitales. "
                        "Crea el lote sin ruta_fuente; las imágenes se suben después. "
                        + common_err
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "productor": {"type": "string", "description": "Empresa emisora, leída del documento físico"},
                            "ruta_base": {"type": "string", "description": "Carpeta raíz de trabajo del pipeline (debe existir)"},
                            "titular": {"type": "string", "description": "Titular del archivo personal"},
                            "finalidad": {"type": "string", "description": "Motivo de la digitalización"},
                            "proyecto_destino": {"type": "string", "description": "Proyecto memento destino"},
                            "m360_proyecto_id": {"type": "integer", "description": "ID del proyecto M360 destino"},
                        },
                        "required": ["productor", "ruta_base"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_crear_documento",
                    "description": (
                        "Cataloga un documento dentro de un lote de escaneo. "
                        "Usar tras crear el lote y antes de subir imágenes. "
                        "El tipo documental sale del documento físico (certificado, contrato, liquidación, comunicación). "
                        + common_err
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lote_id": {"type": "integer", "description": "ID del lote"},
                            "tipo": {"type": "string", "description": "Tipo documental real, ej. 'certificado', 'contrato', 'liquidacion'"},
                            "titulo": {"type": "string", "description": "Título descriptivo del documento"},
                            "productor": {"type": "string", "description": "Empresa emisora (campo creator)"},
                            "fecha_documento": {"type": "string", "format": "date", "description": "Fecha de emisión impresa. DEBE ser ISO 8601 estricto YYYY-MM-DD (se valida; otro formato se rechaza)"},
                            "folios": {"type": "integer", "description": "Número de páginas del físico"},
                            "subject": {"type": "array", "items": {"type": "string"}, "description": "Etiquetas; default [tipo, productor]"},
                        },
                        "required": ["lote_id", "tipo", "titulo", "productor"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_subir_imagenes_escaneo",
                    "description": (
                        "Sube las imágenes escaneadas al inbox del documento (van a <ruta_base>/inbox/<document_id>/). "
                        "Usar tras crear el documento y antes de avanzar etapas. "
                        "Las rutas locales DEBEN estar dentro de la carpeta inbox del documento; "
                        "rutas externas o symlinks que apunten fuera se rechazan. " + common_err
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "documento_id": {"type": "integer"},
                            "rutas": {"type": "array", "items": {"type": "string"}, "description": "Rutas locales de imágenes/PDF, dentro del inbox del documento"},
                        },
                        "required": ["documento_id", "rutas"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_avanzar_etapa",
                    "description": (
                        "Ejecuta/avanza una etapa del pipeline sobre un documento. "
                        "Usar cuando las imágenes ya están en el inbox. "
                        f"Etapas válidas: {self.ETAPAS}. " + common_err
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "documento_id": {"type": "integer"},
                            "etapa": {"type": "string", "enum": self.ETAPAS},
                        },
                        "required": ["documento_id", "etapa"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                "name": "digi_listar_lotes",
                "description": "Lista lotes existentes (id, nombre, estado, productor). Usar para descubrir IDs antes de operar.",
                "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_estado_lote",
                    "description": "Estado de un lote con sus documentos (checksum, OCR, rutas).",
                    "parameters": {"type": "object", "properties": {"lote_id": {"type": "integer"}}, "required": ["lote_id"]},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_estado_documento",
                    "description": "Estado detallado de un documento (metadatos, checksum, OCR, rutas por etapa).",
                    "parameters": {"type": "object", "properties": {"documento_id": {"type": "integer"}}, "required": ["documento_id"]},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_buscar_por_productor",
                    "description": (
                        "Busca documentos digitalizados por empresa emisora (creator). "
                        "Usar ANTES de crear un lote para no duplicar respaldo existente."
                    ),
                    "parameters": {"type": "object", "properties": {"productor": {"type": "string"}}, "required": ["productor"]},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_eliminar_documento",
                    "description": (
                        "DESTRUCTIVA: elimina un documento digitalizado (irreversible). Sin confirmar=true solo previsualiza "
                        "(no borra). Si el documento pertenece a un lote CERTIFICADO exige forzar=true + motivo. "
                        "Rechaza borrar si el documento tiene etapas en vuelo. Advierte que los archivos físicos "
                        "persisten en el servidor (borrado DB-only)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "documento_id": {"type": "integer"},
                            "confirmar": {"type": "boolean", "description": "true para ejecutar el borrado real; false/omitido = solo previsualización"},
                            "forzar": {"type": "boolean", "description": "true para permitir borrar documentos de lotes certificados (requiere motivo)"},
                            "motivo": {"type": "string", "description": "Obligatorio con forzar=true: quién solicita el borrado y por qué (auditoría)"},
                        },
                        "required": ["documento_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "digi_eliminar_lote",
                    "description": (
                        "DESTRUCTIVA: elimina un lote completo EN CASCADA (todos sus documentos y etapas; irreversible). "
                        "Sin confirmar=true solo previsualiza. Lotes certificados exigen forzar=true + motivo. "
                        "Rechaza borrar si hay etapas en vuelo. Advierte que los archivos físicos persisten en el servidor."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lote_id": {"type": "integer"},
                            "confirmar": {"type": "boolean", "description": "true para ejecutar el borrado real; false/omitido = solo previsualización"},
                            "forzar": {"type": "boolean", "description": "true para permitir borrar un lote certificado (requiere motivo)"},
                            "motivo": {"type": "string", "description": "Obligatorio con forzar=true: quién solicita el borrado y por qué (auditoría)"},
                        },
                        "required": ["lote_id"],
                    },
                },
            },
        ]

    # ==================== Helper mapping nombre→método ====================

    def _coaccionar_bools(self, fn: Any, args: Dict[str, Any]):
        """Coerciona args declarados booleanos en la firma de `fn`.

        Un LLM puede emitir "confirmar": "false" (string): con truthiness
        eso EJECUTA el borrado irreversible. Se aceptan bool real,
        "true"/"false" (case-insensitive) y 1/0; cualquier otro valor en un
        parámetro booleano es error, no borrado accidental.
        """
        import inspect
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return args, None
        out = dict(args or {})
        for nombre, param in sig.parameters.items():
            if nombre not in out:
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if param.default is inspect.Parameter.empty or not isinstance(param.default, bool):
                continue
            v = out[nombre]
            if isinstance(v, bool):
                continue
            if v in (1, 0) or (isinstance(v, str) and v.strip().lower() in ("true", "false")):
                out[nombre] = str(v).strip().lower() in ("true", "1")
            else:
                return None, self._err("ARG_BOOL_INVALIDO", f"El parámetro booleano '{nombre}' debe ser true/false, recibido {v!r}.", "Enviar un booleano JSON verdadero; no strings ni otros valores.")
        return out, None

    def ejecutar(self, nombre: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Despacha una tool por nombre (para el loop del agente)."""
        mapa = {
            "digi_crear_lote_escaneo": self.crear_lote_escaneo,
            "digi_crear_documento": self.crear_documento,
            "digi_subir_imagenes_escaneo": self.subir_imagenes_escaneo,
            "digi_avanzar_etapa": self.avanzar_etapa,
            "digi_listar_lotes": self.listar_lotes,
            "digi_estado_lote": self.estado_lote,
            "digi_estado_documento": self.estado_documento,
            "digi_buscar_por_productor": self.buscar_por_productor,
            "digi_eliminar_documento": self.eliminar_documento,
            "digi_eliminar_lote": self.eliminar_lote,
        }
        fn = mapa.get(nombre)
        if not fn:
            return self._err("TOOL_DESCONOCIDA", f"'{nombre}' no existe.", f"Tools disponibles: {sorted(mapa)}")
        args, error = self._coaccionar_bools(fn, args or {})
        if error:
            return error
        try:
            return fn(**{k: v for k, v in args.items() if k in fn.__code__.co_varnames})
        except TypeError as exc:
            return self._err("ARGS_INVALIDOS", str(exc), "Revisar nombres de parámetros contra el schema.")
        except ValueError as exc:
            return self._err("ARGS_INVALIDOS", str(exc), "Revisar formato de los valores (p.ej. fecha ISO 8601).")

    # ==================== Internos ====================

    def _get(self, path: str) -> Any:
        try:
            return self.client._get_request(path)
        except Exception as exc:  # noqa: BLE001
            return {"network_error": str(exc)}

    def _err(self, code: str, message: str, suggestion: str) -> Dict[str, Any]:
        return {"ok": False, "error_code": code, "message": message, "suggestion": suggestion}

    def _es_error_resp(self, resp: Any) -> bool:
        """True si la respuesta del cliente es un dict de error estándar.

        Única fuente del set de claves de error (http_error/network_error/
        timeout): antes estaba replicado en 9 guards con copias divergentes
        (una ya omitía timeout). Cualquier clave nueva se añade aquí solo.

        Las listas peladas NO son error: los endpoints de digitalización
        devuelven listas directamente (verificado en vivo 2026-10-14) y
        _unwrap_list las acepta; clasificarlas como error rompería
        listar_lotes/buscar_por_productor.
        """
        if isinstance(resp, list):
            return False
        return (
            not isinstance(resp, dict)
            or bool(resp.get("http_error"))
            or bool(resp.get("network_error"))
            or bool(resp.get("timeout"))
        )

    def _post_archivos_vista(self, path: str, items: List[Any], timeout: int = 120) -> Dict[str, Any]:
        """POST multipart a una vista Django con sesión+CSRF del cliente.

        `items`: lista de (fd, nombre, ctype) ya validados por _abrir_escaneo
        (fds abiertos). El cuerpo se transmite como stream (un archivo
        residente a la vez) con Content-Length calculado desde fstat(fd): leer
        todo el lote a memoria provocaba picos de ~2x el tamaño del batch.
        Los fds se cierran siempre al terminar (éxito o error).
        """
        boundary = f"----DigiTool{uuid.uuid4().hex}"
        # Fuente ÚNICA del layout multipart: CAMPOS y CIERRE se usan tanto para
        # calcular Content-Length como para generar el stream, así que no pueden
        # divergir (antes el tuple y el cierre estaban escritos dos veces).
        campos = (("etapa", "preparacion"), ("avanzar", "0"))
        cierre = f"--{boundary}--\r\n".encode()

        def _parte_campo(field: str, value: str) -> bytes:
            return f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n".encode()

        def _parte_archivo_header(nombre: str, ctype: str) -> bytes:
            nombre_seguro = re.sub(r'["\r\n]', "_", nombre)
            return (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"inbox_files\"; "
                f"filename=\"{nombre_seguro}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
            )

        try:
            tamano = sum(len(_parte_campo(f, v)) for f, v in campos) + len(cierre)
            for fd, nombre, ctype in items:
                tamano += len(_parte_archivo_header(nombre, ctype)) + os.fstat(fd).st_size + 2

            def _cuerpo():
                for field, value in campos:
                    yield _parte_campo(field, value)
                for fd, nombre, ctype in items:
                    yield _parte_archivo_header(nombre, ctype)
                    anunciado = os.fstat(fd).st_size
                    enviados = 0
                    while enviados < anunciado:
                        bloque = os.read(fd, min(1024 * 1024, anunciado - enviados))
                        if not bloque:
                            raise ArchivoModificado(f"{nombre}: truncado durante la lectura ({enviados}/{anunciado} bytes)")
                        enviados += len(bloque)
                        yield bloque
                    if os.read(fd, 1):
                        raise ArchivoModificado(f"{nombre}: creció durante la lectura (> {anunciado} bytes)")
                    yield b"\r\n"
                yield cierre

            return self.client._post_vista(
                path,
                _cuerpo(),
                f"multipart/form-data; boundary={boundary}",
                timeout=timeout,
                content_length=tamano,
            )
        finally:
            for fd, _, _ in items:
                try:
                    os.close(fd)
                except OSError:
                    pass

    def _post_form_vista(self, path: str, campos: Dict[str, str], timeout: int = 300) -> Dict[str, Any]:
        """POST form-urlencoded a una vista Django con sesión+CSRF."""
        import urllib.parse

        data = urllib.parse.urlencode(campos).encode()
        return self.client._post_vista(path, data, "application/x-www-form-urlencoded", timeout=timeout)

