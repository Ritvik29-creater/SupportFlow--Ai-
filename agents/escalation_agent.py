"""
SupportFlow AI — Zomato-grade Escalation Agent v2
Creates human support tickets with full context, sentiment-aware priority.
Generates empathetic, personalized escalation messages.
Human-in-the-loop: saves ticket to DB for human agent review.
"""
import uuid
from datetime import datetime
from config import LLM
from database.hitl_store import save_hitl_ticket


def escalation_agent(state: dict) -> dict:
    """
    Handles escalation to human support with HITL (Human-in-the-Loop).
    Creates a support ticket, saves it for human agent review, and generates
    an empathetic escalation message for the customer.
    """
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")

    intent = state.get("intent", "general_support")
    intent_display = intent.replace("_", " ").title()
    user_query = state.get("user_query", "")
    session_id = state.get("session_id", "unknown")
    sentiment_data = state.get("sentiment_data", {})
    agent_metadata = state.get("agent_metadata", {})
    conversation_history = state.get("conversation_history", [])

    severity = agent_metadata.get("complaint_severity", "standard")
    sentiment = sentiment_data.get("sentiment", "neutral")
    urgency = sentiment_data.get("urgency", "low")

    # ── Priority determination ─────────────────────────────────────────────────
    if (severity == "critical" or urgency == "high" or
            any(w in user_query.lower() for w in [
                "food poisoning", "cockroach", "threaten", "assault",
                "medical", "hospital", "emergency", "legal", "police"
            ])):
        priority = "🔴 CRITICAL"
        response_time = "15-30 minutes"
        priority_level = "critical"
    elif intent in ["refund", "payment", "delivery_partner"] or sentiment == "very_upset":
        priority = "🟠 HIGH"
        response_time = "1-2 hours"
        priority_level = "high"
    elif intent in ["restaurant", "order_tracking"]:
        priority = "🟡 MEDIUM"
        response_time = "2-4 hours"
        priority_level = "medium"
    else:
        priority = "🟢 STANDARD"
        response_time = "4-8 hours"
        priority_level = "standard"

    # ── Save to HITL store (for human agents to review) ───────────────────────
    try:
        save_hitl_ticket({
            "ticket_id": ticket_id,
            "session_id": session_id,
            "intent": intent,
            "priority": priority_level,
            "sentiment": sentiment,
            "urgency": urgency,
            "user_query": user_query,
            "conversation_history": conversation_history,
            "agent_metadata": agent_metadata,
            "timestamp": timestamp,
            "status": "open",
        })
    except Exception as e:
        print(f"[HITL Store Error] {e}")  # Don't fail escalation if DB save fails

    # ── Generate personalized escalation message ──────────────────────────────
    tone = sentiment_data.get("tone_modifier", "Be empathetic and reassuring.")
    
    escalation_prompt = f"""Write a warm, empathetic escalation message for a food delivery support chat.

TONE: {tone}
Customer's issue: {user_query}
Issue category: {intent_display}
Ticket ID: {ticket_id}
Priority: {priority}
Expected human response time: {response_time}

The message MUST:
1. Acknowledge their SPECIFIC situation (not generic — mention what they described)
2. Apologize genuinely for not being able to fully resolve this automatically
3. Reassure them a specialized human expert will personally handle it
4. Show the ticket ID clearly (format: **Ticket: {ticket_id}**)
5. State the exact response time clearly (format: **Response within: {response_time}**)
6. Give them 1-2 practical tips while they wait (keep photo, note order details, etc.)
7. End warmly — tell them they can track the ticket in Help & Support → My Tickets
8. For CRITICAL priority: add extra urgency and reassurance

Keep it under 180 words. Format key details with **bold**.
"""

    try:
        personalized_message = LLM.invoke(escalation_prompt).content.strip()
    except Exception:
        # Fallback message if LLM fails
        personalized_message = (
            f"I sincerely apologize for the inconvenience — your concern deserves personal attention from our team.\n\n"
            f"**Ticket ID:** `{ticket_id}`\n"
            f"**Category:** {intent_display}\n"
            f"**Priority:** {priority}\n"
            f"**Created:** {timestamp}\n\n"
            f"A human support specialist will review your case and respond within **{response_time}** "
            f"via SMS + in-app notification.\n\n"
            f"**While you wait:** Keep any photos or screenshots related to your issue — "
            f"our agent may request them for faster resolution.\n\n"
            f"**Track your ticket:** Help & Support → My Tickets → `{ticket_id}`"
        )

    # Ensure ticket ID is always visible in the message
    if ticket_id not in personalized_message:
        personalized_message += (
            f"\n\n---\n"
            f"🎫 **Ticket:** `{ticket_id}` | "
            f"⏱️ **Response within:** {response_time} | "
            f"📂 **Category:** {intent_display}"
        )

    return {
        "answer": personalized_message,
        "ticket_id": ticket_id,
        "action": "escalate",
        "agent_metadata": {
            **(agent_metadata or {}),
            "priority_level": priority_level,
            "response_time": response_time,
        },
    }