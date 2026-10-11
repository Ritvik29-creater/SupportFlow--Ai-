"""
SupportFlow AI — Situation & Restaurant-Aware Refund Agent
Applies realistic, situation-based and restaurant-specific food delivery policies:
1. Strictly ZERO photo requirement: Evaluates complaints interactively without requiring photo uploads.
2. Restaurant & Cuisine-specific guarantees:
   - Biryani & Mughlai: Handi seal vs side raita/salan leak policy.
   - Pizza & Italian: Crust integrity & topping assurance; skillet reheating advice.
   - Ice Cream & Desserts: Zero-Melt Guarantee (100% full refund/replacement for melted product).
   - Pure Veg & North Indian: Zero-tolerance dietary sanctity guarantee (Non-veg in veg = 100% + ₹200 voucher).
   - Fast Food: Combo item fulfillment & fry crunch guarantee.
3. Interactive guided resolution: Presents clear customer choice options (Wallet vs Voucher vs Original Payment)
   and executes instant database commits when confirmed.
"""
import re
from typing import Dict, Any, Optional, List
from config import LLM
from database.order_service import find_order_by_id, get_recent_orders, process_instant_refund
from database.restaurant_policies import evaluate_situation_refund, get_restaurant_policy


PRACTICAL_REFUND_POLICY = """You are SupportFlow's Chief Customer Resolution Specialist — pragmatic, empathetic, and strictly aligned with fair, transparent, and balanced platform standards.

CORE OPERATIONAL PRINCIPLES:
1. 📸 NO PHOTO PROOF REQUIRED:
   - NEVER ask the customer to upload or take a photograph.
   - Evaluate all claims textually and conversationally based on reported details, delivery telemetry, and restaurant rules.

2. 🍲 SITUATION-SPECIFIC COMPENSATION RULES (NEVER DEFAULT TO 100% FULL REFUNDS!):
   - **DO NOT ALWAYS GIVE FULL REFUNDS**: Full 100% refund is strictly reserved for catastrophic failure (dietary violation, spoiled/inedible, foreign object, or complete physical destruction).
   - **Cold / Lukewarm Food (Hot Meals)**:
     Temperature drop during two-wheeler transit across traffic is a normal physical occurrence; food remains fresh, wholesome, and safe.
     STRICTLY NEVER issue a 100% full refund for cold food!
     Issue a 25% courtesy wallet refund or ₹75 voucher (`WARM25`) along with chef reheating advice (skillet for pizza, moist microwave for biryani).
   - **Personal Taste / Spiciness / Flavor Dissatisfaction**:
     Dishes are prepared following standard recipes; taste is subjective.
     STRICTLY NEVER give a full refund. Issue a 15% goodwill coupon (`TASTE15`).
   - **Minor Packaging Leak (Side Condiment / Raita / Salan / Dip)**:
     Main course is intact and safe. Issue a 20% courtesy credit or condiment voucher.
   - **Moderate Gravy Leak (Box cracked, but 70%+ food edible)**:
     Issue a 35% partial refund or ₹100 dining voucher (`SPILL35`).
   - **Sogginess / Moisture (Fries / Crust)**:
     Steam condensation in delivery bags is natural. Issue a 20% courtesy credit (`CRISP20`) + air fryer/skillet tip.
   - **Transit Delay (15-40 mins)**:
     Issue a 15% courtesy credit or ₹50 on-time voucher (`ONTIME50`).
   - **Missing Items**:
     Refund exact item price based on the bill + ₹30 delivery credit. NEVER refund the entire order bill for one missing side!
   - **Catastrophic Failure / Severe Ruin (Smashed on floor, inedible)**:
     100% Full Refund or meal reorder voucher.
   - **Melted Ice Cream / Frozen Desserts (Zero-Melt Guarantee)**:
     If melted to warm liquid: 100% item refund or free replacement voucher. If soft: 35% courtesy credit.
   - **Dietary Sanctity Violation (Non-veg delivered for Veg)**:
     Zero tolerance policy! 100% full order refund + ₹200 apology voucher (`RESPECT200`).
   - **Cancellation after Cooking Started**:
     0% refund (standard cancellation fee to protect kitchen partners from food waste).
"""


