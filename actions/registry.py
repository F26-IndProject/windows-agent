"""
actions/registry.py — Windows registry access (admin role only)
================================================================
Simulates an admin reading and writing registry keys.
Uses Python's built-in winreg module — no extra packages needed.

WHY REGISTRY ACCESS:
Vladislav specifically asked for registry access as an admin behaviour.
Real admins read registry keys when diagnosing issues (checking installed
software versions, service configurations, etc.) and occasionally write
keys when configuring software.

This generates registry audit log entries (if auditing is enabled)
which is realistic Windows admin activity.

All writes are to safe locations (HKCU\Software\LISA) so nothing
important is damaged. All reads are from standard OS keys.
"""

import logging
import winreg
from datetime import datetime


# Map short names to the actual registry hive constants
_HIVES = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKU":  winreg.HKEY_USERS,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,
}


def _parse_key_path(key_path: str):
    """
    Split 'HKLM\\SOFTWARE\\Microsoft' into (HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft').
    """
    parts = key_path.split("\\", 1)
    hive_name = parts[0].upper()
    sub_key   = parts[1] if len(parts) > 1 else ""
    hive = _HIVES.get(hive_name)
    if not hive:
        raise ValueError(f"Unknown registry hive: {hive_name}")
    return hive, sub_key


def read_key(key_path: str, value_name: str = ""):
    """
    Read a value from the Windows registry.

    key_path   — e.g. 'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'
    value_name — the name of the value to read (empty string = default value)
    """
    try:
        hive, sub_key = _parse_key_path(key_path)
        with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ) as key:
            value, reg_type = winreg.QueryValueEx(key, value_name)
            logging.info(
                f"Registry read: {key_path}\\{value_name} = {str(value)[:100]}"
            )
            return value
    except FileNotFoundError:
        logging.warning(f"Registry key not found: {key_path}\\{value_name}")
        return None
    except PermissionError:
        logging.warning(f"Permission denied reading registry: {key_path}")
        return None
    except Exception as e:
        logging.error(f"Registry read failed: {key_path}\\{value_name} — {e}")
        return None


def write_key(key_path: str, value_name: str, data: str):
    """
    Write a string value to the Windows registry.
    Only writes to HKCU (current user) to avoid needing admin rights.
    """
    try:
        hive, sub_key = _parse_key_path(key_path)

        # Safety check — only allow writing to HKCU in this simulation
        if hive != winreg.HKEY_CURRENT_USER:
            logging.warning(
                "Registry write blocked: only HKCU writes are allowed in simulation"
            )
            return

        # KEY_WRITE | KEY_READ opens or creates the key
        with winreg.CreateKeyEx(hive, sub_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, str(data))
            logging.info(
                f"Registry write: {key_path}\\{value_name} = {str(data)[:100]}"
            )
    except PermissionError:
        logging.warning(f"Permission denied writing registry: {key_path}")
    except Exception as e:
        logging.error(f"Registry write failed: {key_path}\\{value_name} — {e}")


def enumerate_subkeys(key_path: str):
    """
    List subkeys of a registry key.
    Simulates an admin browsing the registry (like opening regedit).
    """
    try:
        hive, sub_key = _parse_key_path(key_path)
        with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ) as key:
            index = 0
            subkeys = []
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                    subkeys.append(subkey_name)
                    index += 1
                except OSError:
                    break
            logging.info(
                f"Registry enumerated {len(subkeys)} subkeys under {key_path}"
            )
            return subkeys
    except Exception as e:
        logging.error(f"Registry enumeration failed: {key_path} — {e}")
        return []
