import logging
import subprocess
import os
import sys
import time
import random

from actions.apps import kill_process

def get_spawner_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        base_dir = os.path.dirname(exe_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, "spawn.exe")

SPAWNER_PATH = get_spawner_path()
SYSTEM32 = r"C:\Windows\System32"
CMD_PATH = r"C:\Windows\System32\cmd.exe"
POWERSHELL_PATH = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

def run_cmd(command: str, visible: bool = True):
    if not visible:
        try:
            result = subprocess.run(
                ["cmd.exe", "/C", command],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logging.info(f"CMD (hidden) '{command}' → {result.stdout[:200]}")
        except Exception as e:
            logging.error(f"Hidden CMD failed: {e}")
        return

    try:
        subprocess.Popen(
            [SPAWNER_PATH, CMD_PATH, f'/K "{command}"', SYSTEM32],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"CMD window started: {command}")

        wait = random.randint(15, 25)
        logging.info(f"CMD window open for {wait}s")
        time.sleep(wait)

        kill_process("cmd.exe")
        logging.info("CMD window closed")

    except Exception as e:
        logging.error(f"Visible CMD failed: {e}")


def run_powershell(command: str, visible: bool = True):
    if not visible:
        try:
            result = subprocess.run(
                ["powershell.exe", "-NonInteractive", "-Command", command],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logging.info(f"PowerShell (hidden) '{command}' → {result.stdout[:200]}")
        except Exception as e:
            logging.error(f"Hidden PowerShell failed: {e}")
        return

    try:
        safe_cmd = command.replace('"', '\\"')
        subprocess.Popen(
            [SPAWNER_PATH, POWERSHELL_PATH, f'-NoExit -Command "{safe_cmd}"', SYSTEM32],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        logging.info(f"PowerShell window started: {command}")

        wait = random.randint(15, 25)
        logging.info(f"PowerShell window open for {wait}s")
        time.sleep(wait)

        kill_process("powershell.exe")
        logging.info("PowerShell window closed")

    except Exception as e:
        logging.error(f"Visible PowerShell failed: {e}")