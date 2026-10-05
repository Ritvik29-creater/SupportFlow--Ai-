"""
Chat Router — LangGraph AI customer support endpoint (no auth required)
Processes queries through the multi-agent LangGraph pipeline.
Human-in-the-loop escalation is automatically triggered for low-confidence answers.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import uuid

from api.schemas.schemas import ChatMessage, ChatResponse, HITLTicketOut, HITLUpdateRequest, FeedbackRequest
from agents.injection_guard import is_prompt_injection, sanitize_context
from core.graph import build_graph
from database.hitl_store import get_ticket, get_open_tickets, update_ticket_status

router = APIRouter(prefix="/api/chat", tags=["AI Support Chat"])

# Build LangGraph pipeline once at startup (singleton)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# In-memory conversation store (keyed by session_id)
_sessions: dict = {}
# In-memory feedback store
_feedback: dict = {}


def get_session_history(session_id: str) -> list:
    return _sessions.get(session_id, [])


def save_session_history(session_id: str, history: list):
    # Keep last 20 turns to prevent unbounded memory growth
    _sessions[session_id] = history[-20:]


@router.post("/", response_model=ChatResponse)
def chat(message: ChatMessage):
    """
    Main AI chat endpoint — no authentication required.
    Runs the customer query through the full LangGraph multi-agent pipeline:
      1. Sentiment Agent (detect emotion, calibrate tone)
      2. Injection Guard (security)
      3. Intent Agent (classify: refund / order / payment / restaurant / etc.)
      4. Specialist Agent (domain-specific answer using RAG docs)
      5. Confidence Agent (score + decide: answer | clarify | escalate)
      6. If escalate → Human-in-the-loop ticket created and saved to DB
    """
    query = message.content.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Security check: block prompt injection attempts
    if is_prompt_injection(query):
        return ChatResponse(
            answer=(
                "I'm unable to process that request. "
                "Please describe your food delivery issue in plain English — "
                "I'm here to help with orders, refunds, payments, and more."
            ),
            action="escalate",
            intent="unknown",
            confidence=0.0,
            session_id=message.session_id or str(uuid.uuid4()),
        )

    # Sanitize user input
    query = sanitize_context(query)

    # Session management (maintains conversation memory across turns)
    session_id = message.session_id or str(uuid.uuid4())
    conversation_history = get_session_history(session_id)

    # Build initial LangGraph state
    state = {
        "user_query": query,
        "session_id": session_id,
        "customer_id": "anonymous",
        "conversation_history": conversation_history,
        "force_escalate": False,
        "retrieved_docs": [],
        "agent_metadata": {},
        "sentiment_data": {},
    }

    # Run the LangGraph multi-agent pipeline
    try:
        graph = get_graph()
        result = graph.invoke(state)
    except Exception as e:
        print(f"[LangGraph Error] {type(e).__name__}: {e}")
        return ChatResponse(
            answer=(
                "I encountered a technical issue processing your request. "
                "A support ticket has been created and a human agent will "
                "follow up with you shortly. We apologize for the inconvenience."
            ),
            action="escalate",
            intent="unknown",
            confidence=0.0,
            session_id=session_id,
        )

    # Update conversation memory for multi-turn support
    conversation_history.append({"role": "user", "content": query})
    conversation_history.append({
        "role": "assistant",
        "content": result.get("answer", "")
    })
    save_session_history(session_id, conversation_history)

    # Extract sentiment info for response
    sentiment_data = result.get("sentiment_data") or {}
    agent_metadata = result.get("agent_metadata") or {}

    return ChatResponse(
        answer=result.get("answer", "I'm sorry, I couldn't process your request."),
        action=result.get("action", "escalate"),
        intent=result.get("intent", "unknown"),
        confidence=result.get("answer_confidence"),
        ticket_id=result.get("ticket_id"),
        session_id=session_id,
        sentiment=sentiment_data.get("sentiment"),
        sentiment_urgency=sentiment_data.get("urgency"),
        agent_used=agent_metadata.get("specialized_agent"),
    )


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear conversation history for a given session."""
    if session_id in _sessions:
        del _sessions[session_id]
    return {"message": "Session cleared"}


@router.get("/health")
def chat_health():
    """Quick health check for the AI pipeline."""
    return {
        "status": "ok",
        "pipeline": "LangGraph multi-agent v2",
        "agents": [
            "sentiment", "intent", "order", "payment", "refund",
            "restaurant", "delivery_partner", "account_app", "coupon_offer",
            "confidence", "clarification", "escalation"
        ]
    }


# ── HITL (Human-in-the-Loop) Endpoints ────────────────────────────────────────

@router.get("/hitl/tickets")
def get_hitl_tickets(limit: int = 50):
    """Get all open escalation tickets ordered by priority (for human agents)."""
    tickets = get_open_tickets(limit=limit)
    return {"tickets": tickets, "count": len(tickets)}


@router.get("/hitl/tickets/{ticket_id}")
def get_hitl_ticket(ticket_id: str):
    """Get details of a specific ticket including full conversation history."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.patch("/hitl/tickets/{ticket_id}")
def update_hitl_ticket(ticket_id: str, update: HITLUpdateRequest):
    """Human agent updates ticket status with optional response."""
    success = update_ticket_status(
        ticket_id=ticket_id,
        status=update.status,
        human_response=update.human_response,
        agent_id=update.agent_id,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update ticket")
    return {"message": f"Ticket {ticket_id} updated to {update.status}"}


# ── Customer Feedback Endpoint ─────────────────────────────────────────────────

@router.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Customer submits satisfaction rating after their issue is resolved."""
    _feedback[feedback.session_id] = {
        "session_id": feedback.session_id,
        "rating": feedback.rating,
        "helpful": feedback.helpful,
        "comment": feedback.comment,
    }
    
    # Positive feedback message
    if feedback.rating >= 4:
        message = "Thank you! We're glad we could help. 😊"
    elif feedback.rating >= 3:
        message = "Thank you for your feedback! We'll use it to improve."
    else:
        message = "We're sorry we didn't meet your expectations. Your feedback has been noted and we'll do better."
    
    return {"message": message, "recorded": True}
