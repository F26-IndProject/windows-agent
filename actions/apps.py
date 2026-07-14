import logging
import subprocess
import os
import sys
import time
import random

EDGE_PATH    = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ACROBAT_PATH = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"

# Edge session directory — deleting these prevents tab restore after close
EDGE_SESSION_DIR = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default"
)


def get_spawner_path():
    if getattr(sys, 'frozen', False):
        exe_dir  = os.path.dirname(sys.executable)
        base_dir = os.path.dirname(exe_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, "spawn.exe")

SPAWNER_PATH = get_spawner_path()
TASKKILL_PATH = r"C:\Windows\System32\taskkill.exe"
SYSTEM32      = r"C:\Windows\System32"


def kill_process(process_name: str, tree: bool = False):
    """Kill a process by name via spawn.exe so agent.exe is not the parent."""
    args = f"/F /IM {process_name}"
    if tree:
        args += " /T"
    try:
        subprocess.Popen(
            [SPAWNER_PATH, TASKKILL_PATH, args, SYSTEM32],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(0.5)
    except Exception as e:
        logging.error(f"kill_process {process_name} failed: {e}")


def _configure_edge_preferences():
    """
    Modify Edge Preferences before launch to prevent tab restore.
    Sets exit_type = Normal so Edge thinks it closed cleanly,
    and restore_on_startup = 1 (New Tab Page) not session restore.
    This is more reliable than deleting session files.
    """
    import json
    prefs_path = os.path.join(EDGE_SESSION_DIR, "Preferences")
    try:
        if os.path.exists(prefs_path):
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        else:
            prefs = {}
        prefs.setdefault('profile', {})['exit_type']     = 'Normal'
        prefs.setdefault('profile', {})['exited_cleanly'] = True
        prefs.setdefault('session', {})['restore_on_startup'] = 1
        with open(prefs_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f)
    except Exception as e:
        logging.warning(f"Could not configure Edge preferences: {e}")


def _clear_edge_session():
    """
    Delete ALL Edge session data to prevent any tab restore on next launch.
    Covers individual session files, the Sessions snapshot folder, and Snapshots.
    Must be called AFTER all msedge.exe processes have fully terminated.
    """
    import shutil

    # Individual session files
    for name in ["Current Session", "Current Tabs", "Last Session", "Last Tabs"]:
        path = os.path.join(EDGE_SESSION_DIR, name)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # Sessions and Snapshots folders contain additional recovery data
    for folder in ["Sessions", "Snapshots"]:
        folder_path = os.path.join(EDGE_SESSION_DIR, folder)
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)
        except Exception:
            pass


def _find_edge_hwnd():
    """
    Find the main Edge browser window handle.
    Verifies the window belongs to msedge.exe so other Chromium-based apps
    like VS Code or Discord are never accidentally targeted.
    """
    import win32gui
    import win32process
    import psutil

    found = [None]

    def callback(hwnd, _):
        if found[0]:
            return
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.GetClassName(hwnd) != "Chrome_WidgetWin_1":
            return
        if not win32gui.GetWindowText(hwnd):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if "msedge" in psutil.Process(pid).name().lower():
                found[0] = hwnd
        except Exception:
            pass

    win32gui.EnumWindows(callback, None)
    return found[0]


def _close_edge():
    """
    Close the current Edge tab via Ctrl+W (Edge closes itself when last tab gone),
    then force kill any remaining Edge processes and clear session files.
    """
    try:
        import win32gui
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("WScript.Shell")

        hwnd = _find_edge_hwnd()
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, 9)        # SW_RESTORE if minimised
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            time.sleep(0.3)
            shell.SendKeys("^w")
            logging.info("Edge tab closed via Ctrl+W")
            time.sleep(2)

        del shell
        pythoncom.CoUninitialize()

    except Exception as e:
        logging.warning(f"Edge tab close failed: {e}")

    # Force kill Edge and ALL child processes (/T = terminate tree)
    kill_process("msedge.exe", tree=True)

    # Wait for all Edge processes to fully terminate before deleting session files.
    # Without this wait, Edge child processes may still be writing session data
    # when we delete, causing incomplete cleanup and tab restore on next launch.
    time.sleep(3)

    # Clear ALL session data so next launch starts with a blank new tab
    _clear_edge_session()


