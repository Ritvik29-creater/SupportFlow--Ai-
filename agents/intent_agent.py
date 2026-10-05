"""
SupportFlow AI — Zomato-grade Intent Agent v2
Classifies customer intent with high accuracy using few-shot examples + sentiment context.
Handles multi-turn conversations intelligently. Supports 8 intent categories.
"""
import json
import re
from config import LLM_FAST

FOOD_DELIVERY_INTENTS = [
    "order_tracking",
    "payment",
    "refund",
    "restaurant",
    "delivery_partner",
    "account_app",
    "coupon_offer",
    "general_support",
    "unknown",
]

# Comprehensive few-shot examples for maximum accuracy
FEW_SHOT_EXAMPLES = """
EXAMPLES:
Q: "My order from Zomato is stuck on 'preparing' for 1 hour" → {"intent": "order_tracking", "confidence": 0.97}
Q: "The biryani arrived completely cold after 90 minutes" → {"intent": "refund", "confidence": 0.93}
Q: "I was charged twice on my PhonePe, Rs.450 twice" → {"intent": "payment", "confidence": 0.98}
Q: "Food from KFC was stale and had a bad smell" → {"intent": "restaurant", "confidence": 0.94}
Q: "My order was delivered to the wrong address" → {"intent": "order_tracking", "confidence": 0.91}
Q: "Where is my delivery driver? Map is not updating" → {"intent": "order_tracking", "confidence": 0.95}
Q: "I want a refund for my cancelled order" → {"intent": "refund", "confidence": 0.97}
Q: "Restaurant cancelled my order after 45 minutes, I paid Rs.800" → {"intent": "refund", "confidence": 0.96}
Q: "How do I change my delivery address?" → {"intent": "account_app", "confidence": 0.88}
Q: "Why is there a surge fee on my bill?" → {"intent": "payment", "confidence": 0.92}
Q: "The pizza had a cockroach inside, this is disgusting" → {"intent": "restaurant", "confidence": 0.99}
Q: "I didn't get my Zomato gold discount" → {"intent": "coupon_offer", "confidence": 0.89}
Q: "My money was deducted but order wasn't placed" → {"intent": "payment", "confidence": 0.97}
Q: "Missing items - ordered 4 things, only got 2" → {"intent": "order_tracking", "confidence": 0.93}
Q: "Want to know refund status for ticket TKT-1234" → {"intent": "refund", "confidence": 0.95}
Q: "The delivery boy was rude and threatened me" → {"intent": "delivery_partner", "confidence": 0.98}
Q: "Driver delivered to wrong person and is not responding" → {"intent": "delivery_partner", "confidence": 0.97}
Q: "My account got blocked, I can't log in" → {"intent": "account_app", "confidence": 0.95}
Q: "The app keeps crashing when I try to order" → {"intent": "account_app", "confidence": 0.94}
Q: "My promo code FLAT50 is not working" → {"intent": "coupon_offer", "confidence": 0.97}
Q: "How do I apply Zomato Pro benefits?" → {"intent": "coupon_offer", "confidence": 0.91}
Q: "Cash on delivery option is not showing" → {"intent": "payment", "confidence": 0.88}
Q: "Food poisoning from the burger I ordered yesterday" → {"intent": "restaurant", "confidence": 0.99}
Q: "I need GST invoice for my order" → {"intent": "payment", "confidence": 0.85}
Q: "What is the authentic recipe for Hyderabadi Dum Biryani?" → {"intent": "restaurant", "confidence": 0.98}
Q: "How is Margherita D.O.C Pizza prepared and what ingredients are inside?" → {"intent": "restaurant", "confidence": 0.98}
Q: "Which restaurant in Indiranagar has the best pizza or pasta?" → {"intent": "restaurant", "confidence": 0.96}
Q: "My order was just delivered, but the food arrived cold and soggy" → {"intent": "restaurant", "confidence": 0.97}
Q: "Recommend healthy high-protein meals from SupportFlow restaurants" → {"intent": "restaurant", "confidence": 0.95}
"""


def intent_agent(state: dict) -> dict:
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
        )

    sentiment_data = state.get("sentiment_data", {})
    sentiment_hint = ""
    if sentiment_data.get("sentiment") == "very_upset":
        sentiment_hint = "\nNote: Customer appears very distressed — lean toward escalation if ambiguous."

    prompt = f"""You are an expert intent classifier for SupportFlow, a food delivery customer support system.

Classify the customer's query into EXACTLY ONE intent:
- order_tracking: order status, delivery tracking, stuck order, missing items, wrong items, delivery issues, driver location, delivery ETA
- payment: charges, duplicate payment, overcharged, UPI issue, payment failed, surge fee, invoice, wallet, cash on delivery, GST, billing
- refund: wants money back, cancellation refund, compensation, dispute resolution, refund status, refund not received
- restaurant: food quality, cold food, arrived cold, stale food, wrong food, hygiene, restaurant complaint, food safety, spilled packaging, recipe questions, how food is made, ingredients, cooking process, restaurant recommendations, menu inquiries, best dishes, dietary food questions
- delivery_partner: rude delivery person, delivery partner behavior, driver not responding, wrong delivery, delivery partner complaint
- account_app: app crash, login issues, account blocked, password reset, profile changes, address management, notifications, app bug
- coupon_offer: promo code not working, discount not applied, cashback issue, Zomato Pro/Gold, subscription benefits
- general_support: everything else that doesn't fit above — policies, general questions, how-to
- unknown: completely unclear, abusive, or off-topic

{FEW_SHOT_EXAMPLES}

{f"Recent conversation:{chr(10)}{history_text}{chr(10)}" if history_text else ""}
Current query: {state["user_query"]}
{sentiment_hint}

Rules:
- If message mentions both tracking AND refund, prefer "refund" if customer explicitly asks for money back
- If message mentions payment issue AND refund, prefer "payment" if no explicit refund request
- If message is about a rude/threatening delivery person, always use "delivery_partner"
- If message is about food safety (food poisoning, cockroach, etc.), always use "restaurant"
- Consider the FULL conversation history, not just the current message
- For very short/unclear messages in an ongoing conversation, use history context to decide

Respond with ONLY valid JSON:
{{"intent": "<intent>", "confidence": <float 0.0-1.0>}}
"""

    try:
        resp = LLM_FAST.invoke(prompt).content.strip()
        # Strip markdown code fences if present
        resp = re.sub(r"^```(?:json)?\s*", "", resp)
        resp = re.sub(r"\s*```$", "", resp)
        # Extract JSON if surrounded by other text
        json_match = re.search(r'\{[^}]+\}', resp)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(resp)
        intent = parsed.get("intent", "unknown")
        confidence = float(parsed.get("confidence", 0.5))
        if intent not in FOOD_DELIVERY_INTENTS:
            intent = "general_support"
            confidence = 0.5
    except Exception:
        intent = "general_support"
        confidence = 0.5

    return {
        "intent": intent,
        "intent_confidence": confidence,
    }