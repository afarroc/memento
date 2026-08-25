"""MementoBloom :: Service ticket model, storage, and helpers.

A ticket is the canonical entry point for work managed by mementobloom:
- created manually from the panel, from the assistant, or from M360 bridge
- managed by the on-duty assistant through the panel or CLI
- optionally linked to M360 objects: project, task, event, reminder, inbox item

Storage:
- Primary: .memento_runtime/tickets.json (local, file-backed)
- Optional cache: Redis list memento_tickets
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parent.parent
TICKETS_PATH = ROOT / ".memento_runtime" / "tickets.json"
REDIS_KEY = os.environ.get("REDIS_TICKETS_KEY", "memento_tickets")


@dataclass
class M360Link:
    project_id: int = 0
    project_title: str = ""
    task_id: int = 0
    task_title: str = ""
    event_id: int = 0
    event_title: str = ""
    reminder_id: int = 0
    inbox_item_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_title": self.project_title,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "reminder_id": self.reminder_id,
            "inbox_item_id": self.inbox_item_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "M360Link":
        return cls(
            project_id=int(data.get("project_id") or 0),
            project_title=data.get("project_title") or "",
            task_id=int(data.get("task_id") or 0),
            task_title=data.get("task_title") or "",
            event_id=int(data.get("event_id") or 0),
            event_title=data.get("event_title") or "",
            reminder_id=int(data.get("reminder_id") or 0),
            inbox_item_id=int(data.get("inbox_item_id") or 0),
        )


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    status: str = "open"
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    created_by: str = "assistant"
    assigned_to: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = "manual"
    m360_links: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    resolution: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "tags": list(self.tags),
            "source": self.source,
            "m360_links": dict(self.m360_links),
            "context": dict(self.context),
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        m360_links = data.get("m360_links") or {}
        if isinstance(m360_links, dict):
            m360_links = dict(m360_links)
        else:
            m360_links = {}
        return cls(
            id=str(data.get("id") or ""),
            title=str(data.get("title") or ""),
            description=str(data.get("description") or ""),
            status=str(data.get("status") or "open"),
            priority=str(data.get("priority") or "medium"),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            created_by=str(data.get("created_by") or "assistant"),
            assigned_to=str(data.get("assigned_to") or ""),
            tags=list(data.get("tags") or []),
            source=str(data.get("source") or "manual"),
            m360_links=m360_links,
            context=dict(data.get("context") or {}),
            resolution=str(data.get("resolution") or ""),
        )


def _ensure_storage() -> None:
    TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not TICKETS_PATH.exists():
        TICKETS_PATH.write_text(json.dumps({"tickets": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_store() -> Dict[str, Any]:
    _ensure_storage()
    try:
        data = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {"tickets": []}
        data.setdefault("tickets", [])
        return data
    except Exception:
        return {"tickets": []}


def _save_store(store: Dict[str, Any]) -> None:
    _ensure_storage()
    TICKETS_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_id(tickets: List[Ticket]) -> str:
    max_num = 0
    for t in tickets:
        try:
            num = int(str(t.id).split("-")[-1])
            max_num = max(max_num, num)
        except Exception:
            continue
    return f"TICK-{max_num + 1:04d}"


def create_ticket(
    title: str,
    description: str,
    created_by: str = "assistant",
    priority: str = "medium",
    source: str = "manual",
    tags: Optional[List[str]] = None,
    m360_links: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Ticket:
    store = _load_store()
    tickets = [Ticket.from_dict(x) for x in store.get("tickets", [])]
    ticket = Ticket(
        id=_next_id(tickets),
        title=title,
        description=description,
        created_by=created_by,
        priority=priority,
        source=source,
        tags=list(tags or []),
        m360_links=dict(m360_links or {}),
        context=dict(context or {}),
    )
    tickets.append(ticket)
    store["tickets"] = [t.to_dict() for t in tickets]
    _save_store(store)
    return ticket


def update_ticket(ticket_id: str, **changes: Any) -> Optional[Ticket]:
    store = _load_store()
    tickets = [Ticket.from_dict(x) for x in store.get("tickets", [])]
    updated: Optional[Ticket] = None
    for idx, t in enumerate(tickets):
        if t.id == ticket_id:
            for k, v in changes.items():
                if hasattr(t, k):
                    setattr(t, k, v)
            t.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            tickets[idx] = t
            updated = t
            break
    if updated is not None:
        store["tickets"] = [t.to_dict() for t in tickets]
        _save_store(store)
    return updated


def get_ticket(ticket_id: str) -> Optional[Ticket]:
    store = _load_store()
    for item in store.get("tickets", []):
        if item.get("id") == ticket_id:
            return Ticket.from_dict(item)
    return None


def list_tickets(status: Optional[str] = None, source: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Ticket]:
    store = _load_store()
    tickets = [Ticket.from_dict(x) for x in store.get("tickets", [])]
    if status:
        tickets = [t for t in tickets if t.status == status]
    if source:
        tickets = [t for t in tickets if t.source == source]
    if tags:
        tickets = [t for t in tickets if any(tag in t.tags for tag in tags)]
    tickets.sort(key=lambda t: t.created_at, reverse=True)
    return tickets


def delete_ticket(ticket_id: str) -> bool:
    store = _load_store()
    tickets = [Ticket.from_dict(x) for x in store.get("tickets", [])]
    filtered = [t for t in tickets if t.id != ticket_id]
    if len(filtered) == len(tickets):
        return False
    store["tickets"] = [t.to_dict() for t in filtered]
    _save_store(store)
    return True


def stats() -> Dict[str, Any]:
    tickets = list_tickets()
    by_status: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for t in tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        by_source[t.source] = by_source.get(t.source, 0) + 1
    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
        "by_source": by_source,
    }
