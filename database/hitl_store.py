"""
SupportFlow AI — Human-in-the-Loop (HITL) Ticket Store
Persists escalated tickets to SQLite for human agent review.
Provides simple API for saving, retrieving, and updating HITL tickets.
"""
import json
import sqlite3
import os
from datetime import datetime
from config import BASE_DIR

HITL_DB_PATH = os.path.join(BASE_DIR, "data", "hitl_tickets.db")


def _get_conn():
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(HITL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_hitl_db():
    """Create the HITL tickets table if it doesn't exist."""
    os.makedirs(os.path.dirname(HITL_DB_PATH), exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hitl_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                session_id TEXT,
                intent TEXT,
                priority TEXT DEFAULT 'standard',
                sentiment TEXT DEFAULT 'neutral',
                urgency TEXT DEFAULT 'low',
                user_query TEXT,
                conversation_history TEXT,  -- JSON array
                agent_metadata TEXT,        -- JSON object
                status TEXT DEFAULT 'open', -- open | in_review | resolved | closed
                human_agent_id TEXT,
                human_response TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()


def save_hitl_ticket(ticket: dict) -> bool:
    """
    Save an escalation ticket to the HITL database.
    Returns True on success, False on failure.
    """
    try:
        initialize_hitl_db()
        now = datetime.utcnow().isoformat()
        with _get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO hitl_tickets
                (ticket_id, session_id, intent, priority, sentiment, urgency,
                 user_query, conversation_history, agent_metadata, status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.get("ticket_id"),
                ticket.get("session_id"),
                ticket.get("intent"),
                ticket.get("priority", "standard"),
                ticket.get("sentiment", "neutral"),
                ticket.get("urgency", "low"),
                ticket.get("user_query"),
                json.dumps(ticket.get("conversation_history", [])),
                json.dumps(ticket.get("agent_metadata", {})),
                ticket.get("status", "open"),
                ticket.get("timestamp", now),
                now,
            ))
            conn.commit()
        return True
    except Exception as e:
        print(f"[HITL Store] Failed to save ticket: {e}")
        return False


def get_ticket(ticket_id: str) -> dict | None:
    """Retrieve a ticket by ID."""
    try:
        initialize_hitl_db()
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM hitl_tickets WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result["conversation_history"] = json.loads(result.get("conversation_history") or "[]")
                result["agent_metadata"] = json.loads(result.get("agent_metadata") or "{}")
                return result
        return None
    except Exception as e:
        print(f"[HITL Store] Failed to get ticket: {e}")
        return None


def get_open_tickets(limit: int = 50) -> list:
    """Get all open tickets ordered by priority and creation time."""
    try:
        initialize_hitl_db()
        priority_order = "CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
        with _get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM hitl_tickets WHERE status = 'open' ORDER BY {priority_order}, created_at ASC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[HITL Store] Failed to get open tickets: {e}")
        return []


def update_ticket_status(ticket_id: str, status: str, human_response: str = None, agent_id: str = None) -> bool:
    """Update a ticket's status and optionally add human response."""
    try:
        initialize_hitl_db()
        now = datetime.utcnow().isoformat()
        with _get_conn() as conn:
            conn.execute(
                """UPDATE hitl_tickets 
                   SET status = ?, human_response = ?, human_agent_id = ?, updated_at = ?
                   WHERE ticket_id = ?""",
                (status, human_response, agent_id, now, ticket_id)
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[HITL Store] Failed to update ticket: {e}")
        return False


# Initialize on import
try:
    initialize_hitl_db()
except Exception:
    pass  # Non-fatal — HITL store is optional
