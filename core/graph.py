"""
LangGraph Orchestrator v2
Builds the full multi-agent graph for SupportFlow AI.

Flow:
  sentiment → intent → specialized_agent → confidence → [answer | clarify | escalate]

Specialized agents:
  order_agent | payment_agent | refund_agent | restaurant_agent | rag_agent |
  delivery_partner_agent | account_app_agent | coupon_offer_agent
"""
from langgraph.graph import StateGraph, END

from core.state import SupportState
from agents.sentiment_agent import sentiment_agent
from agents.intent_agent import intent_agent
from agents.rag_agent import rag_agent
from agents.order_agent import order_agent
from agents.payment_agent import payment_agent
from agents.refund_agent import refund_agent
from agents.restaurant_agent import restaurant_agent
from agents.delivery_partner_agent import delivery_partner_agent
from agents.account_app_agent import account_app_agent
from agents.coupon_offer_agent import coupon_offer_agent
from agents.visual_verification_agent import visual_verification_agent
from agents.confidence_agent import confidence_agent
from agents.clarification_agent import clarification_agent
from agents.escalation_agent import escalation_agent


def route_by_intent(state: SupportState) -> str:
    """
    Route to a specialized agent based on detected intent.
    If image evidence is provided, route directly to visual_verification_agent.
    Falls back to rag_agent for general_support or unknown.
    """
    # Multimodal photo priority
    if state.get("image_base64"):
        return "visual_verification_agent"

    intent = state.get("intent", "unknown")
    routing_map = {
        "order_tracking":    "order_agent",
        "payment":           "payment_agent",
        "refund":            "refund_agent",
        "restaurant":        "restaurant_agent",
        "delivery_partner":  "delivery_partner_agent",
        "account_app":       "account_app_agent",
        "coupon_offer":      "coupon_offer_agent",
        "general_support":   "rag_agent",
        "unknown":           "rag_agent",
    }
    return routing_map.get(intent, "rag_agent")


def route_by_confidence(state: SupportState) -> str:
    """Route based on confidence agent's decision."""
    return state.get("action", "escalate")


def build_graph():
    graph = StateGraph(SupportState)

    # ─── Register all nodes ───────────────────────────────────────────────────

    # Pre-processing nodes
    graph.add_node("sentiment", sentiment_agent)
    graph.add_node("intent", intent_agent)

    # Specialized domain agents
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("order_agent", order_agent)
    graph.add_node("payment_agent", payment_agent)
    graph.add_node("refund_agent", refund_agent)
    graph.add_node("restaurant_agent", restaurant_agent)
    graph.add_node("delivery_partner_agent", delivery_partner_agent)
    graph.add_node("account_app_agent", account_app_agent)
    graph.add_node("coupon_offer_agent", coupon_offer_agent)
    graph.add_node("visual_verification_agent", visual_verification_agent)

    # Post-processing nodes
    graph.add_node("confidence", confidence_agent)
    graph.add_node("clarify", clarification_agent)
    graph.add_node("escalate", escalation_agent)

    # ─── Entry point ──────────────────────────────────────────────────────────
    graph.set_entry_point("sentiment")

    # ─── Sentiment → Intent ───────────────────────────────────────────────────
    graph.add_edge("sentiment", "intent")

    # ─── Intent → specialized agent (conditional routing) ────────────────────
    graph.add_conditional_edges(
        "intent",
        route_by_intent,
        {
            "order_agent":               "order_agent",
            "payment_agent":             "payment_agent",
            "refund_agent":              "refund_agent",
            "restaurant_agent":          "restaurant_agent",
            "delivery_partner_agent":    "delivery_partner_agent",
            "account_app_agent":         "account_app_agent",
            "coupon_offer_agent":        "coupon_offer_agent",
            "visual_verification_agent": "visual_verification_agent",
            "rag_agent":                 "rag_agent",
        },
    )

    # ─── All specialized agents → confidence check ────────────────────────────
    for agent in [
        "rag_agent", "order_agent", "payment_agent", "refund_agent",
        "restaurant_agent", "delivery_partner_agent", "account_app_agent",
        "coupon_offer_agent", "visual_verification_agent",
    ]:
        graph.add_edge(agent, "confidence")


    # ─── Confidence → final routing ───────────────────────────────────────────
    graph.add_conditional_edges(
        "confidence",
        route_by_confidence,
        {
            "answer":   END,
            "clarify":  "clarify",
            "escalate": "escalate",
        },
    )

    # ─── Terminal nodes ───────────────────────────────────────────────────────
    graph.add_edge("clarify", END)
    graph.add_edge("escalate", END)

    return graph.compile()