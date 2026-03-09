---
phase: 5
plan: 4
wave: 2
---

# Plan 5.4: PyInstaller Packaging

## Objective
Package PharMgmt as a single Windows executable using PyInstaller so the user can run it without Python installed.

## Tasks

<task type="auto">
  <name>PyInstaller configuration and build</name>
  <files>
    c:\PharMgmt\pharmgmt.spec
    c:\PharMgmt\build.py
  </files>
  <action>
    1. Install PyInstaller: `pip install pyinstaller`
    2. Create build.py launcher script:
       - Opens browser to http://localhost:8000
       - Starts uvicorn server
       - Handles Ctrl+C gracefully
    3. Create pharmgmt.spec:
       - Include all static files (HTML, CSS, JS)
       - Include YAML mapping configs
       - Include SQLAlchemy + pdfplumber dependencies
       - Single-file or one-directory mode
    4. Add to pyproject.toml: `[project.scripts]` entry
    5. Build: `pyinstaller pharmgmt.spec`
    6. Test the built exe — ensure it:
       - Starts the server
       - Opens dashboard
       - Can upload and parse a PDF
  </action>
  <verify>
    Build the exe and run it — verify server starts and UI loads
  </verify>
  <done>Single executable packaging working</done>
</task>

## Success Criteria
- [ ] PyInstaller spec configured
- [ ] Build produces working executable
- [ ] Exe starts server and opens browser
- [ ] All features work from the packaged exe
