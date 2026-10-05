"""
SupportFlow AI — Zomato-grade Payment Agent
Handles payment disputes, duplicate charges, failed payments, billing questions.
Provides precise, reassuring guidance without requesting sensitive information.
"""
import re
from config import LLM


PAYMENT_SYSTEM_PROMPT = """You are SupportFlow's payment & billing specialist.
You handle payment disputes with the accuracy and reassurance of a top fintech support agent.

YOUR CAPABILITIES:
✅ Explain duplicate/double charge situations
✅ Resolve payment failure (money deducted, no order created)
✅ Explain bill breakdown (delivery fee, surge, taxes, service fee)
✅ Handle promo/coupon not applied
✅ Wallet balance issues (top-up, refund to wallet)
✅ Invoice requests for GST/business expense

DUPLICATE CHARGE GUIDE:
Common scenario: "I was charged twice"
→ Step 1: Check if one is a "pending authorization" (not actual debit) — auto-reverses in 24-48h
→ Step 2: Check app invoice to confirm what was actually charged
→ Step 3: If genuinely double charged → auto-reversal in 3-5 business days
→ Step 4: If not reversed after deadline → escalate to billing team within 24h

PAYMENT FAILURE GUIDE (money gone but no order):
→ Almost always a network timeout — money is held, NOT deducted
→ Bank releases hold within 24-48 hours automatically
→ If genuinely deducted (check bank statement after 48h) → escalate for manual refund

BILL BREAKDOWN (what customers see):
- Food subtotal: restaurant price
- Delivery fee: distance-based (₹15-₹80 typically)
- Platform fee: small service charge (₹3-₹7)
- Surge pricing: during high demand (disclosed at checkout)
- GST: 5% on food, 18% on delivery (standard India)
- Delivery tip: optional (goes 100% to delivery partner)

PROMO/COUPON NOT APPLIED:
Common reasons:
1. Minimum order value not met
2. Promo expired
3. Restaurant not included in promo
4. Single-use promo already used
5. Can't be stacked with another active promo

IMPORTANT SECURITY RULES (ALWAYS mention if relevant):
⚠️ We NEVER ask for your full card number, CVV, or OTP
⚠️ Only share last 4 digits of card for verification
⚠️ All payments processed through PCI-DSS compliant gateways
⚠️ If someone asks for your payment details claiming to be SupportFlow support — hang up, it's a fraud

RESOLUTION TIMELINES:
- Auto-reversal (pending hold): 24-48 hours
- Duplicate charge refund: 3-5 business days (card) / 2-4 hours (UPI)
- Payment failure refund: 24-48 hours auto, or 24h manual escalation
- Billing team escalation: Response within 24 hours"""


def extract_payment_context(query: str) -> dict:
    """Extract payment details from customer message."""
    q_lower = query.lower()

    # Amounts
    amounts = re.findall(r'(?:rs\.?|inr|₹)\s*(\d+)', query, re.IGNORECASE)
    charged = f"₹{amounts[0]}" if amounts else None
    expected = f"₹{amounts[1]}" if len(amounts) > 1 else None

    # Payment method
    method = None
    if any(w in q_lower for w in ["upi", "phonepe", "gpay", "paytm", "google pay", "bhim"]):
        method = "UPI"
    elif any(w in q_lower for w in ["credit card", "credit", "visa", "mastercard", "amex"]):
        method = "Credit Card"
    elif any(w in q_lower for w in ["debit card", "debit", "atm card"]):
        method = "Debit Card"
    elif any(w in q_lower for w in ["wallet", "zomato money", "supportflow wallet"]):
        method = "Wallet"
    elif any(w in q_lower for w in ["net banking", "netbanking", "bank transfer"]):
        method = "Net Banking"

    # Issue type
    issue = "billing_question"
    if any(w in q_lower for w in ["twice", "double", "duplicate", "charged twice", "two times"]):
        issue = "duplicate_charge"
    elif any(w in q_lower for w in ["failed", "not placed", "deducted but", "money gone"]):
        issue = "payment_failure"
    elif any(w in q_lower for w in ["promo", "coupon", "discount", "offer", "cashback"]):
        issue = "promo_not_applied"
    elif any(w in q_lower for w in ["overcharged", "extra", "more than", "surge"]):
        issue = "overcharged"

    return {
        "charged": charged,
        "expected": expected,
        "method": method,
        "issue": issue,
    }


def payment_agent(state: dict) -> dict:
    """Handles payment and billing queries — Zomato-grade intelligence."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-10:]
        )

    query = state["user_query"]
    ctx = extract_payment_context(query)

    context_summary = f"Payment issue type: {ctx['issue']}\n"
    if ctx["charged"]:
        context_summary += f"Amount charged: {ctx['charged']}\n"
    if ctx["expected"]:
        context_summary += f"Expected amount: {ctx['expected']}\n"
    if ctx["method"]:
        context_summary += f"Payment method: {ctx['method']}\n"

    issue_guidance = {
        "duplicate_charge": "Explain the pending authorization concept, confirm reversal process, give precise timelines based on their payment method",
        "payment_failure": "Reassure them money is likely a hold not a charge, explain the 48h auto-reversal, give escalation path if it doesn't reverse",
        "promo_not_applied": "Explain common reasons promos don't apply, guide them to check expiry/minimum order/restaurant eligibility, offer compensation if eligible",
        "overcharged": "Break down the bill components, explain surge pricing and platform fee transparency, offer escalation to billing team if still incorrect",
        "billing_question": "Answer the specific billing question, provide invoice download instructions, explain GST breakdown",
    }
    guidance = issue_guidance.get(ctx["issue"], issue_guidance["billing_question"])

    prompt = f"""{PAYMENT_SYSTEM_PROMPT}

EXTRACTED CONTEXT:
{context_summary}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S MESSAGE: {query}

RESPONSE FOCUS: {guidance}

RESPONSE RULES:
1. Start by acknowledging the specific payment issue — mention the amounts if provided
2. Distinguish between a real charge and a pending authorization (crucial for duplicate charge cases)
3. Give the exact resolution process step by step
4. Provide precise timelines based on their payment method ({ctx['method'] or 'mention all methods'})
5. NEVER ask for sensitive payment data (full card number, CVV, OTP, PIN)
6. If amount is large (>₹1000), proactively offer to escalate to billing team
7. Close with clear next step if the auto-process doesn't work
8. Use **bold** for amounts, timelines, and important warnings

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "payment_agent",
            "issue_type": ctx["issue"],
            "payment_method": ctx["method"],
        },
    }
