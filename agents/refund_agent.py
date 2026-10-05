"""
SupportFlow AI — Zomato-grade Refund Agent
Handles refund requests with empathy, policy accuracy, and personalization.
Extracts context (amount, restaurant, issue type) directly from natural language.
"""
import re
from config import LLM


REFUND_SYSTEM_PROMPT = """You are SupportFlow's refund specialist — empathetic, efficient, and accurate.
Your job is to resolve refund requests quickly and fairly, like the best support agents at Zomato or Swiggy.

YOUR CAPABILITIES:
✅ Process refund requests for: cold food, wrong order, missing items, late delivery, restaurant cancellation
✅ Explain exact refund timelines based on payment method
✅ Offer alternatives: wallet credit (instant) vs bank refund (3-5 days)
✅ Handle duplicate charge disputes
✅ Follow up on existing refund requests

REFUND ELIGIBILITY RULES (apply accurately):
| Situation | Eligibility |
|-----------|-------------|
| Restaurant cancelled order | ✅ 100% full refund, no questions |
| Wrong order delivered | ✅ 100% full refund OR re-delivery |
| Missing items | ✅ Partial refund for missing items' value |
| Food arrived cold / poor quality | ✅ Partial-full refund (requires photo) |
| Delivery 60+ min late | ✅ Full refund OR compensation credit |
| Delivery 30-60 min late | ✅ Compensation credit (₹30-₹100) |
| Customer changed mind | ❌ No refund if restaurant has started preparing |
| Wrong address by customer | ❌ No refund |

REFUND TIMELINES:
- SupportFlow Wallet: ✅ INSTANT (within 2 hours)  
- UPI (PhonePe, GPay, Paytm): 2-4 business hours
- Credit/Debit Card: 3-5 business days
- Net Banking: 5-7 business days

HOW TO REQUEST A REFUND (step-by-step for customer):
1. Open app → Orders → Tap the specific order
2. Scroll down → "Report an Issue"
3. Select issue type → Upload photo if applicable
4. Choose refund method (Wallet = fastest)
5. Submit — you'll get confirmation in 5 minutes

IMPORTANT RULES:
- Always acknowledge the exact amount if customer mentioned it
- Never ask for sensitive payment details (CVV, OTP, full card number)
- Always mention the 48-hour reporting window
- If issue is older than 72 hours, offer to review on case-by-case basis
- Be empathetic FIRST, then give the policy
- End every response with a clear next step or offer to escalate"""


from database.order_service import find_order_by_id, get_recent_orders, process_instant_refund


def extract_context(query: str, history: list = None) -> dict:
    """Extract key details from customer's message and full conversation history."""
    combined = query
    if history:
        user_msgs = [m["content"] for m in history if m.get("role") == "user"]
        combined = " ".join(user_msgs + [query])

    q_lower = combined.lower()

    # Extract order ID
    order_match = re.search(r'#?(ord-?\w+|\b\d{5,}\b)', combined, re.IGNORECASE)
    order_id = order_match.group(0).upper().replace("#", "") if order_match else None
    if order_id and not order_id.startswith("ORD-") and order_id.isdigit():
        order_id = f"ORD-{order_id}"

    # Extract amount
    amount_match = re.search(r'(?:rs\.?|inr|₹)\s*(\d+)', combined, re.IGNORECASE)
    amount = f"₹{amount_match.group(1)}" if amount_match else None

    # Extract restaurant name (common names)
    restaurants = [
        "zomato", "swiggy", "behrouz", "dominos", "kfc", "mcdonalds", "pizza hut",
        "biryani", "subway", "burger king", "wow momo", "barbeque", "paradise",
        "haldirams", "theobroma", "starbucks", "chaayos", "freshmenu", "licious",
        "artisan burger", "napoli", "woodfired", "tokyo ramen"
    ]
    restaurant = None
    for r in restaurants:
        if r in q_lower:
            restaurant = r.title()
            break

    # Extract issue type
    issue_keywords = {
        "cold": "cold food",
        "wrong": "wrong order",
        "missing": "missing items",
        "cancel": "cancellation",
        "late": "late delivery",
        "duplicate": "duplicate charge",
        "charged twice": "duplicate charge",
        "hygiene": "hygiene/quality complaint",
        "cockroach": "severe quality complaint",
        "raw": "undercooked food",
        "spilled": "damaged packaging",
    }
    issue_type = None
    for keyword, issue in issue_keywords.items():
        if keyword in q_lower:
            issue_type = issue
            break

    # Desired refund method
    refund_method = "wallet" if "wallet" in q_lower else ("bank" if any(w in q_lower for w in ["bank", "card", "upi", "original"]) else None)

    return {
        "order_id": order_id,
        "amount": amount,
        "restaurant": restaurant,
        "issue_type": issue_type,
        "refund_method": refund_method,
    }


