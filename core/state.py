"""
SupportFlow AI — LangGraph State Schema v2
Defines the full state passed between all agents in the pipeline.
"""
from typing import TypedDict, Literal, List, Optional, Dict, Any


class SupportState(TypedDict, total=False):
    # ── User / Session Context ─────────────────────────────────────────────────
    user_query: str
    session_id: Optional[str]
    customer_id: Optional[str]

    # ── Conversation Memory ────────────────────────────────────────────────────
    # List of {"role": "user"|"assistant", "content": "..."}
    conversation_history: List[Dict[str, str]]

    # ── Sentiment Analysis ────────────────────────────────────────────────────
    # Output from sentiment_agent — influences tone of all downstream agents
    # {"sentiment": "frustrated|very_upset|neutral|...", "urgency": "high|medium|low",
    #  "needs_extra_empathy": bool, "tone_modifier": "..."}
    sentiment_data: Optional[Dict[str, Any]]

    # ── Intent Classification ─────────────────────────────────────────────────
    intent: str  # order_tracking | payment | refund | restaurant | delivery_partner |
                 # account_app | coupon_offer | general_support | unknown
    intent_confidence: float

    # ── RAG / Knowledge Base ──────────────────────────────────────────────────
    retrieved_docs: List[str]
    force_escalate: bool     # Set by any agent that detects a case requiring human review

    # ── Generated Answer ──────────────────────────────────────────────────────
    answer: str
    answer_confidence: float

    # ── Routing Decision ──────────────────────────────────────────────────────
    action: Literal["answer", "clarify", "escalate"]

    # ── Human Escalation ──────────────────────────────────────────────────────
    ticket_id: Optional[str]  # Created when action == "escalate"

    # ── Agent Metadata ────────────────────────────────────────────────────────
    # Extra structured data from specialized agents
    # e.g., {"extracted_amount": "₹450", "issue_type": "cold_food", "complaint_severity": "moderate"}
    agent_metadata: Optional[Dict[str, Any]]