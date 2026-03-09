---
phase: 5
plan: 2
wave: 1
---

# Plan 5.2: Error Handling & First-Run Experience

## Objective
Add graceful handling of malformed/corrupt PDFs, improve error messages, and build a first-run onboarding flow that guides new users through the system.

## Tasks

<task type="auto">
  <name>Robust PDF error handling</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\text_extraction.py
    c:\PharMgmt\src\pharmgmt\services\ingestion.py
    c:\PharMgmt\src\pharmgmt\parsing\table_parser.py
  </files>
  <action>
    1. text_extraction.py: wrap pdfplumber.open() in try/except for:
       - Corrupt PDFs (generic Exception from pdfplumber)
       - Password-protected PDFs
       - Empty PDFs (0 pages)
       - Return structured error: {error: str, recoverable: bool}
    2. ingestion.py: catch extraction errors, set document status to "error"
       - Store error message in document metadata
       - Don't crash the whole upload on one bad file
    3. table_parser.py: add timeout protection (max 30s per page)
       - If a page takes too long, skip it and flag the document
    4. API upload endpoint: return user-friendly error messages
       - "This PDF appears to be corrupted"
       - "This PDF is password-protected"
       - "No text could be extracted from this PDF"
  </action>
  <verify>
    Upload a corrupt file, an empty file, a non-PDF → verify friendly error messages
  </verify>
  <done>Upload handles all edge cases with clear error messages</done>
</task>

<task type="auto">
  <name>First-run onboarding</name>
  <files>
    c:\PharMgmt\src\pharmgmt\static\js\pages\dashboard.js
    c:\PharMgmt\src\pharmgmt\static\css\components.css
  </files>
  <action>
    1. Detect first run: if /api/stats returns 0 documents, show onboarding
    2. Onboarding flow on dashboard (replaces empty state):
       - Step 1: Welcome message explaining PharMgmt
       - Step 2: "Upload your first bill" with arrow pointing to Upload nav
       - Step 3: "View parsed results" with example of what they'll see
    3. Add a dismissable banner: "Getting Started" with 3 quick tips
    4. Store dismissed state in localStorage so it only shows once
  </action>
  <verify>
    Clear localStorage, open dashboard with empty DB → see onboarding flow
  </verify>
  <done>First-run shows welcoming onboarding, dismissed after interaction</done>
</task>

## Success Criteria
- [ ] Corrupt PDFs show friendly error msg
- [ ] Non-PDF uploads rejected cleanly
- [ ] Password-protected PDFs handled
- [ ] First-run onboarding displays on empty DB
- [ ] Onboarding dismissable and remembered
