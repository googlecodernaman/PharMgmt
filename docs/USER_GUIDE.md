# PharMgmt User Guide

## Getting Started

### First Upload

1. Open **http://localhost:8000** — you'll see the Dashboard with a welcome guide
2. Click **Upload** in the sidebar (or the "Upload Your First Bill" button)
3. Drag-and-drop a PDF bill, or click to browse
4. Wait for parsing — you'll see extracted line items with confidence scores
5. Click **View Bill** to see the full detail

### Understanding the Dashboard

The dashboard shows 4 key metrics:
- **Total Bills** — number of uploaded documents
- **Line Items** — total parsed product rows across all bills
- **Needs Review** — documents with low confidence flagged for manual check
- **Avg Confidence** — overall parsing accuracy

## How Parsing Works

### Bill Types

PharMgmt supports Stock & Sales reports common to Indian pharmacy distributors. The parser:

1. **Extracts text** using pdfplumber (handles both structured tables and plain text)
2. **Auto-detects bill type** from header keywords and column names
3. **Maps columns** to canonical fields (product, packing, qty, price, expiry, etc.)
4. **Scores confidence** per row (0-100%) based on data quality
5. **Flags issues** — arithmetic mismatches, missing fields, low confidence rows

### Text-Line Fallback

Many Indian pharmacy PDFs use space-delimited text instead of proper tables. PharMgmt automatically falls back to a text-line parser that:
- Scans lines for numeric trailing values
- Splits product name and packing from the text prefix
- Maps 8+ values to opening/receipt/issue/closing qty/value

### Confidence Scoring

- **Green (≥80%)** — High confidence, data likely correct
- **Yellow (50-80%)** — Medium, review recommended
- **Red (<50%)** — Low confidence, manual verification needed

## Core Features

### Bills

View all uploaded documents with search, filter, and sort. Click any bill to see:
- **Line Items tab** — parsed product rows with confidence bars
- **Raw Text tab** — original PDF text for verification
- **CSV Export** — download line items as spreadsheet

### Products

Aggregated view of all products across bills — pack sizes, latest stock, prices.

### Staging Review

Documents flagged for manual review appear here. You can **Accept** (convert staged rows to confirmed line items) or **Reject** (discard).

### Alerts

Expiry monitoring grouped by severity:
- 🔴 **Expired** — past expiry date
- 🟠 **< 30 Days** — critical, needs immediate attention
- 🟡 **< 60 Days** — approaching expiry
- 🔵 **< 90 Days** — early warning

### Analytics

- **Price Changes** — products with price increases/decreases across bills
- **Product Prices** — search a product to see its full price history

### Reports

Three report types with CSV export:
- **Purchase Report** — all purchases grouped by supplier and product
- **Stock Summary** — current stock levels and values
- **Sanity Report** — parsing issues and flagged documents

## Backup & Restore

### Via Dashboard
Click the backup button in the sidebar or use the API.

### Via CLI

```bash
# Create a backup
pharmgmt backup

# List backups
pharmgmt backups

# Restore
pharmgmt restore pharmgmt_backup_20260309_092300
```

### Retention Policy

Clean up old raw PDF data to save disk space:

```bash
# Default: keep raw PDFs 90 days, text 180 days
pharmgmt cleanup

# Custom retention
pharmgmt cleanup --raw-days 30 --text-days 60
```

> **Note:** Cleanup only deletes raw PDF bytes and extracted text. Parsed records (documents, line items, payments) are kept forever.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No line items" after upload | Check Staging Review — the document may need manual review |
| Upload fails | Ensure file is a valid PDF (not password-protected or corrupt) |
| Slow performance | Run `pharmgmt cleanup` to delete old data |
| Need fresh start | Delete `pharmgmt.db` and run `pharmgmt migrate` |
