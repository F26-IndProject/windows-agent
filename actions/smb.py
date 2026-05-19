"""
actions/smb.py — SMB network share access
==========================================
Simulates a user accessing a network file share.
Uses standard Windows net use commands and file operations.
Generates real SMB/CIFS traffic on the network which is
exactly what the customer asked for.

WHY THIS MATTERS:
In a cyber range, defenders use tools like Wireshark, Suricata,
or Zeek to watch network traffic. Without SMB traffic, the network
looks suspicious — real office networks have constant file share access.
This makes the simulation look authentic.

HOW IT WORKS:
1. Maps the share using "net use" (like a user mapping a network drive)
2. Performs file operations (list, read, write, delete)
3. Disconnects the share
"""

import logging
import os
import random
import subprocess
import time
from datetime import datetime


# The drive letter we'll temporarily map the share to
# Z: is rarely used so unlikely to conflict
DRIVE_LETTER = "Z:"


def access_share(
    server: str,
    share: str,
    action: str = "list",
    username: str = "",
    password: str = ""
):
    """
    Access an SMB share and perform a file operation.

    server   — IP or hostname of the file server
    share    — name of the share (e.g., "documents" maps to \\server\documents)
    action   — what to do: "list", "read", "write", "browse"
    username — leave empty for guest/current user
    password — leave empty for current user's credentials
    """
    share_path = f"\\\\{server}\\{share}"

    try:
        # Step 1: Map the share to a drive letter
        _map_share(share_path, username, password)
        time.sleep(2)

        # Step 2: Perform the requested action
        if action == "list":
            _list_share()
        elif action == "read":
            _read_from_share()
        elif action == "write":
            _write_to_share()
        elif action == "browse":
            # Do all of the above in sequence
            _list_share()
            time.sleep(2)
            _read_from_share()
            time.sleep(2)
            _write_to_share()

        # Step 3: Wait a bit (simulates user looking at files)
        time.sleep(random.randint(5, 15))

    except Exception as e:
        logging.error(f"SMB access failed for {share_path}: {e}")

    finally:
        # Always disconnect the share when done
        _unmap_share()


def _map_share(share_path: str, username: str, password: str):
    """Map the network share to drive letter Z:"""
    # First try to disconnect any existing Z: mapping
    subprocess.run(
        ["net", "use", DRIVE_LETTER, "/delete", "/yes"],
        capture_output=True
    )
    time.sleep(1)

    # Build the net use command
    cmd = ["net", "use", DRIVE_LETTER, share_path]
    if username:
        cmd += [f"/user:{username}", password]
    cmd += ["/persistent:no"]   # Don't save across reboots

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    if result.returncode == 0:
        logging.info(f"Mapped {share_path} to {DRIVE_LETTER}")
    else:
        logging.error(f"Failed to map share: {result.stderr}")
        raise RuntimeError(f"net use failed: {result.stderr}")


def _list_share():
    """List files on the mapped share — generates SMB directory listing traffic."""
    try:
        result = subprocess.run(
            ["dir", f"{DRIVE_LETTER}\\"],
            capture_output=True, text=True, shell=True, timeout=10
        )
        logging.info(f"Listed share contents: {result.stdout[:300]}")
    except Exception as e:
        logging.error(f"Share listing failed: {e}")


def _read_from_share():
    """Try to read a file from the share — generates SMB read traffic."""
    try:
        # Try to read common filenames
        candidates = [
            f"{DRIVE_LETTER}\\readme.txt",
            f"{DRIVE_LETTER}\\notes.txt",
            f"{DRIVE_LETTER}\\info.txt",
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(500)
                logging.info(f"Read from share: {path} ({len(content)} chars)")
                return
        logging.info("No readable files found on share (this is normal)")
    except Exception as e:
        logging.error(f"Share read failed: {e}")


def _write_to_share():
    """Write a file to the share — generates SMB write traffic."""
    try:
        filename = f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = f"{DRIVE_LETTER}\\{filename}"
        content = (
            f"Status update\n"
            f"Created: {datetime.now().isoformat()}\n"
            f"User: active session\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Wrote to share: {path}")

        # Clean up after ourselves
        time.sleep(2)
        os.remove(path)
        logging.info(f"Removed temp file from share: {path}")

    except Exception as e:
        logging.error(f"Share write failed: {e}")


def _unmap_share():
    """Disconnect the mapped share."""
    try:
        subprocess.run(
            ["net", "use", DRIVE_LETTER, "/delete", "/yes"],
            capture_output=True, timeout=10
        )
        logging.info(f"Unmapped {DRIVE_LETTER}")
    except Exception as e:
        logging.error(f"Failed to unmap share: {e}")
