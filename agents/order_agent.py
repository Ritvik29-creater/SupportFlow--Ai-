"""
SupportFlow AI — Zomato-grade Order Tracking Agent
Handles delivery tracking, stuck orders, missing items, wrong orders, late deliveries.
Gives actionable, real-time guidance like a live support agent.
"""
import re
from config import LLM


ORDER_SYSTEM_PROMPT = """You are SupportFlow's order tracking & delivery specialist.
You handle real-time order issues with the urgency and accuracy of a top-tier food delivery support agent.

YOUR CAPABILITIES:
✅ Order status explanations (Placed → Confirmed → Preparing → Out for Delivery → Delivered)
✅ Delayed delivery guidance (when to wait, when to act, when to escalate)
✅ Missing/wrong item resolution
✅ Driver contact guidance
✅ Order cancellation advice
✅ Live order issue escalation

ORDER STATUS GUIDE (explain clearly to customers):
- "Order Placed": Restaurant received order, waiting for confirmation
- "Confirmed": Restaurant accepted, cooking started
- "Preparing": Kitchen actively cooking your food
- "Ready for Pickup": Food ready, waiting for delivery partner
- "Out for Delivery": Driver picked up, on the way to you
- "Delivered": Marked as delivered

DELAY THRESHOLDS AND ACTIONS:
⏰ 0-15 min delay: Normal, no action needed
⏰ 15-30 min delay: Check live tracking, driver may be stuck in traffic
⏰ 30-60 min delay: Contact driver → contact restaurant → consider cancelling
⏰ 60+ min delay: ESCALATE immediately, full refund eligible, press our ops team
⏰ Stuck on "Preparing" 45+ min: Restaurant may have lost the order — escalate

MISSING ITEMS ACTION PLAN:
1. Take photos of received items immediately
2. Orders → Report Issue → "Missing Items"
3. Select each missing item individually
4. Choose: instant wallet refund OR re-delivery (within 2km, within 30 min)
5. Resolution: typically within 15-30 minutes

WRONG ORDER ACTION PLAN:
1. Don't eat it (especially if allergen concern)
2. Take photo of what you received
3. Orders → Report Issue → "Received Wrong Order"
4. Eligible for: full refund OR fresh re-delivery
5. Wrong food is always a full refund case — no questions asked

IMPORTANT RULES:
- Never ask for order ID if the customer has already described the issue clearly
- Give estimated wait times and exact steps, not vague advice
- For orders stuck 60+ min, always offer to escalate to ops team
- Be empathetic but action-oriented — customers are frustrated when food is late"""


from database.order_service import find_order_by_id, get_recent_orders


def extract_order_context(query: str, history: list = None) -> dict:
    """Extract order details from customer message and conversation history."""
    combined = query
    if history:
        user_msgs = [m["content"] for m in history if m.get("role") == "user"]
        combined = " ".join(user_msgs + [query])
    
    q_lower = combined.lower()

    # Order ID
    order_match = re.search(r'#?(ord-?\w+|\b\d{5,}\b)', combined, re.IGNORECASE)
    order_id = order_match.group(0).upper().replace("#", "") if order_match else None
    if order_id and not order_id.startswith("ORD-") and order_id.isdigit():
        order_id = f"ORD-{order_id}"

    # Time waited
    time_match = re.search(r'(\d+)\s*(?:min|minute|hour|hr)', q_lower)
    wait_time = time_match.group(0) if time_match else None

    # Amount
    amount_match = re.search(r'(?:rs\.?|inr|₹)\s*(\d+)', combined, re.IGNORECASE)
    amount = f"₹{amount_match.group(1)}" if amount_match else None

    # Issue type
    issue = "delivery_delay"
    if any(w in q_lower for w in ["missing", "not there", "forgot", "incomplete"]):
        issue = "missing_items"
    elif any(w in q_lower for w in ["wrong", "different", "not what i ordered"]):
        issue = "wrong_order"
    elif any(w in q_lower for w in ["stuck", "preparing", "no update", "not moving"]):
        issue = "stuck_order"
    elif any(w in q_lower for w in ["cancelled", "cancel", "restaurant closed"]):
        issue = "cancelled_order"

    return {
        "order_id": order_id,
        "wait_time": wait_time,
        "amount": amount,
        "issue": issue,
    }


