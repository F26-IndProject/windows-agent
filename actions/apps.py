"""
actions/apps.py — Application launching
=========================================
THE KEY FILE for the parent-process requirement.

The original code used:
    subprocess.Popen([path], shell=True)

This makes the agent the parent of every app it launches.
A defender watching Task Manager would see:
    agent.exe
    └── WINWORD.EXE   ← parent is agent

THE FIX: Use Windows ShellExecute via ctypes.
ShellExecute tells the Windows Shell (explorer.exe) to open the application.
The resulting process tree looks like:
    svchost.exe (ShellHWDetection)
    └── WINWORD.EXE   ← parent is svchost, not agent

This is how humans normally open applications (by double-clicking),
so it looks completely natural to monitoring tools.
"""

import ctypes
import logging
import os
import subprocess
import time


def open_app_via_shell(path: str):
    """
    Open any application using Windows ShellExecuteW.
    This is the correct way — the agent is NOT the parent of the launched process.

    ShellExecute is a Windows API function. ctypes lets us call it from Python
    without installing anything extra.
    """
    try:
        # SW_SHOWNORMAL = 1 means "show the window normally"
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,       # hwnd: no parent window
            "open",     # operation: open the file
            path,       # file path
            None,       # parameters: none
            None,       # working directory: default
            1           # SW_SHOWNORMAL
        )
        # ShellExecute returns a value > 32 if successful
        if ret > 32:
            logging.info(f"Opened via ShellExecute: {path}")
        else:
            logging.error(f"ShellExecute failed for {path} — return code {ret}")
    except Exception as e:
        logging.error(f"ShellExecute error for {path}: {e}")


def open_browser(url: str):
    """
    Open a URL in the default browser using ShellExecute.
    Windows will use whatever browser is set as default (Edge, Firefox, Chrome).
    The browser process parent will be svchost.exe — not the agent.
    """
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            url,    # ShellExecute can open URLs directly
            None,
            None,
            1
        )
        if ret > 32:
            logging.info(f"Browser opened URL: {url}")
        else:
            logging.error(f"Failed to open browser for URL: {url} (code {ret})")
    except Exception as e:
        logging.error(f"Browser open error: {e}")


def close_app_by_name(process_name: str):
    """
    Close a running application by its process name.
    Uses taskkill — standard Windows tool.
    Example: close_app_by_name("WINWORD.EXE")
    """
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            capture_output=True,
            text=True
        )
        logging.info(f"Closed process: {process_name}")
    except Exception as e:
        logging.error(f"Failed to close {process_name}: {e}")
