"""
SupportFlow AI — Coupon & Offers Agent
Handles promo codes, cashback, SupportFlow Pro/Gold benefits, subscription issues.
"""
import re
from config import LLM


COUPON_SYSTEM_PROMPT = """You are SupportFlow's promotions & offers specialist.
You resolve promo code issues with accuracy and ensure customers get the benefits they deserve.

YOUR CAPABILITIES:
✅ Diagnose why a promo code or coupon didn't apply
✅ Explain cashback timelines and how to claim
✅ Handle SupportFlow Pro / Gold subscription benefits
✅ Resolve referral reward issues
✅ Process compensation for incorrectly missed discounts
✅ Explain subscription benefits and how to activate them

PROMO CODE TROUBLESHOOTING GUIDE:

COMMON REASONS CODES DON'T WORK:
1. ❌ Minimum order value not met (check the code's T&Cs)
2. ❌ Code is restaurant-specific (not valid for the selected restaurant)
3. ❌ Code has expired (check expiry date carefully)
4. ❌ Single-use code already used on another order
5. ❌ Code can't be stacked with another active promo
6. ❌ Code is for first-time users only (account has prior orders)
7. ❌ Payment method restriction (e.g., valid only for UPI payments)
8. ❌ Geographic restriction (only valid in certain cities)
9. ❌ Category restriction (e.g., valid for biryani orders only)

HOW TO APPLY A CODE:
1. Add items to cart
2. Proceed to checkout
3. Look for "Apply Coupon" section
4. Type or paste the exact code (case-sensitive for some codes)
5. Tap Apply

CASHBACK TIMELINES:
- Instant cashback: Applied at time of order (visible in order total)
- UPI cashback: 1-3 business days (credited by payment provider)
- Wallet cashback: Within 24 hours
- Bank cashback: 7-21 days (as per bank policy)

SUPPORTFLOW PRO/GOLD BENEFITS:
- Free delivery on orders above minimum (varies by city)
- Exclusive member-only discounts (10-30% off)
- Priority customer support
- Early access to restaurant offers
- Gold: Additional dining discounts

IF ELIGIBLE DISCOUNT WASN'T APPLIED:
- If code was valid but didn't apply due to app error: Full compensation of missed discount
- If code wasn't used at all but was valid: Apply retroactively as wallet credit
- Processing: Within 24 hours after review

IMPORTANT RULES:
- Never promise to apply expired codes — even if unfair, policy cannot be overridden
- For valid missed discounts due to technical error: Always compensate
- Always check if the customer is a Pro/Gold member when handling offers"""


def coupon_offer_agent(state: dict) -> dict:
    """Handles promo codes, cashback, and subscription benefit issues."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-8:]
        )

    query = state["user_query"]
    q_lower = query.lower()
    sentiment_data = state.get("sentiment_data", {})
    tone = sentiment_data.get("tone_modifier", "Be friendly and helpful.")

    # Extract promo code if mentioned
    code_match = re.search(r'\b([A-Z]{2,}[\d]{0,4}|[\d]{0,4}[A-Z]{2,})\b', query)
    promo_code = code_match.group() if code_match else None

    # Classify issue type
    issue_type = "general_promo"
    if any(w in q_lower for w in ["not working", "not applying", "invalid", "error", "doesn't work"]):
        issue_type = "code_not_working"
    elif any(w in q_lower for w in ["cashback", "refund", "money back", "credited"]):
        issue_type = "cashback_issue"
    elif any(w in q_lower for w in ["pro", "gold", "subscription", "premium", "membership"]):
        issue_type = "subscription_benefits"
    elif any(w in q_lower for w in ["referral", "refer", "invite"]):
        issue_type = "referral_reward"

    prompt = f"""{COUPON_SYSTEM_PROMPT}

ISSUE TYPE: {issue_type.replace("_", " ").upper()}
{f"PROMO CODE MENTIONED: {promo_code}" if promo_code else ""}
TONE GUIDANCE: {tone}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S MESSAGE: {query}

RESPONSE INSTRUCTIONS:
1. Acknowledge the specific promo/discount issue they're facing
2. If code isn't working: walk through the most likely reasons (numbered list) in order of likelihood
3. Give them specific steps to troubleshoot and verify the code
4. If the code should have worked (valid, correct restaurant, met minimum): offer wallet compensation
5. For cashback: give exact timeline for their payment method
6. For Pro/Gold members: explain how to activate the benefit they're missing
7. End with: what to do if the issue isn't resolved (reply here for manual review)
8. Use **bold** for code names, amounts, and timelines
9. Keep under 220 words but be complete

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "coupon_offer_agent",
            "issue_type": issue_type,
            "promo_code": promo_code,
        },
    }
