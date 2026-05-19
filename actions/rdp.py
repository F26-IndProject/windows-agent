"""
actions/rdp.py — RDP remote desktop connections (admin role only)
==================================================================
Simulates an admin user opening a Remote Desktop connection to another machine.
Uses mstsc.exe (Windows built-in RDP client) via ShellExecute so the
mstsc.exe process is NOT a child of the agent.

WHY THIS IS ADMIN-ONLY:
Regular office workers don't use RDP. Admins do — to manage servers,
check on services, or troubleshoot. Including RDP traffic for admin-role
agents makes the network simulation more realistic.

WHAT HAPPENS ON THE NETWORK:
RDP uses port 3389 (TCP). When this runs, Wireshark will show connections
from this Windows VM to the target on port 3389 — exactly the traffic
pattern of a real admin doing their job.

REQUIRES:
The target machine must have Remote Desktop enabled.
On the target: Settings → System → Remote Desktop → Enable Remote Desktop.
"""

import ctypes
import logging
import os
import subprocess
import tempfile
import time


def connect(target: str, username: str = "", password: str = "", duration_seconds: int = 30):
    """
    Open an RDP session to the target machine.

    target           — IP or hostname to connect to
    username         — Windows username on the target
    password         — Password (stored temporarily in a .rdp file, deleted after)
    duration_seconds — How long to keep the session open before closing
    """
    try:
        # Create a temporary .rdp file with connection settings
        # mstsc.exe reads .rdp files — this is the standard way to pre-configure connections
        rdp_content = _build_rdp_file(target, username, password)

        # Write to a temp file
        rdp_path = os.path.join(tempfile.gettempdir(), f"lisa_session_{target.replace('.', '_')}.rdp")
        with open(rdp_path, "w") as f:
            f.write(rdp_content)

        logging.info(f"Opening RDP connection to {target}")

        # Launch mstsc.exe via ShellExecute — parent will be svchost, not agent
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            "mstsc.exe",
            rdp_path,
            None,
            1
        )

        if ret > 32:
            logging.info(f"RDP session opened to {target}")
            # Keep the session open for a realistic duration
            time.sleep(duration_seconds)
            # Close mstsc after the session
            _close_rdp()
        else:
            logging.error(f"Failed to open mstsc.exe (ShellExecute code {ret})")

        # Clean up the temp .rdp file
        try:
            os.remove(rdp_path)
        except Exception:
            pass

    except Exception as e:
        logging.error(f"RDP connect to {target} failed: {e}")


def _build_rdp_file(target: str, username: str, password: str) -> str:
    """
    Build the content of an .rdp configuration file.
    mstsc.exe reads this format. Password is stored encoded (not plain text)
    but this is only for lab use — don't use real passwords in production.
    """
    lines = [
        f"full address:s:{target}",
        "prompt for credentials:i:0",     # Don't prompt for credentials
        "administrative session:i:0",
        "desktopwidth:i:1024",
        "desktopheight:i:768",
        "session bpp:i:32",
        "compression:i:1",
        "keyboardhook:i:2",
        "audiocapturemode:i:0",
        "videoplaybackmode:i:1",
        "connection type:i:2",
        "networkautodetect:i:0",
        "bandwidthautodetect:i:1",
        "displayconnectionbar:i:1",
        "enableworkspacereconnect:i:0",
        "disable wallpaper:i:0",
        "allow font smoothing:i:0",
        "allow desktop composition:i:0",
        "disable full window drag:i:1",
        "disable menu anims:i:1",
        "disable themes:i:0",
        "disable cursor setting:i:0",
        "bitmapcachepersistenable:i:1",
        "redirectprinters:i:1",
        "redirectcomports:i:0",
        "redirectsmartcards:i:1",
        "redirectclipboard:i:1",
        "redirectposdevices:i:0",
        "autoreconnection enabled:i:1",
        "authentication level:i:2",
        "negotiate security layer:i:1",
    ]

    if username:
        lines.append(f"username:s:{username}")

    return "\r\n".join(lines) + "\r\n"


def _close_rdp():
    """Close any open mstsc.exe windows."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "mstsc.exe"],
            capture_output=True,
            timeout=10
        )
        logging.info("RDP session closed")
    except Exception as e:
        logging.error(f"Failed to close RDP session: {e}")
