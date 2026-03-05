# Developer Runbook

## Prerequisites
- Python 3.10+
- Git

## Setup

```bash
git clone <repo-url>
cd PharMgmt
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -e ".[dev]"
```

## Initialize Database

```bash
python -m pharmgmt.cli.commands migrate
```

Output: `Database initialized: ./pharmgmt.db` with 12 tables.

## Start Server

```bash
python -m pharmgmt.cli.commands serve
```

Open http://localhost:8000/health — should return `{"status":"ok","version":"0.1.0","schema_version":1}`.

## Ingest a PDF

```bash
python -m pharmgmt.cli.commands ingest path/to/bill.pdf
```

## Run Tests

```bash
pytest tests/ -v
```

## Project Structure

| Path | Purpose |
|------|---------|
| `src/pharmgmt/api/` | FastAPI routes and Pydantic schemas |
| `src/pharmgmt/cli/` | CLI commands (migrate, ingest, serve) |
| `src/pharmgmt/models/` | SQLAlchemy ORM models (12 tables) |
| `src/pharmgmt/parsing/` | PDF parsing engine + normalizers |
| `src/pharmgmt/services/` | Ingestion, text extraction |
| `src/pharmgmt/config.py` | Settings via pydantic-settings |
| `src/pharmgmt/db.py` | DB init, sessions, migrations |
| `src/pharmgmt/main.py` | FastAPI app entry point |
| `tests/` | Pytest test suite |
| `docs/schema.md` | Schema freeze document |

## Database

- **Location**: `./pharmgmt.db` (SQLite)
- **Reset**: delete `pharmgmt.db` and re-run `migrate`
- **Schema version**: tracked in `schema_meta` table

## Configuration

Environment variables (prefix `PHARM_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PHARM_DATABASE_URL` | `sqlite:///./pharmgmt.db` | DB connection |
| `PHARM_UPLOAD_DIR` | `./uploads` | PDF upload directory |
| `PHARM_LOG_DIR` | `./logs` | Log file directory |
| `PHARM_LOG_LEVEL` | `INFO` | Logging level |
| `PHARM_HOST` | `0.0.0.0` | Server host |
| `PHARM_PORT` | `8000` | Server port |