def refund_agent(state: dict) -> dict:
    """Handles refund requests and dispute queries — Zomato-grade intelligence."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-10:]
        )

    query = state["user_query"]
    ctx = extract_context(query, history)

    # Database lookup
    db_order = None
    if ctx["order_id"]:
        db_order = find_order_by_id(ctx["order_id"])

    recent_orders = []
    if not db_order:
        recent_orders = get_recent_orders(limit=2)

    # Check if user is confirming an instant refund action
    refund_confirmation = False
    processed_refund_info = None
    if any(w in query.lower() for w in ["confirm refund", "yes refund", "process refund", "refund to wallet", "refund to card"]):
        target_order_id = ctx["order_id"] or (recent_orders[0]["order_id"] if recent_orders else None)
        if target_order_id:
            processed_refund_info = process_instant_refund(
                order_id=target_order_id,
                reason=ctx["issue_type"] or "Customer complaint",
                method=ctx["refund_method"] or "wallet"
            )
            refund_confirmation = processed_refund_info.get("success", False)

    # Build context summary for the LLM
    context_summary = ""
    if ctx["order_id"]:
        context_summary += f"Order ID: {ctx['order_id']}\n"
    if ctx["amount"]:
        context_summary += f"Order amount: {ctx['amount']}\n"
    if ctx["restaurant"]:
        context_summary += f"Restaurant: {ctx['restaurant']}\n"
    if ctx["issue_type"]:
        context_summary += f"Issue type: {ctx['issue_type']}\n"

    db_context = ""
    if db_order:
        items_str = ", ".join(f"{it['qty']}x {it['name']} ({it['price']})" for it in db_order["items"])
        db_context = f"""
LIVE DATABASE RECORD FOR ORDER {db_order['order_id']}:
- Status: {db_order['status'].upper()}
- Restaurant: {db_order['restaurant_name']}
- Total Amount: {db_order['total_amount']} ({db_order['payment_method'].upper()})
- Items: {items_str}
- Delivered At: {db_order['delivered_at'] or 'Active/In-Transit'}
"""
    elif recent_orders:
        recent_str = "\n".join(
            f"• #{ro['order_id']} from {ro['restaurant_name']} ({ro['status']}) - {ro['total_amount']} [{ro['items_summary']}]"
            for ro in recent_orders
        )
        db_context = f"""
RECENT ORDERS FOUND IN CUSTOMER ACCOUNT:
{recent_str}
(If user hasn't specified an order ID, mention these recent orders!)
"""

    if refund_confirmation and processed_refund_info:
        db_context += f"""
REFUND ACTION EXECUTED:
- Refund ID: {processed_refund_info.get('refund_id')}
- Amount: {processed_refund_info.get('amount')}
- Method: {processed_refund_info.get('method')}
- Status: Successfully processed and approved!
"""

    prompt = f"""{REFUND_SYSTEM_PROMPT}

{db_context}

EXTRACTED CONTEXT:
{context_summary}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S MESSAGE: {query}

RESPONSE INSTRUCTIONS:
1. Start with genuine empathy tailored to their specific problem (e.g. cold food, late arrival, duplicate charge).
2. If real order data was found, REFERENCE IT directly (order ID, restaurant name, exact amount, items).
3. If no order ID was given, mention the recent order(s) found in their account and ask if it's for one of those.
4. If a refund was executed above, celebrate the resolution and give the exact refund ID and timeline!
5. Otherwise, state their exact refund eligibility (100% full refund vs partial), and present their 2 clear options:
   • ⚡ **Instant Wallet Credit ({ctx['amount'] or (db_order['total_amount'] if db_order else 'Full amount')})** — available within 2 hours
   • 💳 **Original Payment Method** — credited back to their bank/card in 3–5 business days
6. Close with an offer to either process the refund right now or connect with a human supervisor.

Write a complete, helpful, empathetic response now:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "refund_agent",
            "order_id": ctx["order_id"] or (db_order["order_id"] if db_order else None),
            "extracted_amount": ctx["amount"] or (db_order["total_amount"] if db_order else None),
            "extracted_restaurant": ctx["restaurant"] or (db_order["restaurant_name"] if db_order else None),
            "issue_type": ctx["issue_type"],
            "refund_executed": refund_confirmation,
        },
    }
