---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Project Scaffold & Configuration

## Objective
Set up the Python project structure with proper packaging, dependencies, configuration, and code style rules. This is the foundation every other plan builds on.

## Context
- .gsd/SPEC.md — Tech stack (Python 3.10+, FastAPI, SQLite, pdfplumber, SQLAlchemy)
- .gsd/ROADMAP.md — Phase 1 deliverables

## Tasks

<task type="auto">
  <name>Create project directory structure</name>
  <files>
    c:\PharMgmt\src\pharmgmt\__init__.py
    c:\PharMgmt\src\pharmgmt\config.py
    c:\PharMgmt\src\pharmgmt\main.py
    c:\PharMgmt\src\pharmgmt\models\__init__.py
    c:\PharMgmt\src\pharmgmt\api\__init__.py
    c:\PharMgmt\src\pharmgmt\parsing\__init__.py
    c:\PharMgmt\src\pharmgmt\cli\__init__.py
    c:\PharMgmt\tests\__init__.py
    c:\PharMgmt\tests\conftest.py
  </files>
  <action>
    Create the src layout with these packages:
    - `pharmgmt/` — root package
    - `pharmgmt/models/` — SQLAlchemy models
    - `pharmgmt/api/` — FastAPI routes
    - `pharmgmt/parsing/` — PDF parsing engine (Phase 2)
    - `pharmgmt/cli/` — CLI commands
    - `tests/` — test directory with conftest.py

    In `config.py`:
    - Use pydantic-settings for configuration
    - Define: DATABASE_URL (default: sqlite:///./pharmgmt.db), UPLOAD_DIR (default: ./uploads), LOG_DIR (default: ./logs), LOG_LEVEL (default: INFO)
    - Load from environment variables with `PHARM_` prefix
    - Load from optional `.env` file

    In `__init__.py` (root):
    - Set `__version__ = "0.1.0"`
  </action>
  <verify>
    python -c "from pharmgmt.config import Settings; s = Settings(); print(s.DATABASE_URL)"
  </verify>
  <done>All packages importable, Settings loads defaults successfully</done>
</task>

<task type="auto">
  <name>Create project metadata and dependency files</name>
  <files>
    c:\PharMgmt\pyproject.toml
    c:\PharMgmt\.gitignore
    c:\PharMgmt\README.md
  </files>
  <action>
    Create `pyproject.toml` with:
    - Project name: pharmgmt
    - Python requires: >=3.10
    - Dependencies: fastapi, uvicorn[standard], sqlalchemy, pdfplumber, pydantic, pydantic-settings, python-multipart, aiofiles
    - Dev dependencies: pytest, pytest-asyncio, httpx (for testing FastAPI)
    - Entry point: pharmgmt-cli = "pharmgmt.cli:main"

    Create `.gitignore` with Python defaults + project-specific:
    - __pycache__, .venv, *.pyc, .env
    - pharmgmt.db, uploads/, logs/
    - .gsd/STATE.md, .gsd/JOURNAL.md, .gsd/TODO.md

    Create `README.md` with:
    - Project name and one-line description
    - Quick start: install, run migrations, start server
    - Tech stack summary
  </action>
  <verify>
    Test-Path "c:\PharMgmt\pyproject.toml"
    Test-Path "c:\PharMgmt\.gitignore"
    Test-Path "c:\PharMgmt\README.md"
  </verify>
  <done>pyproject.toml valid, .gitignore covers all generated files, README has setup instructions</done>
</task>

<task type="auto">
  <name>Create virtual environment and install dependencies</name>
  <files>
    c:\PharMgmt\.venv\
  </files>
  <action>
    Create a Python virtual environment:
    - `python -m venv .venv`
    - Activate and install: `pip install -e ".[dev]"`
    - Verify all imports work

    DO NOT commit .venv to git.
  </action>
  <verify>
    .venv\Scripts\python -c "import fastapi; import sqlalchemy; import pdfplumber; print('All imports OK')"
  </verify>
  <done>Virtual environment created, all dependencies installed and importable</done>
</task>

## Success Criteria
- [ ] Project directory structure matches src layout
- [ ] pyproject.toml is valid and installable
- [ ] All dependencies install cleanly
- [ ] Settings class loads defaults
- [ ] .gitignore covers generated files
