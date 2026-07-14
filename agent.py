"""
LISA Windows Agent — main entry point
======================================
Connects directly to PostgreSQL (like the Linux agent) so activities
appear in the dashboard with their real names, not just "heartbeat".
"""
import argparse
import getpass
import logging
import os
import subprocess
import random
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
import requests
import yaml
from dotenv import load_dotenv
from actions import apps, office, smb, rdp, registry, terminal, cleanup, tasks
from client.server_api import send_heartbeat_to_server
from client.database import DatabaseManager
from utils.logger import setup_logger
# ─── CONFIGURATION ────────────────────────────────────────────────────────────
load_dotenv()
SERVER_IP   = os.getenv("SERVER_IP")
SERVER_PORT = int(os.getenv("SERVER_PORT"))
HEARTBEAT_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/agents/heartbeat"
HEARTBEAT_INTERVAL_SECONDS = 300
# ────────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="LISA Windows Agent")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()
username = getpass.getuser()
mac_int  = uuid.getnode()
mac_str  = f"{mac_int:012x}"
AGENT_ID = f"agent_{username}_{mac_str}".lower()
LOG_FILE = Path("logs/agent.log")
LOG_FILE.parent.mkdir(exist_ok=True)
if args.debug:
    if LOG_FILE.exists():
        LOG_FILE.unlink()
        print("[*] Debug mode: cleared old log file")
    for lock_file in Path().glob("*.lock"):
        try:
            lock_file.unlink()
            print(f"[*] Debug mode: removed lock file {lock_file.name}")
        except Exception as e:
            print(f"[!] Could not remove lock file {lock_file.name}: {e}")
def _launch_log_writer():
    """Launch log_writer.exe via spawn.exe so parent process = explorer.exe."""
    try:
        # Do not launch if already running
        import psutil
        if any(p.name().lower() == "log_writer.exe" for p in psutil.process_iter(["name"])):
            return
        spawn  = Path("spawn.exe")
        writer = Path("log_writer.exe")
        if spawn.exists() and writer.exists():
            subprocess.Popen(
                [str(spawn), str(writer)],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1)  # allow time to start listening
    except Exception as e:
        print(f"[!] Could not launch log_writer: {e}")
_launch_log_writer()
logger = setup_logger()
LOCK_FILE = Path(f"{AGENT_ID}.lock")
# Shared database manager — initialised in main(), used everywhere
db = DatabaseManager()
# Shared mutable role state — updated by heartbeat thread, read by main loop
agent_role_state = {"role": None, "activities": [], "loaded_at": None}
role_lock = threading.Lock()
def check_singleton():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        logger.info("Removed stale lock file from previous session")
    LOCK_FILE.touch()
    logger.info(f"Lock file created: {LOCK_FILE}")
def cleanup_singleton():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        logger.info(f"Lock file removed: {LOCK_FILE}")
CONFIG_PATH = Path("config/settings.yaml")
PATHS_PATH  = Path("config/paths.yaml")
ROLES_DIR   = Path("roles")
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
def load_config():
    settings  = load_yaml(CONFIG_PATH)
    paths     = load_yaml(PATHS_PATH)
    role_name = settings["role"]
    role_file = ROLES_DIR / f"{role_name}.yaml"
    role      = load_yaml(role_file)
    logger.info(f"Loaded role: {role_name}")
    return settings, paths, role
def load_role_activities(role_name: str):
    role_file = ROLES_DIR / f"{role_name}.yaml"
    if role_file.exists():
        role_data = load_yaml(role_file)
        activities = role_data.get("activities", [])
        logger.info(f"Loaded role '{role_name}' from YAML ({len(activities)} actions)")
        return activities
    logger.info(f"No YAML for role '{role_name}' — checking database")
    activities = db.get_role_definition(role_name)
    if activities:
        return activities
    logger.warning(f"Role '{role_name}' not found in YAML or database — keeping current role")
    return None
def _check_break():
    """Check if agent is currently on an assigned break. Returns (on_break, reason)."""
    try:
        brk = db.get_agent_break(AGENT_ID)
        if brk:
            cur_time = datetime.now().time()
            start    = datetime.strptime(brk['break_start'], "%H:%M").time()
            end      = datetime.strptime(brk['break_end'],   "%H:%M").time()
            if start <= cur_time <= end:
                return True, f"break time: {brk['name']} ({brk['break_start']}–{brk['break_end']})"
    except Exception:
        pass
    return False, None
