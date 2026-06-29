"""
actions/tasks.py — Windows Task Scheduler operations
======================================================
All tasks run under the current user with -RunLevel Limited.
Task actions run via spawn.exe so parent process is explorer.exe, not agent.exe.
Supported triggers: Daily, Weekly, AtLogon, AtStartup
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

_sysroot        = os.environ.get("SystemRoot", r"C:\Windows")
SYSTEM32        = os.path.join(_sysroot, "System32")
POWERSHELL_PATH = os.path.join(_sysroot, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")

DAYS_MAP = {
    "Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday",
    "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday",
    "Sunday": "Sunday"
}


def _get_spawn_path() -> Path:
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent.parent
    else:
        base = Path(__file__).parent.parent
    return base / "spawn_ps.exe"


SPAWN_PATH = _get_spawn_path()


def _run_ps(script: str):
    """
    Run a PowerShell script via spawn.exe so parent process is explorer.exe.
    Falls back to direct subprocess if spawn.exe is not found.
    """
    if SPAWN_PATH.exists():
        safe = script.replace('"', '\\"')
        proc = subprocess.Popen(
            [str(SPAWN_PATH), POWERSHELL_PATH,
             f'-NoProfile -NonInteractive -WindowStyle Hidden -Command "{safe}"',
             SYSTEM32],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        proc.wait()
    else:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-Command", script],
            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
        )


def _task_exists(name: str) -> bool:
    result_file = Path(os.environ.get("TEMP", os.environ.get("TMP", str(Path.cwd())))) / f"._chk_{name}.txt"
    script = (
        f"$r = (Get-ScheduledTask -TaskName '{name}' -ErrorAction SilentlyContinue) -ne $null;"
        f"$r | Out-File -FilePath '{result_file}' -Encoding ascii -NoNewline"
    )
    _run_ps(script)
    try:
        return result_file.read_text(encoding="utf-8", errors="ignore").strip().lower() == "true"
    except Exception:
        return False
    finally:
        try:
            result_file.unlink()
        except Exception:
            pass


def _build_action_cmd(execute: str, args: str) -> str:
    """
    Wrap the task action in powershell -NonInteractive -WindowStyle Hidden
    to suppress windows at execution time.
    If execute is already powershell.exe, just prepend the hidden flags.
    """
    if execute.lower() in ("powershell.exe", "powershell"):
        ps_args = f"-NoProfile -NonInteractive -WindowStyle Hidden {args}".strip()
        return f"New-ScheduledTaskAction -Execute '{execute}' -Argument '{ps_args}'"
    else:
        if args:
            ps_args = f"-NoProfile -NonInteractive -WindowStyle Hidden -Command \"& ''{execute}'' {args}\""
        else:
            ps_args = f"-NoProfile -NonInteractive -WindowStyle Hidden -Command \"& ''{execute}''\""
        return f"New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '{ps_args}'"


def create_task(task: dict):
    """
    Create a scheduled task from a task config dict.
    Fields: name, execute, args, trigger (Daily/Weekly/AtLogon/AtStartup), at, days
    Skips creation if task already exists.
    """
    name    = task.get("name",    "LISATask")
    execute = task.get("execute", "notepad.exe")
    args    = task.get("args",    "")
    trigger = task.get("trigger", "Daily")
    at      = task.get("at",      "09:00")
    days    = task.get("days",    ["Monday"])

    if _task_exists(name):
        logging.info(f"Scheduled task already exists: {name} — skipping")
        return

    if trigger == "Daily":
        trigger_cmd = f"New-ScheduledTaskTrigger -Daily -At '{at}'"
    elif trigger == "Weekly":
        days_str    = ",".join(days) if days else "Monday"
        trigger_cmd = f"New-ScheduledTaskTrigger -Weekly -DaysOfWeek {days_str} -At '{at}'"
    elif trigger == "AtLogon":
        trigger_cmd = "New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME"
    elif trigger == "AtStartup":
        trigger_cmd = "New-ScheduledTaskTrigger -AtStartup"
    else:
        trigger_cmd = f"New-ScheduledTaskTrigger -Daily -At '{at}'"

    action_cmd = _build_action_cmd(execute, args)

    script = (
        f"$Action    = {action_cmd};"
        f"$Trigger   = {trigger_cmd};"
        f"$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME "
        f"-LogonType Interactive -RunLevel Limited;"
        f"Register-ScheduledTask -TaskName '{name}' -Action $Action "
        f"-Trigger $Trigger -Principal $Principal -Force"
    )
    _run_ps(script)
    logging.info(f"Scheduled task created: {name} ({trigger})")


def create_tasks(task_list: list):
    """Process all tasks — create those that don't exist, skip those that do."""
    for task in task_list:
        create_task(task)


def delete_task(name: str):
    _run_ps(f"Unregister-ScheduledTask -TaskName '{name}' -Confirm:$false")
    logging.info(f"Scheduled task deleted: {name}")


def run_task(name: str):
    _run_ps(f"Start-ScheduledTask -TaskName '{name}'")
    logging.info(f"Scheduled task triggered: {name}")


def enable_task(name: str):
    _run_ps(f"Enable-ScheduledTask -TaskName '{name}'")
    logging.info(f"Scheduled task enabled: {name}")


def disable_task(name: str):
    _run_ps(f"Disable-ScheduledTask -TaskName '{name}'")
    logging.info(f"Scheduled task disabled: {name}")