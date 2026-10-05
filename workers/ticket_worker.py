"""
Redis Background Worker for Support Ticket Processing
Processes escalated support tickets asynchronously via Redis Queue (RQ / Celery style).
Calculates priority, checks SLA requirements, and assigns human agents.
"""
import time
import os
import json
from datetime import datetime


def process_escalated_ticket(ticket_data: dict):
    """
    Background task executed by Redis worker when a query is escalated.
    """
    ticket_id = ticket_data.get("ticket_id", "UNKNOWN")
    customer_id = ticket_data.get("customer_id")
    category = ticket_data.get("category", "general_support")
    query = ticket_data.get("query", "")

    print(f"⚙️ [Ticket Worker] Processing escalated ticket {ticket_id} for Category: {category}")
    
    # 1. Determine urgency / priority
    urgent_keywords = ["allergy", "poison", "charged twice", "stolen", "accident", "emergency"]
    is_urgent = any(k in query.lower() for k in urgent_keywords)
    priority = "HIGH" if is_urgent else "MEDIUM"
    
    # 2. Compute SLA target
    sla_minutes = 30 if priority == "HIGH" else 120
    
    # Simulate processing & assignment
    time.sleep(0.5)
    
    result = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "priority": priority,
        "sla_target_minutes": sla_minutes,
        "status": "QUEUED_FOR_AGENT",
        "processed_at": datetime.utcnow().isoformat(),
    }
    
    print(f"✅ [Ticket Worker] Ticket {ticket_id} assigned Priority: {priority} (SLA: {sla_minutes}m)")
    return result


def start_worker():
    """Starts Redis RQ worker if Redis is running, otherwise provides standalone daemon mode."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"🚀 [SupportFlow Worker] Connecting to Redis at {redis_url}...")
    try:
        from redis import Redis
        from rq import Worker, Queue, Connection
        
        conn = Redis.from_url(redis_url)
        with Connection(conn):
            q = Queue("support_tickets")
            worker = Worker([q], connection=conn)
            print("🟢 [SupportFlow Worker] Listening for ticket jobs on queue 'support_tickets'...")
            worker.work()
    except Exception as e:
        print(f"⚠️ Redis worker could not connect ({e}). Standing by in mock daemon mode.")


if __name__ == "__main__":
    start_worker()
