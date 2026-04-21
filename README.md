# PharMgmt — Pharmacy supply chain Bill Management System

> Offline-first pharmacy bill management for Indian pharmacies. Upload supplier PDFs, auto-parse product data, track expiry, compare prices, generate reports.

## ✨ Features

- **PDF Parsing** — Drag-and-drop upload with automatic table extraction and text-line fallback
- **Bill Management** — Search, filter, sort bills with confidence scoring
- **Expiry Alerts** — 30/60/90 day warnings with severity color coding
- **Price Analytics** — Track price changes and compare suppliers
- **Payment Tracking** — Record payments, track paid/partial/unpaid status
- **Reports** — Purchase reports, stock summaries, sanity checks with CSV export
- **Backup & Restore** — Timestamped backups via CLI or API

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Initialize database
python -m pharmgmt.cli.commands migrate

# Start server
python -m pharmgmt.cli.commands serve

# Open browser → http://localhost:8000
```

## 📸 Dashboard

Dark glassmorphism UI with 9 pages: Dashboard, Bills, Bill Detail, Upload, Products, Staging Review, Alerts, Analytics, Reports.

## 🛠 CLI Commands

```bash
pharmgmt version          # Show version
pharmgmt migrate          # Init/migrate database
pharmgmt serve            # Start web server
pharmgmt ingest <file>    # Ingest a PDF
pharmgmt backup           # Create backup
pharmgmt backups          # List backups
pharmgmt restore <name>   # Restore from backup
pharmgmt cleanup          # Run retention policy
```

## 🏗 Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite (WAL mode) |
| PDF | pdfplumber (text + table extraction) |
| Frontend | Vanilla HTML/CSS/JS (no build step) |
| Design | Dark glassmorphism, Inter font, CSS custom properties |

## 📁 Project Structure

```
src/pharmgmt/
├── api/          # FastAPI routes, schemas, dependencies
├── cli/          # CLI commands (serve, ingest, backup, etc.)
├── models/       # SQLAlchemy ORM models
├── parsing/      # PDF parser, column resolver, confidence scoring
├── services/     # Business logic (ingestion, alerts, analytics, reports)
└── static/       # Frontend SPA (HTML, CSS, JS)
    ├── css/      # Design system (index, components, responsive)
    └── js/       # SPA router, API client, page renderers
```

## 📖 Documentation

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the complete user guide.

## License

MIT