# 10 realistic Python code snippets for VS Code simulation
VSCODE_CODE_SNIPPETS = [
    "import os\n\ndef list_files(directory='.'):\n    for entry in os.scandir(directory):\n        print(entry.name, '[dir]' if entry.is_dir() else '[file]')\n\nif __name__ == '__main__':\n    list_files()\n",
    "import json\nimport datetime\n\ndef log_event(event_type, message):\n    entry = {'time': datetime.datetime.now().isoformat(), 'type': event_type, 'msg': message}\n    print(json.dumps(entry, indent=2))\n\nlog_event('INFO', 'System check completed')\n",
    "import socket\nimport platform\n\ndef system_info():\n    print('hostname:', socket.gethostname())\n    print('platform:', platform.system())\n    print('version:', platform.version())\n\nsystem_info()\n",
    "import hashlib\n\ndef hash_string(text):\n    return hashlib.sha256(text.encode()).hexdigest()\n\nsamples = ['admin', 'password123', 'server01']\nfor s in samples:\n    print(s, '->', hash_string(s)[:16])\n",
    "import re\n\ndef parse_log(line):\n    m = re.match(r'(\\d{4}-\\d{2}-\\d{2})\\s+(\\w+)\\s+(.+)', line)\n    return m.groups() if m else None\n\ntest = '2026-06-01 INFO Server started'\nprint(parse_log(test))\n",
    "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n\nprint(bubble_sort([64, 34, 25, 12, 22, 11, 90]))\n",
    "import subprocess\nimport sys\n\ndef run(cmd):\n    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)\n    print(r.stdout.strip())\n\nrun('whoami')\nrun('hostname')\n",
    "from pathlib import Path\nimport datetime\n\nreport = Path.home() / 'Documents' / f'report_{datetime.date.today()}.txt'\nlines = ['=== Daily Report ===', f'Date: {datetime.date.today()}', 'Status: Operational']\nreport.write_text('\\n'.join(lines))\nprint('Saved:', report)\n",
    "import time\nimport random\n\nfor i in range(1, 6):\n    time.sleep(random.uniform(0.05, 0.2))\n    print(f'Task {i}/5 complete')\nprint('Done.')\n",
    "import os\nimport sys\n\ninfo = {'python': sys.version.split()[0], 'cwd': os.getcwd(), 'user': os.environ.get('USERNAME', 'unknown')}\nfor k, v in info.items():\n    print(f'{k}: {v}')\n",
]


def open_vscode_with_code(paths: dict):
    """
    Open VS Code with a random Python code snippet, then run the code.
    Flow: create file → open VS Code → wait (reviewing) → run code → close.
    """
    vscode_path = paths.get("apps", {}).get("vscode", "")
    if not vscode_path:
        logging.warning("VS Code path not configured in paths.yaml")
        return

    vscode_path = os.path.expandvars(vscode_path)
    if not os.path.exists(vscode_path):
        logging.warning(f"VS Code not found at: {vscode_path}")
        return

    snippet  = random.choice(VSCODE_CODE_SNIPPETS)
    docs_dir = os.path.expandvars(r"%USERPROFILE%\Documents")
    tmp_path = os.path.join(docs_dir, f"lisa_snippet_{random.randint(1000,9999)}.py")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(snippet)

        # Open VS Code with the file via spawn.exe (parent = explorer.exe)
        working_dir = os.path.dirname(vscode_path)
        subprocess.Popen(
            [SPAWNER_PATH, vscode_path, tmp_path, working_dir],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"VS Code opened: {os.path.basename(tmp_path)}")

        # Simulate reviewing / editing the code
        review_time = random.randint(30, 60)
        logging.info(f"Reviewing code for {review_time}s")
        time.sleep(review_time)

        # Run the code in a visible CMD window via spawn.exe
        # /c runs the command then closes; timeout 5 keeps the window open briefly
        cmd_args = f'/c python "{tmp_path}" & timeout /t 5 /nobreak'
        subprocess.Popen(
            [SPAWNER_PATH, r"C:\Windows\System32\cmd.exe", cmd_args,
             r"C:\Windows\System32"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"Running code: python {os.path.basename(tmp_path)}")

        # Wait for code execution + CMD to close
        time.sleep(15)

        # Close VS Code
        kill_process("Code.exe")
        logging.info("VS Code closed")

    except Exception as e:
        logging.error(f"VS Code action failed: {e}")
        kill_process("Code.exe")
    # Snippet file is kept — cleanup.py will delete it after 4 days


def open_app_via_shell(path: str):
    """Launch any application with explorer.exe as parent via spawn.exe.
    Closes after a realistic delay of 60-120 seconds."""
    try:
        working_dir = os.path.dirname(path) or os.getcwd()
        subprocess.Popen(
            [SPAWNER_PATH, path, "", working_dir],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"Launched via spawn: {path}")
        wait = random.randint(60, 120)
        logging.info(f"App open for {wait}s")
        time.sleep(wait)
        app_name = os.path.basename(path)
        kill_process(app_name)
        logging.info(f"App closed: {app_name}")
    except Exception as e:
        logging.error(f"Spawn error for {path}: {e}")


def open_browser(url: str):
    """
    Open Edge, visit the URL, browse for a realistic time, then close the tab.
    Edge closes itself when the last tab is gone.
    Each call is a complete open → visit → close cycle — no tab accumulation.
    """
    try:
        # Configure preferences BEFORE launch to prevent session restore popup
        _configure_edge_preferences()

        subprocess.Popen(
            [SPAWNER_PATH, EDGE_PATH, url, os.path.dirname(EDGE_PATH)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"Edge opened URL via spawn: {url}")

        # Simulate realistic browsing time
        browse_time = random.randint(20, 45)
        logging.info(f"Browsing for {browse_time}s")
        time.sleep(browse_time)

        _close_edge()
        logging.info(f"Edge closed after visiting: {url}")

    except Exception as e:
        logging.error(f"Browser open error: {e}")


def open_pdf_via_spawn(pdf_path: str):
    """Open PDF in Acrobat with explorer.exe as parent via spawn.exe."""
    try:
        subprocess.Popen(
            [SPAWNER_PATH, ACROBAT_PATH, pdf_path, os.path.dirname(ACROBAT_PATH)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"Acrobat opened PDF via spawn: {os.path.basename(pdf_path)}")
    except Exception as e:
        logging.error(f"Acrobat open error: {e}")


def close_app_by_name(process_name: str):
    try:
        kill_process(process_name)
        logging.info(f"Closed process: {process_name}")
    except Exception as e:
        logging.error(f"Failed to close {process_name}: {e}")