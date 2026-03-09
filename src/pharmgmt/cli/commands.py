"""CLI commands for PharMgmt."""

import argparse
import os
import sys

from pharmgmt import __version__


def cmd_version(args):
    """Print version info."""
    print(f"PharMgmt v{__version__}")

    from pharmgmt.config import get_settings
    settings = get_settings()
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    if os.path.exists(db_path):
        try:
            from pharmgmt.db import check_schema_version
            sv = check_schema_version(settings.DATABASE_URL)
            print(f"Schema version: {sv}")
            print(f"Database: {db_path}")
        except Exception as e:
            print(f"Database: {db_path} (error reading: {e})")
    else:
        print("Database: not initialized (run 'migrate' first)")


def cmd_migrate(args):
    """Initialize or migrate the database."""
    from pharmgmt.config import get_settings
    from pharmgmt.db import init_db
    from pharmgmt.logging_config import setup_logging

    settings = get_settings()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    init_db(settings.DATABASE_URL)

    # Count tables
    import sqlite3
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()

    print(f"Database initialized: {db_path}")
    print(f"Tables: {len(tables)}")
    print(f"Schema version: 1")


def cmd_ingest(args):
    """Ingest a PDF file."""
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.lower().endswith(".pdf"):
        print(f"Error: Only PDF files are supported", file=sys.stderr)
        sys.exit(1)

    from pharmgmt.config import get_settings
    from pharmgmt.db import init_db, get_db_session
    from pharmgmt.logging_config import setup_logging
    from pharmgmt.services.ingestion import ingest_pdf

    settings = get_settings()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    init_db(settings.DATABASE_URL)

    file_name = os.path.basename(file_path)
    with get_db_session(settings.DATABASE_URL) as session:
        result = ingest_pdf(session, file_path, file_name)

    if result["status"] == "success":
        print(f"Ingested: {file_name}")
        print(f"Document ID: {result['document_id']}")
        print(f"Pages extracted: {result['pages_extracted']}")
    elif result["status"] == "duplicate":
        print(f"Duplicate: {file_name}")
        print(f"Already ingested as: {result['existing_document_id']}")
        sys.exit(1)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


def cmd_serve(args):
    """Start the web server."""
    from pharmgmt.config import get_settings
    import uvicorn

    settings = get_settings()
    host = args.host or settings.HOST
    port = args.port or settings.PORT

    print(f"Starting PharMgmt server at http://{host}:{port}")
    print(f"Press Ctrl+C to stop")
    uvicorn.run("pharmgmt.main:app", host=host, port=port, reload=False)


def cmd_backup(args):
    """Create a database backup."""
    from pharmgmt.services.backup import create_backup
    try:
        result = create_backup()
        print(f"Backup created: {result['name']}")
        print(f"Path: {result['path']}")
        print(f"Size: {result['size_bytes'] / 1024:.1f} KB")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_backups(args):
    """List available backups."""
    from pharmgmt.services.backup import list_backups
    backups = list_backups()
    if not backups:
        print("No backups found")
        return
    for b in backups:
        print(f"  {b['name']}  ({b['size_bytes'] / 1024:.1f} KB)")


def cmd_restore(args):
    """Restore from a backup."""
    from pharmgmt.services.backup import restore_backup
    try:
        result = restore_backup(args.name)
        print(f"Restored from: {args.name}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_cleanup(args):
    """Run retention policy — delete old raw data."""
    from pharmgmt.config import get_settings
    from pharmgmt.db import init_db, get_db_session
    from pharmgmt.services.retention import cleanup_old_data

    settings = get_settings()
    init_db(settings.DATABASE_URL)
    with get_db_session(settings.DATABASE_URL) as session:
        result = cleanup_old_data(session, raw_days=args.raw_days, text_days=args.text_days)
    print(f"Raw files deleted: {result['raw_files_deleted']}")
    print(f"Extracted texts deleted: {result['extracted_texts_deleted']}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pharmgmt",
        description="PharMgmt — Pharmacy Bill Management System",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # version
    subparsers.add_parser("version", help="Show version info")

    # migrate
    subparsers.add_parser("migrate", help="Initialize or migrate the database")

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF bill")
    ingest_parser.add_argument("file", help="Path to the PDF file")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the web server")
    serve_parser.add_argument("--host", default=None, help="Host (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=None, help="Port (default: 8000)")

    # backup
    subparsers.add_parser("backup", help="Create a database backup")

    # backups
    subparsers.add_parser("backups", help="List available backups")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument("name", help="Backup name to restore")

    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Run retention policy")
    cleanup_parser.add_argument("--raw-days", type=int, default=90, help="Days to keep raw PDFs (default: 90)")
    cleanup_parser.add_argument("--text-days", type=int, default=180, help="Days to keep extracted text (default: 180)")

    args = parser.parse_args()

    if args.command == "version":
        cmd_version(args)
    elif args.command == "migrate":
        cmd_migrate(args)
    elif args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "backup":
        cmd_backup(args)
    elif args.command == "backups":
        cmd_backups(args)
    elif args.command == "restore":
        cmd_restore(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

