"""
actions/rdp.py — RDP via FreeRDP (wfreerdp.exe)
wfreerdp.exe must be placed in the WinAgent root folder alongside spawn.exe.
/cert:ignore bypasses all certificate and identity dialogs on any Windows version.
"""

import logging
import os
import subprocess
import sys
import time


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(__file__))

BASE_DIR     = _get_base_dir()
SPAWNER_PATH = os.path.join(BASE_DIR, "spawn.exe")
WFREERDP     = os.path.join(BASE_DIR, "wfreerdp.exe")


def connect(target: str, username: str = "", password: str = "", duration_seconds: int = 30):
    if not os.path.exists(WFREERDP):
        logging.error(f"wfreerdp.exe not found at {WFREERDP}")
        return

    try:
        # Build args — /cert:ignore bypasses all cert/identity dialogs
        # /log-level:ERROR suppresses deprecation noise in output
        args = (
            f"/v:{target}"
            f" /u:{username}"
            f" /p:{password}"
            f" /cert:ignore"
            f" /log-level:ERROR"
        )

        subprocess.Popen(
            [SPAWNER_PATH, WFREERDP, args, BASE_DIR],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"RDP session opened to {target} — holding for {duration_seconds}s")

        time.sleep(duration_seconds)
        _close_rdp()

    except Exception as e:
        logging.error(f"RDP connect to {target} failed: {e}")


def _close_rdp():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "wfreerdp.exe"],
            capture_output=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info("RDP session closed")
    except Exception as e:
        logging.error(f"Failed to close RDP session: {e}")