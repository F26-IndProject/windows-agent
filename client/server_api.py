"""
client/server_api.py — Communication with the LISA backend server
==================================================================
After reading the actual backend code, here is how activity logging works:

- There is NO /api/agent_activities endpoint
- Activities are logged through the heartbeat endpoint itself
- The heartbeat payload includes a "current_activity" field
- The backend reads that field and saves it to agent.last_activity
- It also saves the full heartbeat as an AgentActivity record

So instead of two separate functions, we send one enriched heartbeat
that includes what the agent is currently doing.
"""

import logging
import platform
from datetime import datetime

import requests


def send_heartbeat_to_server(url: str, agent_id: str, username: str, role: str,
                              current_activity: str = None):
    """
    Send a heartbeat to the LISA backend.
    current_activity — what the agent just did (e.g. "word_document", "open_browser")
    The backend stores this in agent.last_activity and shows it in the dashboard.
    """
    payload = {
        "agent_id":   agent_id,
        "name":       username,
        "username":   username,
        "status":     "active",
        "os_type":    f"Windows-{platform.version()[:20]}",
        "role":       role,
        "timestamp":  datetime.utcnow().isoformat(),
        "system_info": {
            "platform":  platform.system(),
            "release":   platform.release(),
            "machine":   platform.machine(),
            "processor": platform.processor()[:50],
            "hostname":  platform.node(),
        },
        "last_activity": current_activity or f"Running as {role}"
    }

    if current_activity:
        payload["current_activity"] = {
            "application": current_activity,
            "timestamp":   datetime.utcnow().isoformat()
        }

    headers = {
        "Authorization": "Bearer sk-agent-heartbeat-key-2024",
        "Content-Type":  "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            logging.info(f"Heartbeat sent successfully — activity: {current_activity or 'idle'}")
        else:
            logging.warning(
                f"Heartbeat returned {response.status_code}: {response.text[:200]}"
            )
    except requests.ConnectionError:
        logging.error(f"Cannot reach server at {url}")
    except requests.Timeout:
        logging.error(f"Heartbeat timed out")
    except Exception as e:
        logging.error(f"Heartbeat failed: {e}")


def send_activity(agent_id: str, action: dict, result: dict, base_url: str):
    """
    Log an activity by sending an immediate heartbeat with the activity included.
    The backend has no separate activity endpoint — activities go through heartbeat.
    """
    action_type = action.get("action", "unknown")
    heartbeat_url = f"{base_url}/agents/heartbeat"

    payload = {
        "agent_id":  agent_id,
        "status":    "active",
        "os_type":   f"Windows-{platform.system()}",
        "timestamp": datetime.utcnow().isoformat(),
        "last_activity": action_type,
        "current_activity": {
            "application": action_type,
            "timestamp":   datetime.utcnow().isoformat()
        },
        "statistics": {
            "action":  action_type,
            "result":  result,
            "details": action
        }
    }

    headers = {
        "Authorization": "Bearer sk-agent-heartbeat-key-2024",
        "Content-Type":  "application/json"
    }

    try:
        response = requests.post(heartbeat_url, json=payload, headers=headers, timeout=5)
        if response.status_code in (200, 201):
            logging.info(f"Activity logged to server: {action_type}")
        else:
            logging.warning(f"Activity log returned {response.status_code}")
    except Exception as e:
        logging.warning(f"Activity log failed: {e}")
