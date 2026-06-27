"""Modelos de dominio para sincronizacion M360."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class M360Project:
    name: str
    description: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "active"
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
        }


@dataclass
class M360Task:
    title: str
    project_id: int
    description: str = ""
    due_date: str = ""
    priority: str = "medium"
    status: str = "todo"
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        return {
            "title": self.title,
            "project_id": self.project_id,
            "description": self.description,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
        }


@dataclass
class M360Event:
    title: str
    start_date: str
    end_date: str
    status: str = "planned"
    category: str = ""
    description: str = ""
    price: str = ""
    capacity: str = ""
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        return {
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "capacity": self.capacity,
        }


@dataclass
class M360InboxItem:
    title: str
    description: str = ""
    created_by: str = "mementobloom"
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "created_by": self.created_by,
        }


@dataclass
class M360Reminder:
    remind_at: str
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    reminder_type: str = "task"
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        payload: dict = {
            "remind_at": self.remind_at,
            "reminder_type": self.reminder_type,
        }
        if self.task_id is not None:
            payload["task_id"] = self.task_id
        if self.project_id is not None:
            payload["project_id"] = self.project_id
        return payload


@dataclass
class M360Dependency:
    task_id: int
    depends_on: int
    dependency_type: str = "blocks"
    m360_id: Optional[int] = None

    def to_payload(self) -> dict:
        return {
            "depends_on": self.depends_on,
            "dependency_type": self.dependency_type,
        }


@dataclass
class SyncResult:
    ok: int = 0
    errors: int = 0
    details: list[str] = field(default_factory=list)

    def add_ok(self, label: str) -> None:
        self.ok += 1
        self.details.append(label)

    def add_error(self, label: str, reason: str) -> None:
        self.errors += 1
        self.details.append(f"ERROR {label}: {reason}")
