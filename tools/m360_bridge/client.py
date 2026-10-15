"""Cliente HTTP para M360 — autenticacion y operaciones CRUD."""
from __future__ import annotations

import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


class M360Client:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._timeout = int(os.environ.get("M360_TIMEOUT", "10"))
        self._api_key = os.environ.get("M360_API_KEY")
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._jar))
        self._csrf: Optional[str] = None
        self._session_user: Optional[Dict[str, Any]] = None

    def _init_session(self) -> None:
        csrf_url = f"{self.base_url}/api/csrf/"
        req = urllib.request.Request(csrf_url, method="GET")
        with self._opener.open(req, timeout=self._timeout) as resp:
            # M360 devuelve el token en el header X-Csrftoken (body puede venir vacío {}).
            header_csrf = resp.headers.get("X-Csrftoken") or resp.headers.get("X-CSRFToken")
            if header_csrf:
                self._csrf = header_csrf
            else:
                for c in self._jar:
                    if c.name == "csrftoken":
                        self._csrf = c.value
                        break
        login_url = f"{self.base_url}/api/login/"
        payload = json.dumps({"username": self.username, "password": self.password}).encode("utf-8")
        req = urllib.request.Request(login_url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Referer", self.base_url)
        if self._csrf:
            req.add_header("X-CSRFToken", self._csrf)
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                try:
                    body = json.loads(resp.read().decode("utf-8", errors="replace"))
                    self._session_user = body
                except Exception:
                    self._session_user = {"ok": True}
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Login failed: {exc.code} {exc.reason}") from exc
        # Refrescar CSRF post-login por rotación en Django.
        self._csrf = next((c.value for c in self._jar if c.name == "csrftoken"), self._csrf)

    def _current_csrf(self) -> Optional[str]:
        return next((c.value for c in self._jar if c.name == "csrftoken"), self._csrf)

    def _current_user_id(self) -> Optional[int]:
        if isinstance(self._session_user, dict):
            user = self._session_user.get("user") or {}
            user_id = user.get("id")
            if user_id is not None:
                try:
                    return int(user_id)
                except (TypeError, ValueError):
                    return None
        return None

    def _default_project_context(self) -> Dict[str, Any]:
        if hasattr(self, "_cached_project_context"):
            return self._cached_project_context
        if self._csrf is None:
            self._init_session()
        resp = self.api_v1_list_projects(limit=1)
        if not isinstance(resp, dict) or resp.get("http_error") or resp.get("network_error"):
            return {}
        data = resp.get("data") or []
        if not data:
            return {}
        item = data[0]
        ctx = {
            "project_status_id": (item.get("project_status") or {}).get("id"),
            "host_id": (item.get("host") or {}).get("id"),
            "assigned_to_id": (item.get("assigned_to") or {}).get("id"),
        }
        self._cached_project_context = ctx
        return ctx

    def _request(self, path: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST") -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if self._csrf is None:
            self._init_session()
        payload = dict(payload or {})
        csrf = self._current_csrf()
        encoded = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Referer", f"{self.base_url}{path}")
        if csrf:
            req.add_header("X-CSRFToken", csrf)
        if self._api_key and method in {"POST", "PATCH", "PUT", "DELETE"}:
            req.add_header("Authorization", f"Bearer {self._api_key}")
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                final_url = resp.geturl()
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    result = {"raw": body[:500], "status": resp.status, "final_url": final_url}
                    if resp.status == 200 and body.lstrip().startswith("<!DOCTYPE html>"):
                        lower = body.lower()
                        if "errorlist" in lower or "this field is required" in lower or "log in" in lower:
                            result["ok"] = False
                        elif "/panel/" in final_url or "/detail/" in final_url:
                            result["ok"] = True
                        elif "management360 platform description" in lower:
                            result["ok"] = False
                        else:
                            result["ok"] = True
                    return result
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:500]}
            result = {"http_error": exc.code, "reason": str(exc), **parsed}
            if exc.code in (301, 302, 303, 307, 308) and "Location" in exc.headers:
                result["redirect"] = exc.headers["Location"]
                result["ok"] = True
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"network_error": str(exc)}

    def _get_request(self, path: str, _retry: bool = False) -> Dict[str, Any]:
        if self._csrf is None:
            self._init_session()
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Referer", self.base_url)
        csrf = self._current_csrf()
        if csrf:
            req.add_header("X-CSRFToken", csrf)
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                final_url = resp.geturl()
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    result = {"raw": body[:500], "status": resp.status, "final_url": final_url}
                    if resp.status == 200 and body.lstrip().startswith("<!DOCTYPE html>"):
                        lower = body.lower()
                        if "errorlist" in lower or "this field is required" in lower or "log in" in lower:
                            result["ok"] = False
                        elif "/panel/" in final_url or "/detail/" in final_url:
                            result["ok"] = True
                        elif "management360 platform description" in lower:
                            result["ok"] = False
                        else:
                            result["ok"] = True
                    return result
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:500]}
            result = {"http_error": exc.code, "reason": str(exc), **parsed}
            if exc.code in (301, 302, 303, 307, 308) and "Location" in exc.headers:
                result["redirect"] = exc.headers["Location"]
                result["ok"] = True
            if exc.code in (401, 403) and not _retry:
                self._csrf = None
                self._session_user = None
                self._init_session()
                return self._get_request(path, _retry=True)
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"network_error": str(exc)}

    def _unwrap_list(self, resp: Any) -> List[Any]:
        """Desenvuelve respuestas de lista de la API v1 (data/results/items)."""
        if isinstance(resp, list):
            return resp
        if isinstance(resp, dict):
            for key in ("data", "results", "items"):
                value = resp.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _post_vista(
        self,
        path: str,
        data: Any,
        content_type: str,
        timeout: int = 120,
        content_length: Optional[int] = None,
        _retry: bool = False,
    ) -> Dict[str, Any]:
        """POST a una vista Django con sesión+CSRF del cliente.

        A diferencia de _request_json, apunta a vistas de la app (no a /api/v1):
        acepta `data` como bytes o como iterable de bytes (streaming; en ese
        caso el llamador DEBE fijar content_length). Nunca lanza excepciones:
        devuelve {"ok", "status", "final_url"} o un dict de error estándar
        {"http_error"|"network_error"|"timeout": ...}.

        NO envía Authorization Bearer: las vistas de app se autentican por
        cookie de sesión (+CSRF), y urllib reenviaría ese header en redirects
        a cualquier host (fuga de credencial cross-origen). Detecta respuestas
        de login/form-error aunque el status sea 200 y la URL no contenga
        "login" (fail-closed, no asume éxito).
        """
        import socket

        url = f"{self.base_url}{path}"
        if self._csrf is None:
            self._init_session()
        csrf = self._current_csrf()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", content_type)
        req.add_header("Referer", url)
        if content_length is not None:
            req.add_header("Content-Length", str(content_length))
        if csrf:
            req.add_header("X-CSRFToken", csrf)
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                final_url = resp.geturl()
                body = resp.read().decode("utf-8", errors="replace")
                body_lower = body.lower()
                login_markers = (
                    'type="password"',
                    "errorlist",
                    "this field is required",
                )
                if "login" in final_url or any(m in body_lower for m in login_markers):
                    return {
                        "http_error": resp.status,
                        "reason": f"respuesta de login/error en {final_url}",
                        "body": body[:500],
                    }
                return {"ok": True, "status": resp.status, "final_url": final_url}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:500]}
            result = {"http_error": exc.code, "reason": str(exc), **parsed}
            # Re-auth solo con cuerpo en memoria: un generador de stream ya se
            # consumió y el reintento enviaría un body vacío/parcial (fail-closed
            # en ese caso: se devuelve el error para que el llamador gestione).
            if exc.code in (401, 403) and not _retry and isinstance(data, (bytes, bytearray)):
                self._csrf = None
                self._session_user = None
                self._init_session()
                return self._post_vista(path, data, content_type, timeout, content_length, _retry=True)
            return result
        except TimeoutError as exc:
            return {"timeout": True, "reason": f"timeout tras {timeout}s: {exc}"}
        except urllib.error.URLError as exc:
            if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
                return {"timeout": True, "reason": f"timeout tras {timeout}s: {exc.reason}"}
            return {"network_error": str(exc)}
        except OSError as exc:
            return {"network_error": str(exc)}

    def _request_json(self, path: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST", _retry: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if self._csrf is None:
            self._init_session()
        payload = dict(payload or {})
        csrf = self._current_csrf()
        encoded = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Referer", self.base_url)
        if csrf:
            req.add_header("X-CSRFToken", csrf)
        if self._api_key and method in {"POST", "PATCH", "PUT", "DELETE"}:
            req.add_header("Authorization", f"Bearer {self._api_key}")
        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"raw": body[:500], "status": resp.status}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:500]}
            result = {"http_error": exc.code, "reason": str(exc), **parsed}
            if exc.code in (301, 302, 303, 307, 308) and "Location" in exc.headers:
                result["redirect"] = exc.headers["Location"]
                result["ok"] = True
            if exc.code in (401, 403) and not _retry:
                self._csrf = None
                self._session_user = None
                self._init_session()
                return self._request_json(path, payload, method, _retry=True)
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"network_error": str(exc)}

    def ping(self) -> Dict[str, Any]:
        return self._get_request("/api/health/")

    def create_event(
        self,
        title: str,
        start_date: str,
        end_date: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "description": kwargs.get("description", ""),
            "event_status": kwargs.get("event_status", 1),
            "event_category": kwargs.get("event_category", ""),
            "venue": kwargs.get("venue", ""),
            "max_attendees": kwargs.get("max_attendees", 0),
            "ticket_price": kwargs.get("ticket_price", 0),
            "assigned_to": kwargs.get("assigned_to", 1),
        }
        if kwargs.get("attendees"):
            payload["attendees"] = kwargs["attendees"]
        return self._request("/events/events/create/", payload)

    def create_project(
        self,
        name: str,
        description: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": name,
            "description": description,
            "project_status": kwargs.get("project_status", 2),
            "assigned_to": kwargs.get("assigned_to", 1),
            "ticket_price": kwargs.get("ticket_price", 0.07),
        }
        if kwargs.get("event"):
            payload["event"] = kwargs["event"]
        return self._request("/events/projects/create/", payload)

    def create_task(
        self,
        title: str,
        project_id: int,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "description": kwargs.get("description", ""),
            "important": kwargs.get("important", False),
            "project": project_id,
            "assigned_to": kwargs.get("assigned_to", 1),
            "ticket_price": kwargs.get("ticket_price", 0),
        }
        if kwargs.get("task_status"):
            payload["task_status"] = kwargs["task_status"]
        if kwargs.get("event"):
            payload["event"] = kwargs["event"]
        return self._request("/events/tasks/create/", payload)

    def update_task_status(self, task_id: int, status: str) -> Dict[str, Any]:
        return self._request(f"/events/tasks/{task_id}/status/", {"status": status})

    def create_inbox_item(self, title: str, description: str = "", created_by: str = "mementobloom") -> Dict[str, Any]:
        return self._request("/events/inbox/create/", {"title": title, "description": description, "created_by": created_by})

    def process_inbox_item(self, item_id: int, action: str) -> Dict[str, Any]:
        return self._request(f"/events/inbox/process/{item_id}/", {"action": action})

    def create_reminder(self, remind_at: str, task_id: Optional[int] = None, project_id: Optional[int] = None, reminder_type: str = "task") -> Dict[str, Any]:
        payload: Dict[str, Any] = {"remind_at": remind_at, "reminder_type": reminder_type}
        if task_id is not None:
            payload["task_id"] = task_id
        if project_id is not None:
            payload["project_id"] = project_id
        return self._request("/events/reminders/create/", payload)

    def create_dependency(self, task_id: int, depends_on: int, dependency_type: str = "blocks") -> Dict[str, Any]:
        return self._request(f"/events/dependencies/create/{task_id}/", {"depends_on": depends_on, "dependency_type": dependency_type})

    def get_kanban(self) -> Dict[str, Any]:
        return self._get_request("/events/kanban/")

    def get_inbox_stats(self) -> Dict[str, Any]:
        return self._get_request("/events/inbox/api/stats/")

    def logout(self) -> None:
        try:
            self._request("/api/logout/", method="GET")
        except Exception:
            pass
        self._cookie = None
        self._csrf = None
        self._session_user = None

    # API v1 (generic /api/v1/) ---

    def api_v1_health(self) -> Dict[str, Any]:
        return self._get_request("/api/v1/health/")

    def api_v1_list_projects(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/projects/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_get_project(self, project_id: int) -> Dict[str, Any]:
        return self._get_request(f"/api/v1/projects/{project_id}/")

    def api_v1_create_project(self, title: str, description: str = "", **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "project_status_id": kwargs.get("project_status_id", 1),
            "host_id": kwargs.get("host_id", self._current_user_id() or 1),
            "assigned_to_id": kwargs.get("assigned_to_id", self._current_user_id() or 1),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request_json("/api/v1/projects/", payload, method="POST")

    def api_v1_list_tasks(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/tasks/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_get_task(self, task_id: int) -> Dict[str, Any]:
        return self._get_request(f"/api/v1/tasks/{task_id}/")

    def api_v1_create_task(self, title: str, project_id: int, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "project_id": project_id,
            "task_status_id": kwargs.get("task_status", 1),
            "host_id": kwargs.get("host", self._current_user_id() or 1),
            "assigned_to_id": kwargs.get("assigned_to", self._current_user_id() or 1),
        }
        for optional, value in [
            ("description", kwargs.get("description", "")),
            ("important", kwargs.get("important", False)),
            ("ticket_price", kwargs.get("ticket_price", 0)),
        ]:
            if value not in (None, ""):
                payload[optional] = value
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request_json("/api/v1/tasks/", payload, method="POST")

    def api_v1_update_task_status(self, task_id: int, status: str) -> Dict[str, Any]:
        status_map = {
            "To Do": 1,
            "In Progress": 2,
            "In Review": 3,
            "Completed": 4,
        }
        task_status_id = status_map.get(status)
        if task_status_id is None:
            return {"http_error": 400, "reason": f"Unknown status: {status}"}
        return self._request_json(f"/api/v1/tasks/{task_id}/status/", {"task_status_id": task_status_id}, method="POST")

    def api_v1_update_task(self, task_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Actualiza campos de una tarea existente (title, description, etc.).

        Usa PATCH: el endpoint rechaza PUT completo (400 por campos
        obligatorios faltantes) — verificado contra M360 2026-10-10.
        """
        allowed_fields = {"title", "description", "important", "ticket_price", "due_date", "assigned_to_id", "task_status_id"}
        payload = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if not payload:
            return {"http_error": 400, "reason": "No valid fields provided for update"}
        return self._request_json(f"/api/v1/tasks/{task_id}/", payload, method="PATCH")

    # ======================
    # COURSES API v1
    # ======================
    def api_v1_list_courses(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/courses/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_course(self, title: str, project_id: int = 0, **kwargs: Any) -> Dict[str, Any]:
        import re
        slug = kwargs.pop("slug", None)
        if not slug:
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
        payload: Dict[str, Any] = {
            "title": title,
            "slug": slug,
            "project_id": project_id,
        }
        for optional, value in [
            ("description", kwargs.get("description", "")),
            ("short_description", kwargs.get("short_description", "")),
            ("tutor_id", kwargs.get("tutor_id")),
            ("category_id", kwargs.get("category_id")),
            ("career_id", kwargs.get("career_id")),
            ("cycle_id", kwargs.get("cycle_id")),
            ("level", kwargs.get("level", "beginner")),
            ("price", kwargs.get("price", 0)),
            ("duration_hours", kwargs.get("duration_hours", 0)),
            ("is_published", kwargs.get("is_published", False)),
            ("is_featured", kwargs.get("is_featured", False)),
            ("codigo", kwargs.get("codigo")),
            ("creditos", kwargs.get("creditos")),
            ("ht", kwargs.get("ht")),
            ("hp", kwargs.get("hp")),
            ("hl", kwargs.get("hl")),
            ("pc", kwargs.get("pc")),
            ("requisitos", kwargs.get("requisitos")),
            ("naturaleza", kwargs.get("naturaleza")),
            ("competencia_general", kwargs.get("competencia_general")),
            ("componentes", kwargs.get("componentes")),
            ("sumilla", kwargs.get("sumilla")),
            ("logro_curso", kwargs.get("logro_curso")),
            ("sistema_evaluacion", kwargs.get("sistema_evaluacion")),
            ("bibliografia", kwargs.get("bibliografia")),
        ]:
            if value is not None and value != "":
                payload[optional] = value
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._request_json("/api/v1/courses/", payload, method="POST")

    def api_v1_update_course(self, course_id: int, **kwargs: Any) -> Dict[str, Any]:
        allowed_fields = {
            "title", "description", "short_description", "tutor_id", "category_id",
            "career_id", "cycle_id",
            "level", "price", "duration_hours", "is_published", "is_featured", "published_at",
            "codigo", "creditos", "ht", "hp", "hl", "pc", "requisitos", "naturaleza",
            "competencia_general", "componentes", "sumilla", "logro_curso",
            "sistema_evaluacion", "bibliografia",
        }
        payload = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if not payload:
            return {"http_error": 400, "reason": "No valid fields provided for update"}
        return self._request_json(f"/api/v1/courses/{course_id}/", payload, method="PATCH")

    def api_v1_delete_course(self, course_id: int) -> Dict[str, Any]:
        return self._request_json(f"/api/v1/courses/{course_id}/", {}, method="DELETE")

    # ======================
    # DIGITALIZACION API v1
    #
    # Nota (2026-10-14): el metadata OPTIONS de los endpoints de
    # digitalización sololista PUT, pero DELETE SÍ funciona en el servidor
    # (verificado: 204 No Content). Los DELETE existen en DRF pese a no
    # aparecer en la introspección.
    # ======================

    def api_v1_delete_document(self, documento_id: int) -> Dict[str, Any]:
        """Elimina un documento digitalizado (DELETE real, 204 si ok)."""
        return self._request_json(f"/api/v1/digitalizacion/documentos/{documento_id}/", {}, method="DELETE")

    def api_v1_delete_lote(self, lote_id: int, forzar: bool = False) -> Dict[str, Any]:
        """Elimina un lote de digitalización (cascada: documentos y etapas).

        Guarda de archivo legal: rechaza lotes certificados salvo forzar=True.
        La verificación vive en la primitiva (no solo en el tool wrapper) para
        que ningún otro caller futuro la evite.
        """
        if not forzar:
            prev = self._get_request(f"/api/v1/digitalizacion/lotes/{lote_id}/")
            estado = (prev or {}).get("estado") if isinstance(prev, dict) else None
            if estado == "certificado":
                return {
                    "http_error": 409,
                    "reason": f"Lote {lote_id} CERTIFICADO (archivo legal): requiere forzar=True explícito.",
                }
        return self._request_json(f"/api/v1/digitalizacion/lotes/{lote_id}/", {}, method="DELETE")

    def api_v1_list_course_categories(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/course-categories/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_course_category(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name}
        for optional in ("description", "slug"):
            if optional in kwargs and kwargs[optional] not in (None, ""):
                payload[optional] = kwargs[optional]
        return self._request_json("/api/v1/course-categories/", payload, method="POST")

    def api_v1_list_events(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/events/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_event(self, title: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"title": title}
        for optional in ("description", "event_status", "event_category", "start_date", "end_date", "venue", "max_attendees", "ticket_price", "assigned_to", "attendees", "tags"):
            if optional in kwargs and kwargs[optional] not in (None, ""):
                payload[optional] = kwargs[optional]
        return self._request_json("/api/v1/events/", payload, method="POST")

    def api_v1_list_reminders(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/reminders/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_reminder(self, remind_at: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "remind_at": remind_at,
            "title": kwargs.get("title") or "Sprint reminder",
            "reminder_type": kwargs.get("reminder_type", "email"),
            "created_by_id": kwargs.get("created_by_id", self._current_user_id() or 1),
        }
        if kwargs.get("reminder_type") == "sprint":
            payload["reminder_type"] = "email"
        for optional in ("task_id", "project_id", "event_id", "notes"):
            if optional in kwargs and kwargs[optional] not in (None, ""):
                payload[optional] = kwargs[optional]
        return self._request_json("/api/v1/reminders/", payload, method="POST")

    def api_v1_list_inbox(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/inbox/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_inbox_item(self, title: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"title": title}
        for optional in ("description", "notes", "gtd_category", "created_by", "assigned_to"):
            if optional in kwargs and kwargs[optional] not in (None, ""):
                payload[optional] = kwargs[optional]
        return self._request_json("/api/v1/inbox/", payload, method="POST")

    def api_v1_update_inbox_item(self, item_id: int, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {k: v for k, v in kwargs.items() if v not in (None, "")}
        return self._request_json(f"/api/v1/inbox/{item_id}/", payload, method="PATCH")

    # ======================
    # COURSES EXTENDED API v1
    # ======================
    def api_v1_list_modules(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/modules/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_module(self, course_id: int, title: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "course": course_id,
            "title": title,
            "order": kwargs.get("order", 1),
            "description": kwargs.get("description", ""),
            "logro_unidad": kwargs.get("logro_unidad", ""),
        }
        return self._request_json("/api/v1/modules/", payload, method="POST")

    def api_v1_list_lessons(self, **params: Any) -> Dict[str, Any]:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        path = "/api/v1/lessons/" + (f"?{qs}" if qs else "")
        return self._get_request(path)

    def api_v1_create_lesson(self, module_id: Optional[int] = None, title: str = "", **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "lesson_type": kwargs.get("lesson_type", "text"),
            "order": kwargs.get("order", 1),
            "is_free": kwargs.get("is_free", False),
            "duration_minutes": kwargs.get("duration_minutes", 0),
            "content": kwargs.get("content", ""),
            "structured_content": kwargs.get("structured_content", []),
            "video_url": kwargs.get("video_url", ""),
            "quiz_questions": kwargs.get("quiz_questions", []),
            "logro_semana": kwargs.get("logro_semana", ""),
            "saberes_esenciales": kwargs.get("saberes_esenciales", ""),
            "actividades": kwargs.get("actividades", ""),
            "trabajo_campo": kwargs.get("trabajo_campo", ""),
        }
        if module_id is not None:
            payload["module"] = module_id
        return self._request_json("/api/v1/lessons/", payload, method="POST")

    def api_v1_update_lesson(self, lesson_id: int, **kwargs: Any) -> Dict[str, Any]:
        allowed_fields = {
            "title", "description", "lesson_type", "module", "order",
            "content", "structured_content", "video_url", "duration_minutes",
            "is_published", "is_featured", "is_free", "quiz_questions",
            "assignment_instructions", "assignment_file", "assignment_due_date",
            "logro_semana", "saberes_esenciales", "actividades", "trabajo_campo",
        }
        payload: Dict[str, Any] = {k: v for k, v in kwargs.items() if k in allowed_fields and v not in (None, "")}
        return self._request_json(f"/api/v1/lessons/{lesson_id}/", payload, method="PATCH")

    # ======================
    # DIGITALIZACION API v1
    # ======================
    # MEMENTO TICKETS
    # ======================
    def m360_link_ticket(
        self,
        ticket_id: str,
        project_id: Optional[int] = None,
        project_title: str = "",
        task_id: Optional[int] = None,
        task_title: str = "",
        event_id: Optional[int] = None,
        event_title: str = "",
        reminder_id: Optional[int] = None,
        inbox_item_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if project_id is not None:
            payload["project_id"] = project_id
            payload["project_title"] = project_title
        if task_id is not None:
            payload["task_id"] = task_id
            payload["task_title"] = task_title
        if event_id is not None:
            payload["event_id"] = event_id
            payload["event_title"] = event_title
        if reminder_id is not None:
            payload["reminder_id"] = reminder_id
        if inbox_item_id is not None:
            payload["inbox_item_id"] = inbox_item_id
        return self._request_json(f"/api/tickets/{ticket_id}/link-m360", payload, method="POST")

    def m360_create_ticket_from_task(
        self,
        task_id: int,
        created_by: str = "assistant",
        priority: str = "medium",
        source: str = "bridge",
    ) -> Dict[str, Any]:
        task = self.api_v1_get_task(task_id)
        if not isinstance(task, dict) or task.get("http_error") or task.get("network_error"):
            return task
        title = task.get("title") or task.get("name") or f"Tarea {task_id}"
        description = task.get("description") or ""
        project = task.get("project") or {}
        project_id = project.get("id") if isinstance(project, dict) else task.get("project_id")
        project_title = project.get("title") if isinstance(project, dict) else ""
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "created_by": created_by,
            "priority": priority,
            "source": source,
            "m360_links": {},
        }
        if project_id:
            payload["m360_links"]["project_id"] = project_id
            payload["m360_links"]["project_title"] = project_title or ""
        payload["m360_links"]["task_id"] = task_id
        payload["m360_links"]["task_title"] = title
        return self._request_json("/api/tickets", payload, method="POST")

    def m360_sync_tickets_for_project(self, project_id: int, created_by: str = "assistant") -> Dict[str, Any]:
        tasks = self.api_v1_list_tasks(project_id=project_id)
        if not isinstance(tasks, (dict, list)):
            return {"error": "invalid_tasks_response", "raw": str(tasks)[:200]}
        # Fail-closed: un fallo de API (auth/red/500/timeout) NO debe reportarse
        # como "sincronicé 0 tareas" con pinta de éxito.
        if isinstance(tasks, dict) and any(tasks.get(k) for k in ("http_error", "network_error", "timeout")):
            return {"ok": False, "error_code": "SYNC_TASKS_FALLO", "raw": str(tasks)[:200]}
        # Lista vacía es válida (proyecto sin tareas -> resumen con 0), no error.
        data = self._unwrap_list(tasks)
        summary: Dict[str, Any] = {"project_id": project_id, "total_tasks": len(data), "created_tickets": 0, "skipped": 0, "errors": []}
        for task in data:
            task_id = task.get("id")
            title = task.get("title") or task.get("name")
            if not task_id or not title:
                summary["skipped"] += 1
                continue
            ticket = self.m360_create_ticket_from_task(task_id, created_by=created_by, source="bridge")
            if isinstance(ticket, dict) and ticket.get("id"):
                summary["created_tickets"] += 1
            else:
                summary["errors"].append({"task_id": task_id, "result": ticket})
        return summary

    # ======================
    # DIGITALIZACION API v1
    # ======================
    def api_v1_digi_cargar_lote(self, nombre_lote: str, ruta_base: str, modo: str = "existing", created_by_id: Optional[int] = None, metadata_proyecto: Optional[Dict[str, Any]] = None, ruta_fuente: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "nombre_lote": nombre_lote,
            "ruta_fuente": ruta_fuente or ruta_base,
            "ruta_base": ruta_base,
            "modo": modo,
            "created_by_id": created_by_id,
            "metadata_proyecto": metadata_proyecto or {},
        }
        return self._request_json("/api/v1/digitalizacion/lotes/cargar/", payload, method="POST")

    def digi_cargar_lote(self, folder_path: str, nombre_lote: Optional[str] = None, metadata_proyecto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Alias de compatibilidad de `digi_ingestar_lote` (born-digital)."""
        return self.digi_ingestar_lote(folder_path, nombre_lote=nombre_lote, metadata_proyecto=metadata_proyecto)

    def digi_ingestar_lote(self, folder_path: str, nombre_lote: Optional[str] = None, metadata_proyecto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Registrar lote born-digital desde carpeta existente en M360.

        Envía la carpeta al endpoint de digitalización con modo "existing".
        La characterisation técnica, el checksum y la validación de
        autenticidad las ejecuta el backend de M360 sobre los archivos
        ingestados; este método solo valida que la carpeta exista localmente.

        Args:
            folder_path: Carpeta con archivos born-digital.
            nombre_lote: Nombre del lote; si es None se usa el nombre de la carpeta.
            metadata_proyecto: Contexto organizacional y técnico adicional.

        Returns:
            Respuesta del endpoint (`ok`, `lote_id`, `documentos`, ...) o
            `{"ok": False, "error": ...}` si la carpeta no existe.
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return {"ok": False, "error": f"carpeta_no_encontrada: {folder_path}"}
        nombre_lote = nombre_lote or f"{folder.name}"
        return self.api_v1_digi_cargar_lote(
            nombre_lote=nombre_lote,
            ruta_base=str(folder),
            modo="existing",
            metadata_proyecto=metadata_proyecto,
        )

    def digi_validar_documento(self, file_path: str) -> Dict[str, Any]:
        """Validar documento born-digital y extraer metadatos técnicos.

        NOTA: la validación real (checksum SHA-256, characterisation,
        antivirus) aún no está implementada en el bridge; el método
        falla cerrado hasta que exista implementación local o de backend.

        Args:
            file_path: Ruta al archivo PDF/DOCX/XLSX, etc.

        Returns:
            Diccionario con `ok`, `format`, `metadata`, `checksum` y `errors`.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return {"ok": False, "error": f"archivo_no_encontrado: {file_path}"}
        return {
            "ok": False,
            "error": "validacion_no_implementada",
            "format": path.suffix.lower().lstrip("."),
            "metadata": {},
            "checksum": {},
            "errors": ["validacion_no_implementada: falta checksum SHA-256 y characterisation"],
        }