def is_work_time(settings):
    """
    Check if current time falls within working hours.
    Returns (bool, idle_reason) — idle_reason is None when active.
    Priority:
    1. Public holiday → idle
    2. Agent's assigned schedule in DB → use it
    3. Fall back to local schedule
    """
    # 1. Public holiday check
    try:
        if db.is_public_holiday():
            return False, "public holiday"
    except Exception:
        pass
    # 2. Agent-specific schedule from DB
    try:
        schedule = db.get_agent_schedule(AGENT_ID)
        if schedule:
            now      = datetime.now()
            weekday  = now.isoweekday()
            cur_time = now.time()
            start    = datetime.strptime(schedule['work_start'], "%H:%M").time()
            end      = datetime.strptime(schedule['work_end'],   "%H:%M").time()
            if start <= end:
                in_time = start <= cur_time <= end
            else:  # overnight shift e.g. 22:00–06:00
                in_time = cur_time >= start or cur_time <= end
            in_hours = weekday in schedule['work_days'] and in_time
            if in_hours:
                on_break, break_reason = _check_break()
                if on_break:
                    return False, break_reason
                return True, None
            return False, f"Assigned schedule: {schedule['name']} ({schedule['work_start']}–{schedule['work_end']})"
    except Exception:
        pass
    # 3. Fall back to local schedule
    now        = datetime.now()
    weekday    = now.isoweekday()
    cur_time   = now.time()
    work_days  = settings.get("work_days", [1, 2, 3, 4, 5])
    work_start = settings.get("work_start", "09:00")
    work_end   = settings.get("work_end",   "18:00")
    start = datetime.strptime(work_start, "%H:%M").time()
    end   = datetime.strptime(work_end,   "%H:%M").time()
    if start <= end:
        in_time = start <= cur_time <= end
    else:  # overnight shift
        in_time = cur_time >= start or cur_time <= end
    in_hours = weekday in work_days and in_time
    if in_hours:
        on_break, break_reason = _check_break()
        if on_break:
            return False, break_reason
        return True, None
    return False, f"local schedule ({work_start}–{work_end})"
def weighted_choice(activities):
    weights = [a.get("weight", 1) for a in activities]
    return random.choices(activities, weights=weights, k=1)[0]
