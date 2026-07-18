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
from actions.apps import kill_process
def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(__file__))
BASE_DIR     = _get_base_dir()
SPAWNER_PATH = os.path.join(BASE_DIR, "spawn.exe")
WFREERDP     = os.path.join(BASE_DIR, "wfreerdp.exe")
SSHPASS_PATH = os.path.join(BASE_DIR, "sshpass.exe")
def connect(target: str, username: str = "", password: str = "", duration_seconds: int = 30):
    if not os.path.exists(WFREERDP):
        logging.error(f"wfreerdp.exe not found at {WFREERDP}")
        return
    if not os.path.exists(SPAWNER_PATH):
        logging.error(f"spawn.exe not found at {SPAWNER_PATH}")
        return
    if not os.path.exists(SSHPASS_PATH):
        logging.error(f"sshpass.exe not found at {SSHPASS_PATH}")
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
        _close_rdp(target, username, password)
    except Exception as e:
        logging.error(f"RDP connect to {target} failed: {e}")
def _close_rdp(target: str, username: str, password: str):
    session_id = None
    try:
        # Step 1 — Get session ID dynamically from the target machine
        # Bypasses interactive console stalls via -q and < NUL, and drops state dependencies via UserKnownHostsFile=NUL
        ssh_query_payload = (
            f'"{SSHPASS_PATH}" -p {password} ssh -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL '
            f'{username}@{target} "query user" < NUL'
        )
        result = subprocess.run(
            ssh_query_payload,
            shell=True, capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if "Active" in line or "Disc" in line:
                parts = line.split()
                # Dynamic index validation handles column collapsing on disconnected states safely
                if len(parts) >= 3 and parts[2].isdigit():
                    session_id = parts[2]
                elif len(parts) >= 2 and parts[1].isdigit():
                    session_id = parts[1]
                break
    except subprocess.TimeoutExpired:
        logging.warning(f"SSH query timed out on {target} — skipping console handoff")
    except Exception as e:
        logging.warning(f"SSH query failed on {target}: {e} — skipping console handoff")
    if session_id:
        try:
            # Step 2 — Hand session back to console dynamically using the discovered ID and %SystemRoot%
            handoff_cmd = f"cmd.exe /c %SystemRoot%\\System32\\tscon.exe {session_id} /dest:console"
            ssh_handoff_payload = (
                f"\"{SSHPASS_PATH}\" -p {password} ssh -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "
                f"{username}@{target} \"{handoff_cmd}\" < NUL"
            )
            subprocess.run(ssh_handoff_payload, shell=True, capture_output=True, timeout=30)
            logging.info(f"Target console session {session_id} successfully returned to local monitor via SSH.")
        except Exception as e:
            logging.warning(f"Console handoff failed on {target}: {e}")
    else:
        logging.info("Could not determine session ID on target — skipping console handoff")
    time.sleep(1)
    kill_process("wfreerdp.exe")
    logging.info("RDP session closed")