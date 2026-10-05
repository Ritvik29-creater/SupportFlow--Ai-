"""
SupportFlow AI — Zomato-grade Clarification Agent
Asks targeted, context-aware follow-up questions.
Never redundantly asks for info the customer already provided.
Smart enough to spot implicit context.
"""
import re
from config import LLM


def extract_provided_info(query: str, history: list = None) -> dict:
    """Detect what information the customer has already provided across entire chat."""
    combined = query
    if history:
        user_msgs = [m["content"] for m in history if m.get("role") == "user"]
        combined = " ".join(user_msgs + [query])
    
    q_lower = combined.lower()
    return {
        "has_amount": bool(re.search(r'(?:rs\.?|inr|₹)\s*\d+', combined, re.IGNORECASE)),
        "has_restaurant": any(r in q_lower for r in [
            "dominos", "kfc", "mcdonald", "pizza hut", "behrouz", "zomato", "swiggy",
            "biryani", "restaurant", "burger king", "subway", "wow momo", "artisan", "napoli"
        ]),
        "has_order_id": bool(re.search(r'#?(ord-?\w+|\b\d{5,}\b)', combined, re.IGNORECASE)),
        "has_time": bool(re.search(r'\d+\s*(?:min|hour|hr|days?)', q_lower)),
        "has_payment_method": any(p in q_lower for p in [
            "upi", "gpay", "phonepe", "paytm", "card", "wallet", "cod", "cash", "netbanking"
        ]),
        "has_issue_description": len(combined.split()) >= 6 or any(w in q_lower for w in ["cold", "late", "missing", "wrong", "cancel", "duplicate", "delay", "bad"]),
    }


def clarification_agent(state: dict) -> dict:
    """Generates a single, smart clarifying question — Zomato-grade conversation."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-8:]
        )

    intent = state.get("intent", "general_support")
    user_query = state.get("user_query", "")
    info = extract_provided_info(user_query, history)

    # Build a picture of what's still missing
    missing = []

    if intent == "refund":
        if not info["has_issue_description"]:
            missing.append("what exactly went wrong (cold food, missing items, wrong order, restaurant cancelled?)")
        if not info["has_amount"] and not history_text:
            missing.append("the order amount (helps us process the refund faster)")
        if not info["has_time"]:
            missing.append("when this happened (refunds must be reported within 48 hours)")

    elif intent == "order_tracking":
        if not info["has_restaurant"] and not info["has_order_id"]:
            missing.append("the restaurant name or order ID so we can look into it")
        if not info["has_time"]:
            missing.append("how long you've been waiting / when you placed the order")

    elif intent == "payment":
        if not info["has_amount"]:
            missing.append("the exact amount you were charged vs what you expected")
        if not info["has_payment_method"]:
            missing.append("your payment method (UPI, card, wallet?) — this affects the refund timeline")

    elif intent == "restaurant":
        if not info["has_restaurant"]:
            missing.append("the restaurant name")
        if not info["has_issue_description"]:
            missing.append("what specifically was wrong with the food (quality, wrong item, hygiene?)")

    else:  # general_support
        if not info["has_issue_description"]:
            missing.append("exactly what issue you're facing — is it about an order, payment, account, or something else?")

    # Pick the single most important missing piece
    top_missing = missing[0] if missing else "any additional details about the issue"

    prompt = f"""You are a warm, helpful food delivery support agent for SupportFlow.
The customer's issue needs one more piece of information to be resolved properly.

Customer intent: {intent}
Customer's message: {user_query}
{f"Conversation so far:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

The most important missing information: {top_missing}

Write ONE short clarifying question (1-2 sentences max) that:
1. Starts with a brief empathetic acknowledgment (e.g., "I understand you're frustrated!", "I'm sorry to hear that!")
2. Asks specifically for: {top_missing}
3. Is warm and conversational — NOT robotic or formal
4. Does NOT ask for multiple things at once
5. Does NOT ask for info the customer already provided

Examples of good clarifying questions:
- "I completely understand your frustration! Could you tell me which restaurant this order was from?"
- "I'm sorry about the payment issue! Just to help you faster — was this a UPI payment or credit/debit card?"
- "I want to make sure you get the right refund. Did the food arrive cold, or were items missing from the bag?"

Write your single clarifying question now:"""

    question = LLM.invoke(prompt).content.strip()

    return {
        "answer": question,
    }