def extract_context(query: str, history: Optional[List[Dict[str, Any]]] = None) -> dict:
    """Extract key details from customer's message and full conversation history."""
    combined = query
    if history:
        all_msgs = [m.get("content", "") for m in history]
        combined = " ".join(all_msgs + [query])

    q_lower = combined.lower()

    # Extract order ID
    order_match = re.search(r'#?(ord-?\w+|\b\d{5,}\b)', combined, re.IGNORECASE)
    order_id = order_match.group(0).upper().replace("#", "") if order_match else None
    if order_id and not order_id.startswith("ORD-") and order_id.isdigit():
        order_id = f"ORD-{order_id}"

    # Extract amount
    amount_match = re.search(r'(?:rs\.?|inr|₹)\s*(\d+)', combined, re.IGNORECASE)
    amount = f"₹{amount_match.group(1)}" if amount_match else None

    # Detect issue type
    issue_type = None
    if (("non-veg" in q_lower and "veg" in q_lower) or
        ("chicken" in q_lower and any(w in q_lower for w in ["pure veg", "ordered veg", "vegetarian", "ordered paneer"]))):
        issue_type = "dietary_violation"
    elif any(w in q_lower for w in ["melt", "melted", "liquid", "watery ice cream", "melted ice cream"]):
        issue_type = "melted_dessert"
    elif any(w in q_lower for w in ["cold", "lukewarm", "not hot", "chilled", "stale"]):
        issue_type = "cold_food"
    elif any(w in q_lower for w in ["missing", "forgot", "didn't get", "not delivered", "short item", "where is my drink"]):
        issue_type = "missing_items"
    elif any(w in q_lower for w in ["spill", "leak", "crush", "damaged", "messy box", "gravy", "bag soaked", "cracked"]):
        issue_type = "spilled_packaging"
    elif any(w in q_lower for w in ["burnt", "charred", "black", "inedible", "raw", "undercooked"]):
        issue_type = "burnt_quality"
    elif any(w in q_lower for w in ["wrong item", "wrong food", "different dish", "not what i ordered", "mismatch"]):
        issue_type = "wrong_order"
    elif any(w in q_lower for w in ["late", "delay", "taking too long", "where is it", "rider delayed"]):
        issue_type = "late_delivery"
    elif any(w in q_lower for w in ["charged twice", "duplicate", "double charge"]):
        issue_type = "duplicate_charge"
    elif any(w in q_lower for w in ["cancel", "change mind"]):
        issue_type = "cancellation"
    else:
        issue_type = "general_refund"

    refund_method = "wallet" if "wallet" in q_lower else ("voucher" if "voucher" in q_lower or "coupon" in q_lower else ("bank" if any(w in q_lower for w in ["bank", "card", "upi"]) else "wallet"))

    return {
        "order_id": order_id,
        "amount": amount,
        "issue_type": issue_type,
        "refund_method": refund_method,
    }


