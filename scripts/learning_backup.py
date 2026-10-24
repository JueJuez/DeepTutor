"""Quiesced single-user learning backups; restore only into a new directory.

Run with --help. Model settings, credentials, logs, KBs and other workspaces
are deliberately outside this bounded recovery format.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack, closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
from typing import Any
import uuid

FORMAT_VERSION = 1
ROOTS = (
    "chat_history.db",
    "usage.sqlite3",
    "workspace/learning",
    "workspace/reading",
    "workspace/notebook",
)
MANIFEST = "snapshot.json"


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _allowed(name: str) -> bool:
    parts = PurePosixPath(name)
    return (
        not parts.is_absolute()
        and ".." not in parts.parts
        and "\\" not in name
        and ":" not in name
        and name == parts.as_posix()
        and any(name == root or name.startswith(root + "/") for root in ROOTS)
    )


def _inventory(root: Path) -> dict[str, tuple[int, int]]:
    files = {}
    for selected in ROOTS:
        entry = root / selected
        if not entry.exists():
            continue
        # Reject links before recursing: snapshots cannot escape their scope.
        stack = [entry]
        if entry.is_file() and entry.suffix in {".db", ".sqlite3"}:
            stack.extend(
                path
                for suffix in ("-wal", "-shm", "-journal")
                if (path := Path(str(entry) + suffix)).exists()
            )
        while stack:
            path = stack.pop()
            if path.is_symlink() or path.is_junction():
                raise ValueError(f"Linked storage is unsupported: {path}")
            if path.is_dir():
                stack.extend(path.iterdir())
            elif path.is_file():
                stat = path.stat()
                files[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return files


def _new_stage(source: Path, destination: Path) -> Path:
    source, destination = source.resolve(), destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination must not exist: {destination}")
    if destination.resolve().is_relative_to(source) or source.is_relative_to(destination.resolve()):
        raise ValueError("Source and destination must be separate directory trees")
    if not destination.parent.is_dir():
        raise ValueError("Destination parent must already exist")
    stage = destination.with_name(destination.name + ".partial-" + uuid.uuid4().hex)
    stage.mkdir(mode=0o700)
    return stage


def _sqlite_copy(source: Path, destination: Path) -> dict[str, Any]:
    # Read-only URI + SQLite backup includes committed WAL pages without
    # checkpointing or changing the source database.
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
        with closing(sqlite3.connect(destination)) as copied:
            original.backup(copied)
            copied.commit()
            copied.execute("PRAGMA journal_mode=DELETE")
            return _sqlite_info(copied)


def _sqlite_info(conn: sqlite3.Connection) -> dict[str, Any]:
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite integrity check failed")
    schema = conn.execute(
        "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
    ).fetchall()
    return {
        "user_version": conn.execute("PRAGMA user_version").fetchone()[0],
        "schema_sha256": hashlib.sha256(json.dumps(schema).encode()).hexdigest(),
    }


def create_backup(user_root: Path, destination: Path, *, quiesced: bool = False) -> Path:
    """Back up selected stores after all writers have been stopped.

    Individual SQLite copies are WAL-safe. Cross-store consistency relies on
    the caller stopping writers; inventory changes abort rather than publish.
    An interrupted operation leaves an explicitly incomplete .partial folder.
    """
    if not quiesced:
        raise ValueError("Stop all writers and explicitly pass quiesced=True / --quiesced")
    user_root, destination = user_root.resolve(), destination.absolute()
    if not user_root.is_dir():
        raise ValueError("User storage directory does not exist")
    initial = _inventory(user_root)
    if "chat_history.db" not in initial:
        raise ValueError("Selected user root has no chat_history.db")
    stage = _new_stage(user_root, destination)
    records = {}
    with ExitStack() as handles:
        guards = []
        for name in initial:
            if Path(name).suffix in {".db", ".sqlite3"}:
                conn = handles.enter_context(
                    closing(sqlite3.connect((user_root / name).as_uri() + "?mode=ro", uri=True))
                )
                guards.append((conn, conn.execute("PRAGMA data_version").fetchone()[0]))
        # Reader creation can initialize WAL sidecars. Freeze inventory only
        # after guards are open, and ignore SHM read marks, never WAL content.
        before = _inventory(user_root)
        for name in sorted(before):
            if name.endswith(("-wal", "-shm", "-journal")):
                if any(
                    name.removesuffix(suffix) in before for suffix in ("-wal", "-shm", "-journal")
                ):
                    continue
                raise ValueError("Orphan SQLite sidecar in selected storage")
            original, copied = user_root / name, stage / name
            copied.parent.mkdir(parents=True, exist_ok=True)
            database = (
                _sqlite_copy(original, copied) if original.suffix in {".db", ".sqlite3"} else None
            )
            if database is None:
                shutil.copyfile(original, copied)
            records[name] = {
                "sha256": _digest(copied),
                "size": copied.stat().st_size,
                "sqlite": database,
            }

        def stable(inventory: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
            return {k: v for k, v in inventory.items() if not k.endswith("-shm")}

        changed = any(
            conn.execute("PRAGMA data_version").fetchone()[0] != version for conn, version in guards
        )
        if changed or stable(before) != stable(_inventory(user_root)):
            raise ValueError(
                "Storage changed during backup; stop writers and retry into a new directory"
            )
    snapshot = {
        "format_version": FORMAT_VERSION,
        "app_version": importlib.metadata.version("deeptutor"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "consistency": "caller_quiesced",
        "scope": list(ROOTS),
        "files": records,
    }
    (stage / MANIFEST).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    verify_backup(stage)
    # os.rename on Windows refuses an existing destination; do not use replace.
    if destination.exists():
        raise FileExistsError(destination)
    os.rename(stage, destination)
    return destination


def verify_backup(backup: Path) -> dict[str, Any]:
    """Reject incomplete, modified, linked or out-of-scope snapshots."""
    manifest = backup / MANIFEST
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("Missing snapshot manifest")
    snapshot = json.loads(manifest.read_text(encoding="utf-8"))
    if snapshot.get("format_version") != FORMAT_VERSION or snapshot.get("scope") != list(ROOTS):
        raise ValueError("Unsupported backup format or scope")
    records = snapshot.get("files")
    if not isinstance(records, dict) or "chat_history.db" not in records:
        raise ValueError("Incomplete learning backup")
    actual = set()
    for path in backup.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked backup entries are unsupported")
        if path.is_file():
            actual.add(path.relative_to(backup).as_posix())
    if actual != {*records, MANIFEST}:
        raise ValueError("Backup has missing or extra files")
    for name, info in records.items():
        if not _allowed(name):
            raise ValueError("Unsafe or out-of-scope backup path")
        path = backup / name
        if path.stat().st_size != info["size"] or _digest(path) != info["sha256"]:
            raise ValueError("Backup checksum mismatch")
        if info.get("sqlite") is not None:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
                if _sqlite_info(conn) != info["sqlite"]:
                    raise ValueError("Backup schema mismatch")
    return snapshot


def restore_backup(backup: Path, destination: Path) -> Path:
    """Verify, restore into a new directory, verify again, then publish it."""
    backup, destination = backup.resolve(), destination.absolute()
    snapshot = verify_backup(backup)
    stage = _new_stage(backup, destination)
    for name in [*snapshot["files"], MANIFEST]:
        copied = stage / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(backup / name, copied)
    verify_backup(stage)
    if destination.exists():
        raise FileExistsError(destination)
    os.rename(stage, destination)
    return destination


def main() -> None:
    """Expose explicit backup and restore maintenance commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("--user-root", type=Path, required=True)
    backup.add_argument("--output", type=Path, required=True)
    backup.add_argument("--quiesced", action="store_true")
    restore = commands.add_parser("restore")
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            create_backup(args.user_root, args.output, quiesced=args.quiesced)
            if args.command == "backup"
            else restore_backup(args.backup, args.destination)
        )
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"Backup operation failed: {exc}\n")
    print(result)


if __name__ == "__main__":
    main()
