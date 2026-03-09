---
phase: 5
plan: 3
wave: 2
---

# Plan 5.3: Backup & Retention

## Objective
Add manual DB backup/restore via CLI and API, and a configurable retention policy for old raw PDFs and extracted text data.

## Tasks

<task type="auto">
  <name>Backup and restore</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\backup.py
    c:\PharMgmt\src\pharmgmt\cli\commands.py
    c:\PharMgmt\src\pharmgmt\api\routes.py
  </files>
  <action>
    Create backup.py service:
    - `create_backup(db_path, backup_dir)` → copies SQLite DB + raw_files dir to timestamped folder
    - `restore_backup(backup_path, db_path)` → restores from backup
    - `list_backups(backup_dir)` → returns available backups with dates/sizes

    CLI commands:
    - `pharmgmt backup` → creates backup to configured backup dir
    - `pharmgmt restore <backup_name>` → restores from backup
    - `pharmgmt backups` → lists available backups

    API endpoints:
    - `POST /api/backup` → trigger backup, return path
    - `GET /api/backups` → list backups

    Add backup button to dashboard sidebar footer
  </action>
  <verify>
    Run `pharmgmt backup` → verify backup created → `pharmgmt backups` → verify listed
  </verify>
  <done>Backup/restore via CLI and API</done>
</task>

<task type="auto">
  <name>Retention policy</name>
  <files>
    c:\PharMgmt\src\pharmgmt\services\retention.py
    c:\PharMgmt\src\pharmgmt\config.py
  </files>
  <action>
    Create retention.py:
    - `cleanup_old_data(session, raw_days=90, text_days=180)`:
      - Delete RawFile records older than raw_days
      - Delete ExtractedText older than text_days
      - Keep Document + LineItem records forever (archival)
    - Configurable via config.py: RAW_RETENTION_DAYS, TEXT_RETENTION_DAYS

    Add CLI command: `pharmgmt cleanup` → runs retention policy
    Add to settings: retention config with defaults (90d raw, 180d text)
  </action>
  <verify>
    .venv\Scripts\python -m pytest tests/ -v --tb=short
  </verify>
  <done>Retention policy cleans old raw data while preserving parsed records</done>
</task>

## Success Criteria
- [ ] Backup creates timestamped copies
- [ ] Restore works from backup
- [ ] CLI commands: backup, restore, backups, cleanup
- [ ] Retention deletes old raw data per config
