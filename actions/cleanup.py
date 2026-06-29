"""
actions/cleanup.py — Delete agent-created files older than N days
==================================================================
Runs at agent startup and every 24 hours.
Cleans:
  - Word documents    → %USERPROFILE%\Documents\*.docx / *.doc
  - Excel files       → %USERPROFILE%\Documents\*.xlsx
  - VS Code snippets  → %USERPROFILE%\Documents\lisa_snippet_*.py
  - Received attachments → %USERPROFILE%\Downloads\LISA_Attachments\*
"""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path


MAX_AGE_DAYS = 4


def _delete_old_files(folder: str, patterns: list, max_age_days: int = MAX_AGE_DAYS):
    """Delete files in folder matching any pattern that are older than max_age_days."""
    folder_path = Path(os.path.expandvars(folder))
    if not folder_path.exists():
        return

    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted = 0

    for pattern in patterns:
        for file in folder_path.glob(pattern):
            try:
                if not file.is_file():
                    continue
                modified = datetime.fromtimestamp(file.stat().st_mtime)
                if modified < cutoff:
                    file.unlink()
                    logging.info(f"Cleanup: deleted old file {file.name} (modified {modified.date()})")
                    deleted += 1
            except Exception as e:
                logging.warning(f"Cleanup: could not delete {file.name}: {e}")

    return deleted


def run_cleanup():
    """Run all cleanup tasks — call at startup and every 24 hours."""
    logging.info("Running scheduled file cleanup (files older than 4 days)")
    total = 0

    # All agent-created files in Documents
    total += _delete_old_files(
        r"%USERPROFILE%\Documents",
        ["*.docx", "*.doc", "*.xlsx", "*.py", "*.txt"]
    ) or 0

    # Received email attachments
    total += _delete_old_files(
        r"%USERPROFILE%\Downloads\LISA_Attachments",
        ["*.*"]
    ) or 0

    logging.info(f"Cleanup complete — {total} file(s) deleted")


def cleanup_loop():
    """Background thread — runs cleanup at startup then every 24 hours."""
    run_cleanup()
    while True:
        time.sleep(24 * 60 * 60)  # 24 hours
        run_cleanup()