#!/usr/bin/env python3
"""MementoBloom :: Ticket CLI — create and manage service tickets from the assistant or shell."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.tickets import (
    create_ticket,
    delete_ticket,
    get_ticket,
    list_tickets,
    stats as ticket_stats,
    update_ticket,
)


def _print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gestión de tickets de servicio MementoBloom")
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create", help="Crear ticket")
    create.add_argument("--title", required=True)
    create.add_argument("--description", required=True)
    create.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
    create.add_argument("--source", default="assistant", choices=["manual", "assistant", "bridge"])
    create.add_argument("--created-by", default="assistant")
    create.add_argument("--tags", default="")
    create.add_argument("--context", default="")

    update = sub.add_parser("update", help="Actualizar ticket")
    update.add_argument("ticket_id")
    update.add_argument("--status")
    update.add_argument("--priority")
    update.add_argument("--assigned-to")
    update.add_argument("--resolution")
    update.add_argument("--tags")

    show = sub.add_parser("show", help="Ver ticket")
    show.add_argument("ticket_id")

    delete = sub.add_parser("delete", help="Eliminar ticket")
    delete.add_argument("ticket_id")

    sub.add_parser("list", help="Listar tickets")
    sub.add_parser("stats", help="Estadísticas")

    resolve = sub.add_parser("resolve", help="Resolver ticket")
    resolve.add_argument("ticket_id")

    close = sub.add_parser("close", help="Cerrar ticket")
    close.add_argument("ticket_id")
    close.add_argument("--resolution", default="Cerrado desde CLI")

    link = sub.add_parser("link-m360", help="Vincular objeto M360 a ticket")
    link.add_argument("ticket_id")
    link.add_argument("--project-id", type=int)
    link.add_argument("--project-title", default="")
    link.add_argument("--task-id", type=int)
    link.add_argument("--task-title", default="")
    link.add_argument("--event-id", type=int)
    link.add_argument("--event-title", default="")
    link.add_argument("--reminder-id", type=int)
    link.add_argument("--inbox-item-id", type=int)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "create":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                context = {"raw": args.context}
        ticket = create_ticket(
            title=args.title,
            description=args.description,
            created_by=args.created_by,
            priority=args.priority,
            source=args.source,
            tags=tags,
            context=context,
        )
        _print_json(ticket.to_dict())
        return 0

    if args.command == "update":
        changes = {}
        if args.status:
            changes["status"] = args.status
        if args.priority:
            changes["priority"] = args.priority
        if args.assigned_to:
            changes["assigned_to"] = args.assigned_to
        if args.resolution:
            changes["resolution"] = args.resolution
        if args.tags:
            changes["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
        updated = update_ticket(args.ticket_id, **changes)
        if not updated:
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        _print_json(updated.to_dict())
        return 0

    if args.command == "show":
        ticket = get_ticket(args.ticket_id)
        if not ticket:
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        _print_json(ticket.to_dict())
        return 0

    if args.command == "delete":
        if not delete_ticket(args.ticket_id):
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        print(json.dumps({"ok": True}))
        return 0

    if args.command == "list":
        tickets = list_tickets()
        _print_json([t.to_dict() for t in tickets])
        return 0

    if args.command == "stats":
        _print_json(ticket_stats())
        return 0

    if args.command == "resolve":
        updated = update_ticket(args.ticket_id, status="resolved")
        if not updated:
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        _print_json(updated.to_dict())
        return 0

    if args.command == "close":
        updated = update_ticket(args.ticket_id, status="closed", resolution=args.resolution)
        if not updated:
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        _print_json(updated.to_dict())
        return 0

    if args.command == "link-m360":
        m360_links = {}
        if args.project_id is not None:
            m360_links["project_id"] = args.project_id
            m360_links["project_title"] = args.project_title or ""
        if args.task_id is not None:
            m360_links["task_id"] = args.task_id
            m360_links["task_title"] = args.task_title or ""
        if args.event_id is not None:
            m360_links["event_id"] = args.event_id
            m360_links["event_title"] = args.event_title or ""
        if args.reminder_id is not None:
            m360_links["reminder_id"] = args.reminder_id
        if args.inbox_item_id is not None:
            m360_links["inbox_item_id"] = args.inbox_item_id
        updated = update_ticket(args.ticket_id, m360_links=m360_links)
        if not updated:
            print(f"Ticket {args.ticket_id} not found", file=sys.stderr)
            return 1
        _print_json(updated.to_dict())
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
