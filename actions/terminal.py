"""
actions/terminal.py — Terminal command execution
==================================================
Runs PowerShell and CMD commands in a way that:
1. Runs them in a NEW window (so a user watching the screen sees a terminal open)
2. Uses ShellExecute so the terminal's parent is svchost, not the agent
3. Logs what was run and the result

For admin-role agents, this is where scheduled task creation,
registry queries, and service management commands run.
"""

import ctypes
import logging
import subprocess
import time


def run_powershell(command: str, visible: bool = True):
    """
    Run a PowerShell command.
    If visible=True, a PowerShell window opens on screen (realistic).
    If visible=False, runs hidden in background (for cleanup tasks).
    """
    try:
        if visible:
            # Use ShellExecute to open PowerShell visibly
            # /K means "run command and keep window open"
            # /C means "run command and close window"
            full_cmd = f'powershell.exe -NoExit -Command "{command}"'
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                "powershell.exe",
                f'-NoExit -Command "{command}"',
                None,
                1   # SW_SHOWNORMAL — show the window
            )
            if ret > 32:
                logging.info(f"PowerShell command started: {command}")
            else:
                logging.error(f"ShellExecute failed for PowerShell (code {ret})")

            # Let it run for a realistic duration before moving on
            time.sleep(5)

        else:
            # Hidden execution — capture output for logging
            result = subprocess.run(
                ["powershell.exe", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            logging.info(f"PowerShell (hidden) '{command}' → {result.stdout[:200]}")

    except Exception as e:
        logging.error(f"PowerShell command failed '{command}': {e}")


def run_cmd(command: str, visible: bool = True):
    """
    Run a CMD command. Same approach as PowerShell.
    """
    try:
        if visible:
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                "cmd.exe",
                f'/K "{command}"',
                None,
                1
            )
            if ret > 32:
                logging.info(f"CMD command started: {command}")
            else:
                logging.error(f"ShellExecute failed for CMD (code {ret})")

            time.sleep(4)

        else:
            result = subprocess.run(
                ["cmd.exe", "/C", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            logging.info(f"CMD (hidden) '{command}' → {result.stdout[:200]}")

    except Exception as e:
        logging.error(f"CMD command failed '{command}': {e}")
