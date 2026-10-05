"""
Notification Background Worker
Handles async email/push notifications for order updates, refund status changes, and support resolutions.
"""
import time
from datetime import datetime


def send_customer_notification(payload: dict):
    """
    Sends customer notification asynchronously.
    """
    customer_id = payload.get("customer_id")
    event_type = payload.get("event_type", "ORDER_UPDATE")
    message = payload.get("message", "")
    
    print(f"📩 [Notification Worker] Dispatching {event_type} to Customer {customer_id}: {message}")
    time.sleep(0.2)
    return {"status": "SENT", "timestamp": datetime.utcnow().isoformat()}
