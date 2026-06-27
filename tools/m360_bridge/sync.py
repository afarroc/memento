"""Sincronizador de sprints/handoffs hacia M360."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import M360Client
from .models import SyncResult


@dataclass(frozen=True)
class SprintTask:
    id: str
    title: str
    description: str = ""
    status: str = "todo"
    priority: str = "medium"
    due_date: str = ""
    depends_on: List[str] | None = None


@dataclass(frozen=True)
class SprintEvent:
    id: str
    title: str
    start_date: str
    end_date: str
    status: str = "planned"
    category: str = ""
    description: str = ""
    price: str = ""
    capacity: str = ""


@dataclass(frozen=True)
class SprintReminder:
    id: str
    remind_at: str
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    reminder_type: str = "task"


@dataclass(frozen=True)
class SprintSpec:
    sprint_id: str
    project_name: str
    project_description: str = ""
    project_start: str = ""
    project_end: str = ""
    project_status: str = "active"
    tasks: List[SprintTask] | None = None
    events: List[SprintEvent] | None = None
    reminders: List[SprintReminder] | None = None


def _load_gtd_csv(name: str) -> List[Dict[str, str]]:
    base = Path(__file__).resolve().parent.parent.parent / "gtd_memento"
    path = base / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _to_date(value: str) -> str:
    if not value:
        return ""
    text = value.strip()
    if len(text) == 10:
        return text
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except Exception:
        return text


def infer_sprint_spec(sprint_id: str, *, now: Optional[date] = None) -> SprintSpec:
    now = now or date.today()
    start = now.isoformat()
    end = (now + __import__("datetime").timedelta(days=5)).isoformat()

    tasks: List[SprintTask] = []
    for row in _load_gtd_csv("03_templates/sprint_templates.csv"):
        tasks.append(
            SprintTask(
                id=row.get("id", ""),
                title=row.get("name", ""),
                description=row.get("description", ""),
                status="todo",
                priority="medium",
                due_date="",
            )
        )

    # Fallback: si no hay templates, generar 3 tareas mínimas para probar la integración
    if not tasks:
        for index, title in enumerate(["Base de estabilización", "Corrección de bloqueantes", "Documentación y handoffs"], start=1):
            tasks.append(
                SprintTask(
                    id=str(index),
                    title=title,
                    status="todo",
                    priority="medium",
                    due_date="",
                )
            )

    events: List[SprintEvent] = [
        SprintEvent(
            id="kickoff",
            title="Sprint Kickoff",
            start_date=start,
            end_date=start,
            status="planned",
            category="sprint",
            description="Inicio de sprint",
        ),
        SprintEvent(
            id="review",
            title="Sprint Review",
            start_date=end,
            end_date=end,
            status="planned",
            category="sprint",
            description="Cierre y revisión",
        ),
    ]

    reminders: List[SprintReminder] = [
        SprintReminder(
            id="reminder-1",
            remind_at=f"{end}T09:00:00",
            reminder_type="sprint",
        )
    ]

    return SprintSpec(
        sprint_id=sprint_id,
        project_name=f"MementoBloom - {sprint_id}",
        project_description=f"Sincronizado automáticamente desde gtd_memento ({start})",
        project_start=start,
        project_end=end,
        project_status="active",
        tasks=tasks or None,
        events=events or None,
        reminders=reminders or None,
    )


class M360Sync:
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
        env_path: Optional[str] = None,
    ) -> None:
        env_path = env_path or str(Path(__file__).resolve().parent.parent.parent / ".env")
        if os.path.exists(env_path):
            for line in Path(env_path).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
        base_url = base_url or os.environ.get("M360_BASE_URL", "http://127.0.0.1:8000")
        username = username or os.environ.get("M360_USERNAME", "")
        password = password or os.environ.get("M360_PASSWORD", "")
        timeout = timeout if timeout is not None else int(os.environ.get("M360_TIMEOUT", "10"))
        self.client = M360Client(base_url=base_url, username=username, password=password)
        self._timeout = timeout

    def sync_sprint(self, sprint_id: str, project_id: Optional[int] = None) -> SyncResult:
        result = SyncResult()
        spec = infer_sprint_spec(sprint_id)
        if spec is None:
            result.add_error("sprint_spec", "No se pudo inferir el sprint")
            return result

        if project_id is not None:
            result.add_ok(f"usando proyecto existente id={project_id}")
        else:
            project_resp = self.client.api_v1_create_project(
                title=spec.project_name,
                description=spec.project_description,
            )
            project_id = self._extract_id(project_resp)
            if project_id is None and not project_resp.get("ok"):
                result.add_error("project", f"Error al crear proyecto: {project_resp}")
                return result
            if project_id is None:
                project_id = self._extract_id_from_redirect(project_resp, "projects")
            if project_id is None and not project_resp.get("ok"):
                result.add_error("project", f"Error al crear proyecto: {project_resp}")
                return result
            result.add_ok(f"proyecto creado id={project_id or 'ok'}")

        task_id_map: Dict[str, int] = {}
        if spec.tasks:
            for task in spec.tasks:
                task_resp = self.client.api_v1_create_task(
                    title=task.title,
                    project_id=project_id,
                    description=task.description,
                )
                new_task_id = self._extract_id(task_resp)
                if new_task_id is None and not task_resp.get("ok"):
                    result.add_error("task", f"Error creando {task.id}: {task_resp}")
                    continue
                if new_task_id is None:
                    new_task_id = self._extract_id_from_redirect(task_resp, "tasks")
                if new_task_id is not None:
                    task_id_map[task.id] = new_task_id
                    result.add_ok(f"tarea {task.id} -> id={new_task_id}")
                else:
                    result.add_ok(f"tarea {task.id} -> creada (redirect)")

        if spec.events:
            for event in spec.events:
                event_resp = self.client.api_v1_create_event(
                    title=event.title,
                    description=event.description,
                )
                if not event_resp.get("ok") and "http_error" in event_resp and str(event_resp.get("http_error")).startswith("4"):
                    result.add_error("event", f"Error creando {event.id}: {event_resp}")
                else:
                    result.add_ok(f"evento {event.id}")

        if spec.reminders:
            for reminder in spec.reminders:
                resolved_task_id = task_id_map.get(reminder.task_id) if reminder.task_id else None
                reminder_resp = self.client.api_v1_create_reminder(
                    remind_at=reminder.remind_at,
                    reminder_type=reminder.reminder_type,
                    task_id=resolved_task_id,
                    project_id=project_id,
                )
                if not reminder_resp.get("ok") and "http_error" in reminder_resp and str(reminder_resp.get("http_error")).startswith("4"):
                    result.add_error("reminder", f"Error creando recordatorio {reminder.id}: {reminder_resp}")
                else:
                    result.add_ok(f"recordatorio {reminder.id}")

        return result

    @staticmethod
    def _extract_id(payload: Dict[str, Any]) -> Optional[int]:
        if not isinstance(payload, dict):
            return None
        for key in ("id", "project_id", "task_id"):
            if key in payload:
                try:
                    return int(payload[key])
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _extract_id_from_redirect(payload: Dict[str, Any], kind: str) -> Optional[int]:
        import re
        redirect = payload.get("redirect") or ""
        m = re.search(rf"/events/{kind}/(?:panel/)?(\d+)", redirect)
        if m:
            try:
                return int(m.group(1))
            except (TypeError, ValueError):
                return None
        return None


def sync_sprint(sprint_id: str) -> Dict[str, Any]:
    sync = M360Sync()
    result = sync.sync_sprint(sprint_id)
    return {
        "sprint_id": sprint_id,
        "ok": result.ok,
        "errors": result.errors,
        "details": result.details,
    }