def refund_agent(state: dict) -> dict:
    """Handles refund requests interactively with restaurant & situation-specific policies."""
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
        if recent_orders:
            db_order = find_order_by_id(recent_orders[0]["order_id"])

    order_amount_raw = db_order.get("amount_raw", 350.0) if db_order else 350.0
    active_order_id = db_order["order_id"] if db_order else (ctx["order_id"] or "ORD-ACTIVE")
    restaurant_name = db_order.get("restaurant_name", "Partner Restaurant") if db_order else "Partner Restaurant"
    cuisine = db_order.get("cuisine", "") if db_order else ""

    # Evaluate using the comprehensive restaurant & situation engine
    resolution = evaluate_situation_refund(
        issue_type=ctx["issue_type"],
        order_data=db_order,
        user_complaint=query,
        history=history
    )

    # Check if user is confirming an instant refund action or choosing an option
    refund_confirmation = False
    processed_refund_info = None

    q_clean = query.strip().lower()

    # Check if there was a prior offer made in recent chat history
    has_prior_offer = False
    if history:
        for m in reversed(history[-4:]):
            if m.get("role") == "assistant" and any(k in m.get("content", "").lower() for k in [
                "voucher", "wallet", "courtesy", "credit", "reheating", "compensation",
                "option 1", "option 2", "option 3", "refund amount"
            ]):
                has_prior_offer = True
                break

    is_confirming = any(w in q_clean for w in [
        "confirm refund", "yes refund", "process refund", "credit to wallet",
        "apply voucher", "accept", "proceed", "credit my wallet", "give me wallet",
        "voucher code", "send voucher", "choose wallet", "choose voucher", "option 1", "option 2", "option 3",
        "wallet credit", "credit to my wallet"
    ]) or (has_prior_offer and any(w in q_clean for w in [
        "yes", "sure", "ok", "okay", "wallet", "voucher", "please proceed", "credit", "go ahead",
        "option 1", "option 2", "option 3", "1", "2"
    ]))

    if is_confirming:
        chosen_method = "voucher" if any(v in q_clean for v in ["voucher", "option 2", "code"]) else ("bank" if any(b in q_clean for b in ["bank", "card", "upi", "option 3"]) else "wallet")
        processed_refund_info = process_instant_refund(
            order_id=active_order_id,
            reason=f"Customer complaint ({ctx['issue_type']} - {resolution['tier']})",
            method=chosen_method,
            amount=resolution["refund_amount"],
            voucher_code=resolution["voucher_code"]
        )
        refund_confirmation = processed_refund_info.get("success", False)

    db_context = f"""
LIVE DATABASE RECORD & SITUATION EVALUATION:
- Order ID: {active_order_id}
- Restaurant: {restaurant_name} ({cuisine or 'Food Partner'})
- Billed Amount: ₹{order_amount_raw:.2f}
- Customer Issue Category: {ctx['issue_type']}
- Photo Requirement: ❌ ZERO PHOTO REQUIRED (Resolved conversationally)
- Policy Tier: {resolution['tier']}
- Recommended Compensation: ₹{resolution['refund_amount']:.2f} (Voucher Code: {resolution['voucher_code'] or 'None'})
- Policy Rationale: {resolution['policy_rationale']}
- Chef Reheating / Handling Tip: {resolution['reheating_tip']}
"""

    if refund_confirmation and processed_refund_info:
        db_context += f"""
DATABASE ACTION EXECUTED:
- Refund ID: {processed_refund_info.get('refund_id')}
- Method: {processed_refund_info.get('method')}
- Amount Credited: {processed_refund_info.get('amount')}
- Voucher Issued: {processed_refund_info.get('voucher_code')}
- Status: Successfully processed and committed to SQLite database!
"""

    exec_action_details = ""
    if refund_confirmation and processed_refund_info:
        exec_action_details = (
            f"   - Confirm the transaction enthusiastically with exact Refund ID `{processed_refund_info.get('refund_id', 'REF-SUCCESS')}`, "
            f"method ({processed_refund_info.get('method')}), amount {processed_refund_info.get('amount')}, "
            f"or Voucher code `{processed_refund_info.get('voucher_code', 'N/A')}`.\n"
            f"   - Explain that wallet credits are instantaneous and ready for use!"
        )
    else:
        exec_action_details = "   - Present the resolution options clearly and invite the customer to choose."

    prompt = f"""{PRACTICAL_REFUND_POLICY}

{db_context}

CUSTOMER MESSAGE: "{query}"

{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

RESPONSE GUIDELINES:
1. **Tone & Style**:
   - Empathetic, reassuring, professional markdown.
   - Mention the specific restaurant name (**{restaurant_name}**) and customer's situation context.
   - NEVER ask for photos or mention camera/upload!

2. **If DATABASE ACTION EXECUTED above**:
{exec_action_details}

3. **If NOT yet executed (Presenting resolution & options)**:
   - Respect the evaluated situation tier: **{resolution['tier']}** (Amount: ₹{resolution['refund_amount']:.2f}, Pct: {resolution['refund_pct']}%):
     * For **Cold / Lukewarm Food**: Explicitly explain that food temperature cools during two-wheeler courier transit across traffic, but the meal remains freshly cooked and safe. State clearly that **100% full refunds are not provided for cool food**. Offer the **25% courtesy wallet refund (₹{resolution['refund_amount']:.2f})** or ₹75 voucher (`{resolution['voucher_code']}`), along with the chef reheating tip: *{resolution['reheating_tip']}*.
     * For **Taste / Flavor / Spiciness**: Explain that dishes are prepared following standard recipes; taste is subjective. Offer a **15% goodwill coupon (₹{resolution['refund_amount']:.2f})**. Never give 100% refund.
     * For **Sogginess / Moisture**: Offer the **20% courtesy credit (₹{resolution['refund_amount']:.2f})** with crisping guidance.
     * For **Minor Spillage / Condiment Leak**: Offer the **20% courtesy credit** (₹{resolution['refund_amount']:.2f}) or condiment voucher.
     * For **Moderate Gravy Leak**: Offer the **35% partial refund (₹{resolution['refund_amount']:.2f})** or ₹100 voucher.
     * For **Missing Items**: Offer the item-level refund of ₹{resolution['refund_amount']:.2f} (item price + ₹30 delivery compensation). Never refund the entire meal.
     * For **Melted Ice Cream / Desserts**: Frozen desserts cannot be reheated; offer the 100% item refund (₹{resolution['refund_amount']:.2f}) or replacement voucher.
     * For **Dietary Sanctity Violation (Non-veg in Veg)**: Apologize deeply for the breach at {restaurant_name}. Offer immediate 100% full refund + ₹200 voucher (`{resolution['voucher_code']}`).
     * For **Catastrophic Ruin**: Offer 100% full refund.
   - Lay out the interactive choices clearly:
     * **Option 1**: ⚡ Instant Wallet Credit of ₹{resolution['refund_amount']:.2f}
     * **Option 2**: 🎟️ Apology Voucher `{resolution['voucher_code'] or 'None'}` ({resolution['voucher_value'] or 'Next order'})
     * **Option 3**: 💳 Original Payment Refund (3–5 business days)
   - Ask: *"Which option would you prefer so I can apply it to your account immediately?"*

Respond now:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "refund_agent",
            "order_id": active_order_id,
            "restaurant_name": restaurant_name,
            "issue_type": ctx["issue_type"],
            "refund_pct": resolution["refund_pct"],
            "refund_amount": f"₹{resolution['refund_amount']:.2f}",
            "voucher_code": resolution["voucher_code"],
            "refund_executed": refund_confirmation,
            "decision": resolution["decision"],
        },
        "resolution_details": resolution,
    }
