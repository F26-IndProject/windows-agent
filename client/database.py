"""
client/database.py — Direct PostgreSQL connection for Windows agent
====================================================================
Instead of going through the backend API (which always saves everything
as activity_type="heartbeat"), we connect directly to PostgreSQL —
exactly the same way the Linux agent does.

This means activities appear in the dashboard with their real names:
word_document, open_browser, outlook_read, run_powershell, etc.

REQUIRES: pip install psycopg2-binary
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2


# ─── CONFIGURATION ────────────────────────────────────────────────────────────
# Must match the database password in docker-compose.yml on the server VM
DB_CONFIG = {
    "host":     "192.168.100.10",
    "port":     5432,
    "database": "lisa_dev",
    "user":     "lisa",
    "password": "lisa_password_2026"
}
# ────────────────────────────────────────────────────────────────────────────────


class DatabaseManager:
    """Handles all direct PostgreSQL operations for the Windows agent."""

    def __init__(self):
        self.connection = None

    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            logging.info("Connected to PostgreSQL database directly")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            logging.info("Disconnected from database")

    def _execute(self, query: str, params: tuple = None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    columns = [d[0] for d in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.connection.commit()
                    return []
        except Exception as e:
            logging.error(f"Query failed: {e}")
            if self.connection:
                self.connection.rollback()
            return []

    def ensure_agent_exists(self, agent_id: str, username: str, role: str) -> Optional[int]:
        """
        Make sure this agent exists in the agents table.
        Returns the internal integer ID (not the agent_id string).
        """
        # Check if already exists
        results = self._execute(
            "SELECT id FROM agents WHERE agent_id = %s",
            (agent_id,)
        )
        if results:
            return results[0]['id']

        # Create new agent record
        logging.info(f"Creating agent record in database: {agent_id}")
        self._execute(
            """
            INSERT INTO agents (agent_id, name, status, os_type, config, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                agent_id,
                username,
                "active",
                "Windows",
                json.dumps({"role": role}),
                datetime.utcnow()
            )
        )
        results = self._execute(
            "SELECT id FROM agents WHERE agent_id = %s",
            (agent_id,)
        )
        return results[0]['id'] if results else None

    def update_agent_status(self, agent_id: str, last_activity: str):
        """Update last_seen and last_activity for this agent."""
        self._execute(
            """
            UPDATE agents
            SET status = 'active',
                last_seen = %s,
                last_activity = %s,
                updated_at = %s
            WHERE agent_id = %s
            """,
            (datetime.utcnow(), last_activity, datetime.utcnow(), agent_id)
        )

    def log_activity(self, agent_id: str, activity_type: str, activity_data: Dict[str, Any]):
        """
        Insert a row into agent_activities.
        This is what appears in the Recent activity list on the dashboard.
        activity_type can be anything: word_document, open_browser, outlook_read, etc.
        """
        # Get the internal integer ID
        results = self._execute(
            "SELECT id FROM agents WHERE agent_id = %s",
            (agent_id,)
        )
        if not results:
            logging.error(f"Agent not found in DB: {agent_id}")
            return

        internal_id = results[0]['id']

        self._execute(
            """
            INSERT INTO agent_activities (agent_id, activity_type, activity_data, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (
                internal_id,
                activity_type,
                json.dumps(activity_data),
                datetime.utcnow()
            )
        )
        logging.info(f"Activity logged to DB: {activity_type}")
