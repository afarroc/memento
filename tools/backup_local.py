#!/usr/bin/env python3
"""Backup automático de archivos locales personalizados no trackeados.

Copia el estado actual de archivos locales importantes a `.backups/<YYYYMMDD_HHMMSS>/`
sin modificar nada en el working tree. Sirve como punto de restauración manual.
"""

from __future__ import annotations

import argparse
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

WS = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_ROOT = WS / ".backups"


def _normalize_destination(dest_root: Optional[Path], ts: str) -> Path:
    base = dest_root if dest_root is not None else DEFAULT_BACKUP_ROOT
    return Path(base) / ts


def _get_backup_paths(include: Optional[List[str]], exclude: Optional[List[str]]) -> List[Path]:
    paths: List[Path] = [
        WS / "memory" / "personality",
        WS / "gtd_memento",
        WS / "config.json",
        WS / ".env",
        WS / ".agent_context" / "START_CONTEXT.md",
        WS / "projects" / "m360",
        WS / "projects" / "ventas_porta",
    ]
    if include:
        paths += [WS / p for p in include]
    if exclude:
        paths = [p for p in paths if str(p.relative_to(WS)) not in exclude]
    return paths


def backup(dest_root: Optional[Path] = None, compress: bool = False) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = _normalize_destination(dest_root, ts)
    dest.mkdir(parents=True, exist_ok=False)

    backup_paths = _get_backup_paths(None, None)

    copied = []
    for src in backup_paths:
        if not src.exists():
            continue
        rel = src.relative_to(WS)
        dst = dest / rel
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied.append(str(rel))

    manifest = dest / "manifest.txt"
    manifest.write_text(
        "MementoBloom local backup\n"
        f"Timestamp: {ts}\n"
        f"Compressed: {compress}\n"
        f"Items backed up: {len(copied)}\n"
        + "\n".join(sorted(copied)),
        encoding="utf-8",
    )

    if compress:
        archive_name = str(dest) + ".tar.gz"
        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(dest, arcname=ts)
        shutil.rmtree(dest)
        print(f"Backup comprimido creado en: {archive_name}")
        return Path(archive_name)

    print(f"Backup creado en: {dest}")
    return dest


def restore(backup_ts: str, dest_root: Path = WS, dry_run: bool = False) -> None:
    src = Path(backup_ts) if Path(backup_ts).exists() else DEFAULT_BACKUP_ROOT / backup_ts
    if not src.exists():
        raise FileNotFoundError(f"No existe el backup: {src}")
    for item in sorted(src.iterdir()):
        if item.name == "manifest.txt":
            continue
        target = dest_root / item.name
        print(f"[restore] {item} -> {target}")
        if dry_run:
            continue
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup de archivos locales personalizados no trackeados")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("backup", help="Crear backup")
    b.add_argument("--dest", type=Path, help="Directorio destino (por defecto .backups/)")
    b.add_argument("--compress", action="store_true", help="Comprimir backup en tar.gz")
    r = sub.add_parser("restore", help="Restaurar backup")
    r.add_argument("timestamp", help="Timestamp del backup a restaurar (ej. 20260627_131500)")
    r.add_argument("--dest", type=Path, default=WS, help="Directorio destino")
    r.add_argument("--dry-run", action="store_true", help="Mostrar acciones sin escribir")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "backup":
        backup(dest_root=args.dest, compress=args.compress)
    elif args.command == "restore":
        restore(backup_ts=args.timestamp, dest_root=args.dest, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