def order_agent(state: dict) -> dict:
    """Handles order tracking, delivery issues, missing/wrong items — Zomato-grade."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-10:]
        )

    query = state["user_query"]
    ctx = extract_order_context(query, history)

    # Database lookup
    db_order = None
    if ctx["order_id"]:
        db_order = find_order_by_id(ctx["order_id"])

    recent_orders = []
    if not db_order:
        recent_orders = get_recent_orders(limit=2)

    # Build context summary
    context_summary = f"Issue type: {ctx['issue']}\n"
    if ctx["order_id"]:
        context_summary += f"Order ID: {ctx['order_id']}\n"
    if ctx["wait_time"]:
        context_summary += f"Wait time mentioned: {ctx['wait_time']}\n"
    if ctx["amount"]:
        context_summary += f"Order amount: {ctx['amount']}\n"

    db_context = ""
    if db_order:
        items_str = ", ".join(f"{it['qty']}x {it['name']} ({it['price']})" for it in db_order["items"])
        db_context = f"""
LIVE DATABASE RECORD FOR ORDER {db_order['order_id']}:
- Status: {db_order['status'].upper()}
- Restaurant: {db_order['restaurant_name']} ({db_order['cuisine']})
- Total Amount: {db_order['total_amount']} ({db_order['payment_method'].upper()} - {db_order['payment_status']})
- Delivery Address: {db_order['delivery_address']}
- Delivery Partner: {db_order['driver_name']} (Phone: {db_order['driver_phone']})
- Estimated Delivery: {db_order['estimated_delivery_at']}
- Items in Order: {items_str}
- Special Instructions: {db_order['special_instructions']}
"""
    elif recent_orders:
        recent_str = "\n".join(
            f"• #{ro['order_id']} from {ro['restaurant_name']} ({ro['status']}) - {ro['total_amount']} [{ro['items_summary']}]"
            for ro in recent_orders
        )
        db_context = f"""
RECENT ORDERS FOUND IN CUSTOMER ACCOUNT:
{recent_str}
(If customer hasn't mentioned an order ID, reference these active/recent orders so they can confirm!)
"""

    issue_guidance = {
        "missing_items": "Focus on: eligibility (always eligible), how to report missing items, offer partial refund or re-delivery",
        "wrong_order": "Focus on: full refund eligibility, don't eat if allergen concern, photo proof needed, re-delivery option",
        "stuck_order": "Focus on: when to call restaurant, when to cancel, when to escalate, refund eligibility",
        "cancelled_order": "Focus on: automatic full refund, timeline, no action needed from customer",
        "delivery_delay": "Focus on: steps to track, driver contact, when delay becomes refund-eligible",
    }
    guidance = issue_guidance.get(ctx["issue"], issue_guidance["delivery_delay"])

    prompt = f"""{ORDER_SYSTEM_PROMPT}

{db_context}

EXTRACTED CONTEXT:
{context_summary}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S MESSAGE: {query}

RESPONSE FOCUS: {guidance}

RESPONSE RULES:
1. If LIVE DATABASE RECORD is provided above, USE THE REAL DATA! Mention the restaurant name, exact driver name, phone number, and ETA accurately.
2. If customer's order is delayed or out for delivery, give them the driver contact and reassure them with real ETA.
3. If no order ID was given, mention the recent order(s) found in their account so they can simply say 'yes' or pick one.
4. Give IMMEDIATE actionable steps they can take right now.
5. If order is very delayed (60+ min), offer to cancel with full refund or connect to human supervisor.
6. Use **bold** for important actions, times, driver details, and options.
7. Keep it warm, empathetic, concise, and structured.

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "order_agent",
            "issue_type": ctx["issue"],
            "order_id": ctx["order_id"] or (db_order["order_id"] if db_order else None),
            "db_order_found": bool(db_order),
        },
    }
