"""Backup and restore service — SQLite database + raw files."""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("pharmgmt.backup")


def get_backup_dir() -> Path:
    """Get the backup directory, creating it if needed."""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def create_backup(db_path: str = "pharmgmt.db") -> dict:
    """Create a timestamped backup of the database.

    Args:
        db_path: Path to the SQLite database

    Returns:
        Dict with backup info: {name, path, size_bytes, timestamp}
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"pharmgmt_backup_{timestamp}"
    backup_path = backup_dir / backup_name

    backup_path.mkdir(exist_ok=True)

    # Copy the database
    db_backup = backup_path / "pharmgmt.db"
    shutil.copy2(db_path, db_backup)
    logger.info("Database backed up to %s", db_backup)

    # Copy uploads directory if it exists
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        uploads_backup = backup_path / "uploads"
        shutil.copytree(uploads_dir, uploads_backup, dirs_exist_ok=True)
        logger.info("Uploads directory backed up")

    size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())

    return {
        "name": backup_name,
        "path": str(backup_path),
        "size_bytes": size,
        "timestamp": timestamp,
    }


def restore_backup(backup_name: str, db_path: str = "pharmgmt.db") -> dict:
    """Restore from a backup.

    Args:
        backup_name: Name of the backup folder
        db_path: Path to restore the database to

    Returns:
        Dict with restore info
    """
    backup_dir = get_backup_dir()
    backup_path = backup_dir / backup_name

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_name}")

    db_backup = backup_path / "pharmgmt.db"
    if db_backup.exists():
        shutil.copy2(db_backup, db_path)
        logger.info("Database restored from %s", db_backup)

    uploads_backup = backup_path / "uploads"
    if uploads_backup.exists():
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        shutil.copytree(uploads_backup, uploads_dir, dirs_exist_ok=True)
        logger.info("Uploads restored")

    return {"status": "restored", "backup": backup_name}


def list_backups() -> list[dict]:
    """List available backups.

    Returns:
        List of backup dicts sorted by newest first
    """
    backup_dir = get_backup_dir()
    backups = []

    for entry in sorted(backup_dir.iterdir(), reverse=True):
        if entry.is_dir() and entry.name.startswith("pharmgmt_backup_"):
            size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            backups.append({
                "name": entry.name,
                "path": str(entry),
                "size_bytes": size,
                "timestamp": entry.name.replace("pharmgmt_backup_", ""),
            })

    return backups