def run_action(action, paths, settings):
    action_type = action.get("action")
    delay = action.get("delay", 0)
    if delay:
        logger.info(f"Waiting {delay}s before action: {action_type}")
        time.sleep(delay)
    logger.info(f"Running action: {action_type}")
    try:
        if action_type == "open_browser":
            urls = action.get("urls", ["https://google.com"])
            url  = random.choice(urls)
            apps.open_browser(url)
        elif action_type == "vscode":
            apps.open_vscode_with_code(paths)
        elif action_type == "open_app":
            apps_list = action.get("apps", None)
            app_name  = random.choice(apps_list) if apps_list else action.get("app")
            if app_name == "vscode":
                apps.open_vscode_with_code(paths)
            else:
                path = paths.get("apps", {}).get(app_name)
                if path:
                    apps.open_app_via_shell(os.path.expandvars(path))
                else:
                    logger.warning(f"No path configured for app: {app_name}")
        elif action_type == "word_document":
            filenames = action.get("filenames", None)
            if filenames:
                filename = random.choice(filenames)
            else:
                filename = action.get("filename", "document.docx")
            office.create_word_document(
                filename=filename,
                content=action.get("content", "")
            )
        elif action_type == "excel_spreadsheet":
            office.create_excel_spreadsheet(
                filename=action.get("filename", "data.xlsx")
            )
        elif action_type == "outlook_email":
            recipients = action.get("recipients", None)
            _t = threading.Thread(
                target=office.send_outlook_email,
                kwargs={
                    "to":         action.get("to", None) if not recipients else None,
                    "subject":    action.get("subject", None),
                    "body":       action.get("body", None),
                    "recipients": recipients,
                },
                daemon=True
            )
            _t.start()
            import pythoncom
            deadline = time.time() + 600
            while _t.is_alive() and time.time() < deadline:
                try:
                    pythoncom.PumpWaitingMessages()
                except Exception:
                    pass
                time.sleep(0.1)
            if _t.is_alive():
                logging.warning("Outlook email timed out after 600s — force closing Outlook")
                from actions.apps import kill_process; kill_process("OUTLOOK.EXE")
        elif action_type == "outlook_read":
            _t = threading.Thread(target=office.read_outlook_inbox, daemon=True)
            _t.start()
            import pythoncom
            deadline = time.time() + 600
            while _t.is_alive() and time.time() < deadline:
                try:
                    pythoncom.PumpWaitingMessages()
                except Exception:
                    pass
                time.sleep(0.1)
            if _t.is_alive():
                logging.warning("Outlook read timed out after 600s — force closing Outlook")
                from actions.apps import kill_process; kill_process("OUTLOOK.EXE")
        elif action_type == "run_powershell":
            commands = action.get("commands", None)
            if commands:
                cmd = random.choice(commands)
            else:
                cmd = action.get("command", "Get-Date")
            terminal.run_powershell(cmd)
        elif action_type == "run_cmd":
            commands = action.get("commands", None)
            if commands:
                cmd = random.choice(commands)
            else:
                cmd = action.get("command", "whoami")
            terminal.run_cmd(cmd)
        elif action_type == "smb_access":
            smb.access_share(
                server=action.get("server", SERVER_IP),
                share=action.get("share", "share"),
                action=action.get("smb_action", "browse")
            )
        elif action_type == "rdp_connect":
            rdp_connections = action.get("rdp_connections", [])
            if rdp_connections:
                entry    = random.choice(rdp_connections)
                target   = entry.get("target",   SERVER_IP)
                rdp_user = entry.get("username", os.getenv("RDP_USERNAME", username))
                rdp_pass = entry.get("password", os.getenv("RDP_PASSWORD", ""))
            else:
                targets  = action.get("targets", None)
                target   = random.choice(targets) if targets else action.get("target", SERVER_IP)
                rdp_user = action.get("username", os.getenv("RDP_USERNAME", username))
                rdp_pass = action.get("password", os.getenv("RDP_PASSWORD", ""))
            rdp.connect(target=target, username=rdp_user, password=rdp_pass)
        elif action_type == "registry_read":
            registry.read_key(
                key_path=action.get("key", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"),
                value_name=action.get("value", "ProductName")
            )
        elif action_type == "registry_write":
            registry.write_key(
                key_path=action.get("key", r"HKCU\Software\LISA"),
                value_name=action.get("value", "LastRun"),
                data=datetime.now().isoformat()
            )
        elif action_type == "create_scheduled_task":
            operations = action.get("operations", [])
            # Phase 1 — delete/restore: affect whether tasks get created
            deleted = db.get_deleted_tasks(AGENT_ID)
            for op_entry in operations:
                op   = op_entry.get("operation", "enable")
                name = op_entry.get("name", "")
                if op == "delete":
                    if name not in deleted:
                        tasks.delete_task(name)
                    db.mark_task_deleted(AGENT_ID, name)
                elif op == "restore":
                    db.restore_task(AGENT_ID, name)
                    logger.info(f"Scheduled task '{name}' restored — will be recreated")
            # Phase 2 — create tasks, skipping deleted ones
            task_list = action.get("tasks", [])
            if task_list:
                deleted = db.get_deleted_tasks(AGENT_ID)
                pending = []
                for task in task_list:
                    if task.get("name") in deleted:
                        logger.info(f"Scheduled task '{task.get('name')}' was deleted via manager — not recreating")
                    else:
                        pending.append(task)
                tasks.create_tasks(pending)
            else:
                tasks.create_task(action)
            # Phase 3 — enable/disable/run: require task to exist
            for op_entry in operations:
                op   = op_entry.get("operation", "enable")
                name = op_entry.get("name", "")
                if   op == "enable":  tasks.enable_task(name)
                elif op == "disable": tasks.disable_task(name)
                elif op == "run":     tasks.run_task(name)
        elif action_type == "create_file":
            path    = os.path.expandvars(action.get("path", r"%USERPROFILE%\Documents\notes.txt"))
            content = action.get("content", f"Notes created at {datetime.now()}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"File created: {path}")
        elif action_type == "sleep":
            min_secs = action.get("min_seconds", 30)
            max_secs = action.get("max_seconds", 120)
            secs = random.randint(min_secs, max_secs)
            logger.info(f"Idle for {secs} seconds (range: {min_secs}–{max_secs})")
            time.sleep(secs)
        else:
            logger.warning(f"Unknown action type: {action_type}")
        db.update_agent_status(AGENT_ID, action_type)
        db.log_activity(
            agent_id=AGENT_ID,
            activity_type=action_type,
            activity_data={
                "action":    action_type,
                "details":   action,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Action '{action_type}' failed: {e}")
        db.log_activity(
            agent_id=AGENT_ID,
            activity_type="error",
            activity_data={"action": action_type, "error": str(e)}
        )
def heartbeat_loop():
    while True:
        try:
            with role_lock:
                agent_role   = agent_role_state["role"]
                loaded_at    = agent_role_state["loaded_at"]
            send_heartbeat_to_server(
                url=HEARTBEAT_URL,
                agent_id=AGENT_ID,
                username=username,
                role=agent_role or "user"
            )
            db_role = db.get_agent_role(AGENT_ID)
            if db_role and db_role != agent_role:
                new_activities = load_role_activities(db_role)
                if new_activities:
                    with role_lock:
                        agent_role_state["role"]       = db_role
                        agent_role_state["activities"] = new_activities
                        agent_role_state["loaded_at"]  = datetime.utcnow()
                    logger.info(f"Role changed to: {db_role} — activities reloaded")
            elif db_role and loaded_at:
                updated_at = db.get_role_updated_at(db_role)
                if updated_at:
                    ua = updated_at.replace(tzinfo=None) if hasattr(updated_at, 'tzinfo') else updated_at
                    la = loaded_at.replace(tzinfo=None)  if hasattr(loaded_at, 'tzinfo')  else loaded_at
                    if ua > la:
                        new_activities = load_role_activities(db_role)
                        if new_activities:
                            with role_lock:
                                agent_role_state["activities"] = new_activities
                                agent_role_state["loaded_at"]  = datetime.utcnow()
                            logger.info(f"Custom role '{db_role}' was updated — activities reloaded")
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)
def _disable_quickedit():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)
        mode   = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value &= ~0x0040
        mode.value &= ~0x0010
        kernel32.SetConsoleMode(handle, mode)
    except Exception:
        pass
def main():
    _disable_quickedit()
    check_singleton()
    logger.info(f"LISA Windows Agent starting. Agent ID: {AGENT_ID}, User: {username}")
    if not db.connect():
        logger.error("Cannot connect to database. Exiting.")
        cleanup_singleton()
        sys.exit(1)
    try:
        settings, paths, role_data = load_config()
        activities = role_data.get("activities", [])
        role_name  = settings.get("role", "user")
        if not activities:
            logger.error("No activities defined in role file. Exiting.")
            return
        db.ensure_agent_exists(AGENT_ID, username, role_name)
        db_role = db.get_agent_role(AGENT_ID)
        if db_role and db_role != role_name:
            logger.info(f"DB role '{db_role}' overrides config role '{role_name}' — loading DB role")
            db_activities = load_role_activities(db_role)
            if db_activities:
                role_name  = db_role
                activities = db_activities
            else:
                logger.warning(f"Could not load DB role '{db_role}' — using config role '{role_name}'")
        with role_lock:
            agent_role_state["role"]       = role_name
            agent_role_state["activities"] = activities
            agent_role_state["loaded_at"]  = datetime.utcnow()
        t = threading.Thread(target=heartbeat_loop, daemon=True)
        t.start()
        logger.info(f"Heartbeat thread started — sending to {HEARTBEAT_URL}")
        c = threading.Thread(target=cleanup.cleanup_loop, daemon=True)
        c.start()
        logger.info("Cleanup thread started — removes files older than 4 days every 24h")
        # Default interval from settings.yaml — DB can override per agent
        default_interval_min = settings.get("activity_interval_min", 120)
        default_interval_max = settings.get("activity_interval_max", 300)
        was_idle    = False
        idle_reason = None
        while True:
            active, reason = is_work_time(settings)
            if not active:
                if not was_idle:
                    logger.info(f"Agent not working — {reason}")
                was_idle    = True
                idle_reason = reason
                time.sleep(300)
                continue
            if was_idle:
                logger.info("Agent resuming work")
                was_idle    = False
                idle_reason = None
            with role_lock:
                activities = list(agent_role_state["activities"])
            activity = weighted_choice(activities)
            run_action(activity, paths, settings)
            # Check DB for interval override — falls back to settings.yaml defaults
            db_interval  = db.get_agent_interval(AGENT_ID)
            interval_min = db_interval['interval_min'] if db_interval and db_interval.get('interval_min') else default_interval_min
            interval_max = db_interval['interval_max'] if db_interval and db_interval.get('interval_max') else default_interval_max
            wait = random.randint(interval_min, interval_max)
            logger.info(f"Waiting {wait}s before next activity")
            time.sleep(wait)
    except KeyboardInterrupt:
        logger.info("Stopped by user (Ctrl+C)")
    finally:
        db.disconnect()
        cleanup_singleton()
if __name__ == "__main__":
    main()