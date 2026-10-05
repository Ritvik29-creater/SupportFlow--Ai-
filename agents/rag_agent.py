"""
SupportFlow AI — Zomato-grade RAG Agent v2
Retrieves relevant support documentation and generates highly accurate grounded answers.
Features: MMR retrieval, query rewriting, multi-turn context, grounding check, sentiment-aware tone.
"""
import re
from config import LLM, LLM_FAST
from rag.retriever import retriever, mmr_retriever
from agents.grounding_guard import is_grounded


MIN_CONTEXT_LENGTH = 200  # characters


def rewrite_query(query: str, intent: str, history: list) -> str:
    """Rewrite query to be clearer and more searchable, incorporating conversation context."""
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-4:]
        )

    prompt = f"""Rewrite the following customer support query to be clearer and more searchable for a food delivery support knowledge base.

Intent category: {intent}
{f"Conversation History:{chr(10)}{history_text}{chr(10)}" if history_text else ""}
Original query: {query}

Rules:
- Make it self-contained (incorporate relevant context from history)
- Use clear food delivery terminology (refund, delivery, payment, restaurant quality, etc.)
- Keep it concise — one clear question or topic
- Return ONLY the rewritten query, no explanation
"""
    try:
        return LLM_FAST.invoke(prompt).content.strip()
    except Exception:
        return query


def build_rag_prompt(query: str, context: str, history: list, intent: str, sentiment_data: dict) -> str:
    """Build a structured prompt for grounded, intelligent customer support answers."""
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
        )

    tone_modifier = sentiment_data.get("tone_modifier", "Be professional and empathetic.")
    urgency = sentiment_data.get("urgency", "low")

    urgency_note = ""
    if urgency == "high":
        urgency_note = "\n⚡ URGENCY: HIGH — This customer needs quick, decisive action. Lead with the most important step first.\n"

    return f"""You are SupportFlow's intelligent customer support AI — like Zomato's support bot, but smarter and more empathetic.
You are trained to resolve food delivery issues with accuracy, empathy, and actionable advice.

TONE GUIDANCE: {tone_modifier}
{urgency_note}

KNOWLEDGE BASE (your primary source of truth — always use this):
{context}

{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER QUERY (Intent: {intent.replace("_", " ").title()}): {query}

STRICT RESPONSE RULES:
1. START with a brief, genuine empathetic acknowledgment of their SPECIFIC problem (not generic "I understand your concern")
2. Give a CLEAR, DIRECT answer — never be vague or evasive
3. Provide numbered step-by-step instructions when applicable
4. Include SPECIFIC timelines from the knowledge base (e.g., "refund in 2-4 hours for UPI")
5. Use **bold** for amounts, timelines, action items, and important warnings
6. If multiple options exist (wallet credit vs bank refund): present both with pros/cons
7. End with a clear next step OR offer to escalate to a human agent if unresolved
8. Keep response under 300 words — be concise but COMPLETE
9. DO NOT make up policies, timelines, or amounts not in the knowledge base
10. If genuinely unsure, say so honestly and offer escalation — never hallucinate

ANSWER:"""


def rag_agent(state: dict) -> dict:
    query = state["user_query"]
    history = state.get("conversation_history", [])
    intent = state.get("intent", "general_support")
    sentiment_data = state.get("sentiment_data", {})

    # Step 1: MMR retrieval (diversity + relevance)
    try:
        docs = mmr_retriever.invoke(query)
        context = "\n\n---\n\n".join(d.page_content for d in docs)
    except Exception:
        docs = retriever.invoke(query)
        context = "\n\n---\n\n".join(d.page_content for d in docs)

    # Step 2: If context is thin — rewrite and retry with similarity search
    if len(context) < MIN_CONTEXT_LENGTH:
        rewritten = rewrite_query(query, intent, history)
        try:
            docs2 = retriever.invoke(rewritten)
            context2 = "\n\n---\n\n".join(d.page_content for d in docs2)
            if len(context2) > len(context):
                docs = docs2
                context = context2
        except Exception:
            pass

    # Step 3: If still thin — use intent-based fallback keywords
    if len(context) < MIN_CONTEXT_LENGTH:
        intent_keywords = {
            "refund": "refund policy food delivery cancellation compensation",
            "order_tracking": "order delivery tracking missing items food delivery",
            "payment": "payment billing charges duplicate food delivery invoice",
            "restaurant": "restaurant complaint food quality hygiene food safety",
            "delivery_partner": "delivery partner complaint rude behavior misconduct",
            "account_app": "account login app technical support password reset",
            "coupon_offer": "promo code coupon discount cashback food delivery offer",
            "general_support": "customer support food delivery help policy",
        }
        fallback_query = intent_keywords.get(intent, "food delivery customer support")
        try:
            docs = retriever.invoke(fallback_query)
            context = "\n\n---\n\n".join(d.page_content for d in docs)
        except Exception:
            pass

    # Step 4: Generate grounded, sentiment-aware answer
    prompt = build_rag_prompt(query, context, history, intent, sentiment_data)
    answer = LLM.invoke(prompt).content.strip()

    # Step 5: Grounding guardrail — check for hallucinations
    if context and len(context) > 100 and not is_grounded(answer, context):
        strict_prompt = f"""You are a food delivery support AI. Answer ONLY based on the context below.

Context:
{context}

Customer query: {query}

RULES:
- Base your answer only on the context provided
- If the context doesn't fully cover the question, say: "I don't have complete details on that, but here's what I can tell you from our policies..."
- Always offer to escalate to a human agent if you can't fully resolve it
- Be empathetic and helpful

Answer:"""
        answer = LLM.invoke(strict_prompt).content.strip()

    return {
        "retrieved_docs": [d.metadata.get("source", "") for d in docs],
        "answer": answer,
        "force_escalate": False,
    }
