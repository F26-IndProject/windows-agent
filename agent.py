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
import random
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
import yaml

from actions import apps, office, smb, rdp, registry, terminal
from client.server_api import send_heartbeat_to_server
from client.database import DatabaseManager
from utils.logger import setup_logger

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
SERVER_IP   = "192.168.100.10"
SERVER_PORT = 8000
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

logger = setup_logger()

LOCK_FILE = Path(f"{AGENT_ID}.lock")

# Shared database manager — initialised in main(), used everywhere
db = DatabaseManager()


def check_singleton():
    if LOCK_FILE.exists():
        logger.error(f"Agent {AGENT_ID} is already running. Exiting.")
        sys.exit(1)
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


def is_work_time(settings):
    now       = datetime.now()
    weekday   = now.isoweekday()
    cur_time  = now.time()
    work_days = settings.get("work_days", [1, 2, 3, 4, 5])
    start = datetime.strptime(settings.get("work_start", "09:00"), "%H:%M").time()
    end   = datetime.strptime(settings.get("work_end",   "18:00"), "%H:%M").time()
    return weekday in work_days and start <= cur_time <= end


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

        elif action_type == "open_app":
            app_name = action.get("app")
            path     = paths.get("apps", {}).get(app_name)
            if path:
                apps.open_app_via_shell(os.path.expandvars(path))
            else:
                logger.warning(f"No path configured for app: {app_name}")

        elif action_type == "word_document":
            office.create_word_document(
                filename=action.get("filename", "document.docx"),
                content=action.get("content", "Work notes.")
            )

        elif action_type == "excel_spreadsheet":
            office.create_excel_spreadsheet(
                filename=action.get("filename", "data.xlsx")
            )

        elif action_type == "outlook_email":
            office.send_outlook_email(
                to=action.get("to", "colleague@company.local"),
                subject=action.get("subject", "Update"),
                body=action.get("body", "Please see the latest update.")
            )

        elif action_type == "outlook_read":
            office.read_outlook_inbox()

        elif action_type == "run_powershell":
            terminal.run_powershell(action.get("command", "Get-Date"))

        elif action_type == "run_cmd":
            terminal.run_cmd(action.get("command", "whoami"))

        elif action_type == "smb_access":
            smb.access_share(
                server=action.get("server", SERVER_IP),
                share=action.get("share", "share"),
                action=action.get("smb_action", "list")
            )

        elif action_type == "rdp_connect":
            rdp.connect(
                target=action.get("target", SERVER_IP),
                username=action.get("rdp_user", username),
                password=action.get("rdp_pass", "")
            )

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
            terminal.run_powershell(
                f'New-ScheduledTask -Action (New-ScheduledTaskAction -Execute "{action.get("execute", "notepad.exe")}") '
                f'-Trigger (New-ScheduledTaskTrigger -Daily -At "{action.get("at", "09:00")}") | '
                f'Register-ScheduledTask -TaskName "{action.get("name", "LISATask")}" -Force'
            )

        elif action_type == "create_file":
            path    = os.path.expandvars(action.get("path", r"%USERPROFILE%\Documents\notes.txt"))
            content = action.get("content", f"Notes created at {datetime.now()}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"File created: {path}")

        elif action_type == "sleep":
            secs = action.get("seconds", 60)
            logger.info(f"Idle for {secs} seconds")
            time.sleep(secs)

        else:
            logger.warning(f"Unknown action type: {action_type}")

        # Log to database directly — this is what shows in the dashboard
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
            role = load_yaml(CONFIG_PATH).get("role", "user")
            send_heartbeat_to_server(
                url=HEARTBEAT_URL,
                agent_id=AGENT_ID,
                username=username,
                role=role
            )
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


def main():
    check_singleton()
    logger.info(f"LISA Windows Agent starting. Agent ID: {AGENT_ID}, User: {username}")

    # Connect to database directly
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

        # Register this agent in the database
        db.ensure_agent_exists(AGENT_ID, username, role_name)

        # Start heartbeat thread
        t = threading.Thread(target=heartbeat_loop, daemon=True)
        t.start()
        logger.info(f"Heartbeat thread started — sending to {HEARTBEAT_URL}")

        interval_min = settings.get("activity_interval_min", 120)
        interval_max = settings.get("activity_interval_max", 300)

        while True:
            if not is_work_time(settings):
                logger.info("Outside working hours — sleeping 5 minutes")
                time.sleep(300)
                continue

            activity = weighted_choice(activities)
            run_action(activity, paths, settings)

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
