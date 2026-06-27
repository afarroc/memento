"""Cliente HTTP para M360 — autenticacion y operaciones CRUD."""
from __future__ import annotations

import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class M360Client:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._timeout = int(os.environ.get("M360_TIMEOUT", "10"))
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._jar))
        self._csrf: Optional[str] = None
        self._session_user: Optional[Dict[str, Any]] = None

    def _init_session(self) -> None:
        csrf_url = f"{self.base_url}/api/csrf/"
        req = urllib.request.Request(csrf_url, method="GET")
        with self._opener.open(req, timeout=self._timeout) as resp:
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
        if csrf:
            payload.setdefault("csrfmiddlewaretoken", csrf)
        encoded = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Referer", f"{self.base_url}{path}")
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
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"network_error": str(exc)}

    def _get_request(self, path: str) -> Dict[str, Any]:
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
            return {"http_error": exc.code, "reason": str(exc), **parsed}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"network_error": str(exc)}

    def _request_json(self, path: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST") -> Dict[str, Any]:
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
        return self._request_json(f"/api/v1/tasks/{task_id}/status/", {"status": status}, method="POST")

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
