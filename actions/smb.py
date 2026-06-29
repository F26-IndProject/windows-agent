"""
actions/smb.py — SMB network share access
==========================================
Simulates realistic user file share behaviour:
- Reading files and logging content
- Editing existing files by appending content
- Creating new files
- Moving files between folders
- Copying files
- Deleting temp files
Generates real SMB/CIFS traffic visible on the network.
"""

import logging
import os
import random
import subprocess
import time
from datetime import datetime


DRIVE_LETTER = "Z:"

EDIT_TEMPLATES = [
    "Updated by team member on {date}. Changes reviewed and approved.",
    "Note added {date}: Please review before end of day.",
    "Revision {date}: Minor corrections applied. Version incremented.",
    "Checked on {date}. All items verified and signed off.",
    "Amendment {date}: Additional information appended per manager request.",
    "Follow-up {date}: Awaiting confirmation from stakeholders.",
    "Review complete {date}: No further changes required at this time.",
]

NEW_FILE_CONTENTS = [
    "Meeting summary\nDate: {date}\nAttendees: team members\nDecisions: approved Q3 plan\nAction items: update timeline by Friday.",
    "Status update\nDate: {date}\nAll tasks on track. No blockers identified. Proceeding as planned.",
    "Incident log\nDate: {date}\nMinor issue detected and resolved. Root cause identified. No further impact expected.",
    "Project note\nDate: {date}\nMilestone reached. Deliverable submitted for review. Awaiting feedback.",
]


def access_share(
    server: str,
    share: str,
    action: str = "browse",
    username: str = "",
    password: str = ""
):
    share_path = f"\\\\{server}\\{share}"

    try:
        _map_share(share_path, username, password)
        time.sleep(2)

        if action == "list":
            _list_share()
        elif action == "read":
            _read_all_files()
        elif action == "write":
            _create_new_file()
        elif action == "edit":
            _edit_existing_file()
        elif action == "browse":
            # Full realistic session — all operations
            _list_share()
            time.sleep(random.randint(2, 4))
            _read_all_files()
            time.sleep(random.randint(2, 4))
            _edit_existing_file()
            time.sleep(random.randint(2, 4))
            _create_new_file()
            time.sleep(random.randint(2, 4))
            _copy_file()

        time.sleep(random.randint(5, 15))

    except Exception as e:
        logging.error(f"SMB access failed for {share_path}: {e}")

    finally:
        _unmap_share()


def _map_share(share_path: str, username: str, password: str):
    subprocess.run(["net", "use", DRIVE_LETTER, "/delete", "/yes"], capture_output=True)
    time.sleep(1)

    cmd = ["net", "use", DRIVE_LETTER, share_path]
    if username:
        cmd += [f"/user:{username}", password]
    cmd += ["/persistent:no"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        logging.info(f"Mapped {share_path} to {DRIVE_LETTER}")
    else:
        logging.error(f"Failed to map share: {result.stderr}")
        raise RuntimeError(f"net use failed: {result.stderr}")


def _list_share():
    """List all files and folders on the share."""
    try:
        items = os.listdir(f"{DRIVE_LETTER}\\")
        logging.info(f"Share contents ({len(items)} items): {', '.join(items)}")
    except Exception as e:
        logging.error(f"Share listing failed: {e}")


def _read_all_files():
    """Read every text file on the share and log its full content."""
    try:
        files = [
            f for f in os.listdir(f"{DRIVE_LETTER}\\")
            if os.path.isfile(f"{DRIVE_LETTER}\\{f}")
            and os.path.splitext(f)[1].lower() in [".txt", ".md", ".csv", ".log"]
        ]

        if not files:
            logging.info("No readable text files found on share")
            return

        for filename in files:
            path = f"{DRIVE_LETTER}\\{filename}"
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                logging.info(
                    f"Read file: {filename} ({len(content)} chars)\n"
                    f"--- content ---\n{content.strip()[:200]}\n--- end ---"
                )
                time.sleep(random.randint(2, 5))
            except Exception as e:
                logging.error(f"Could not read {filename}: {e}")

    except Exception as e:
        logging.error(f"Share read failed: {e}")


def _edit_existing_file():
    """Pick a random existing file and append realistic content to it."""
    try:
        files = [
            f for f in os.listdir(f"{DRIVE_LETTER}\\")
            if os.path.isfile(f"{DRIVE_LETTER}\\{f}")
            and os.path.splitext(f)[1].lower() in [".txt", ".md"]
        ]

        if not files:
            logging.info("No editable files found on share — skipping edit")
            return

        filename = random.choice(files)
        path = f"{DRIVE_LETTER}\\{filename}"

        addition = random.choice(EDIT_TEMPLATES).format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        # Reset file if it has grown too large (over 2KB)
        if os.path.getsize(path) > 2048:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"File reset on {datetime.now().strftime('%Y-%m-%d')}\n")
            logging.info(f"Reset oversized file on share: {filename}")
            return

        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n{addition}")

        logging.info(f"Edited file on share: {filename} — appended: {addition}")

    except Exception as e:
        logging.error(f"Share edit failed: {e}")


def _create_new_file():
    """Create a new timestamped file on the share then delete it."""
    try:
        filename = f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = f"{DRIVE_LETTER}\\{filename}"

        content = random.choice(NEW_FILE_CONTENTS).format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"Created file on share: {filename}\n--- content ---\n{content}\n--- end ---")

        time.sleep(random.randint(3, 8))
        os.remove(path)
        logging.info(f"Deleted temp file from share: {filename}")

    except Exception as e:
        logging.error(f"Share write failed: {e}")


def _copy_file():
    """Copy an existing file to a new name — simulates file copy operation."""
    try:
        files = [
            f for f in os.listdir(f"{DRIVE_LETTER}\\")
            if os.path.isfile(f"{DRIVE_LETTER}\\{f}")
            and os.path.splitext(f)[1].lower() in [".txt", ".md"]
        ]

        if not files:
            return

        src_name = random.choice(files)
        src_path = f"{DRIVE_LETTER}\\{src_name}"
        base, ext = os.path.splitext(src_name)
        dst_name = f"{base}_copy_{datetime.now().strftime('%H%M%S')}{ext}"
        dst_path = f"{DRIVE_LETTER}\\{dst_name}"

        import shutil
        shutil.copy2(src_path, dst_path)
        logging.info(f"Copied file on share: {src_name} → {dst_name}")

        time.sleep(random.randint(2, 5))
        os.remove(dst_path)
        logging.info(f"Deleted copy from share: {dst_name}")

    except Exception as e:
        logging.error(f"Share copy failed: {e}")


def _unmap_share():
    try:
        subprocess.run(
            ["net", "use", DRIVE_LETTER, "/delete", "/yes"],
            capture_output=True, timeout=10
        )
        logging.info(f"Unmapped {DRIVE_LETTER}")
    except Exception as e:
        logging.error(f"Failed to unmap share: {e}")
