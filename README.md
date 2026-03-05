# PharMgmt

Offline-first pharmacy bill management system. Ingests supplier PDF bills in varying formats, extracts structured data, and provides a centralized dashboard for tracking inventory, pricing, expiry, and payments.

## Quick Start

```bash
# 1. Clone and set up
git clone <repo-url>
cd PharMgmt
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -e ".[dev]"

# 2. Initialize database
python -m pharmgmt.cli.commands migrate

# 3. Start server
python -m pharmgmt.cli.commands serve
# Open http://localhost:8000/health

# 4. Ingest a PDF bill
python -m pharmgmt.cli.commands ingest path/to/bill.pdf
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+ / FastAPI |
| Database | SQLite (WAL mode) |
| PDF Parsing | pdfplumber |
| ORM | SQLAlchemy 2.0 |
| Frontend | Local web app (HTML/CSS/JS) |

## Project Structure

```
src/pharmgmt/
├── api/          # FastAPI routes and schemas
├── cli/          # CLI commands (ingest, migrate, serve)
├── models/       # SQLAlchemy ORM models
├── parsing/      # PDF parsing engine
├── services/     # Business logic (ingestion, extraction)
├── config.py     # Application settings
├── db.py         # Database initialization
├── main.py       # FastAPI app entry point
└── logging_config.py
```

## License

MIT
