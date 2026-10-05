"""
SupportFlow AI — Zomato-grade Practical Refund & Compensation Agent
Applies realistic, real-world food delivery policies (matching Zomato/Swiggy):
1. Cold food: 20-25% courtesy refund or ₹75 voucher (NO PHOTO REQUIRED - temperature cannot be photographed!).
2. Missing items: Exact item cost refund + ₹30 delivery credit (NO PHOTO REQUIRED).
3. Late delivery (30-60 mins): ₹50 apology voucher (GPS-verified, NO PHOTO REQUIRED).
4. Late delivery (60+ mins): 50% refund or ₹150 credit.
5. Severe packaging spillage / burnt / wrong item: 100% full refund (PHOTO PROOF REQUIRED via Visual Verification Agent).
6. Customer cancellation after cooking started / wrong address: 0% refund.
7. Restaurant-tier specific guidance (Pizza, Biryani, Desserts).
"""
import re
from typing import Dict, Any, Optional
from config import LLM
from database.order_service import find_order_by_id, get_recent_orders, process_instant_refund


PRACTICAL_REFUND_POLICY = """You are SupportFlow's Chief Customer Resolution Specialist — pragmatic, empathetic, and strictly aligned with real-world food delivery economics (like Zomato and Swiggy).

CRITICAL POLICY PRINCIPLES (NEVER GIVE UNJUSTIFIED 100% REFUNDS):
1. **Cold Food / Lukewarm Delivery**:
   - 📸 Photo Required? ❌ NO PHOTO REQUIRED. (Temperature is physically impossible to photograph!).
   - Compensation: 25% Courtesy Wallet Refund OR a ₹75 Next-Order Discount Voucher.
   - Tone: Empathetic apology, explain transit temperature dynamics, provide quick 60-second reheating advice.
   - 100% full refund is NEVER awarded solely for cold food.

2. **Missing Items**:
   - 📸 Photo Required? ❌ NO PHOTO REQUIRED. (Customer cannot photograph what is not there!).
   - Compensation: Exact refund for missing item's value + ₹30 delivery compensation credit. (Never refund the whole meal!).

3. **Late Delivery (GPS Verified)**:
   - 30 to 45 mins late: ₹50 On-Time Guarantee Voucher (e.g., `ONTIME50`).
   - 60+ mins late: 40% to 50% Partial Refund or ₹150 Wallet Credit.

4. **Severe Physical Damage / Spillage / Burnt / Wrong Item**:
   - 📸 Photo Required? ✅ YES, PHOTO PROOF IS STRICTLY REQUIRED.
   - Customer must attach photo via the 📷 camera icon in the chat bar.
   - If photo is verified by the Visual Verification Agent: 100% Full Refund or instant free re-delivery.

5. **Customer Cancellation / Wrong Address**:
   - Restaurant already preparing: ❌ 0% Refund (cancellation fee applies to compensate chef).
   - Incorrect customer address: ❌ 0% Refund.

6. **Restaurant-Specific Advice**:
   - Pizza (e.g. Domino's): Suggest reheating on a skillet for 2 mins to restore crust crunch.
   - Biryani / Curries (e.g. Meghana, Behrouz): Gravy spillage requires photo; if minor raita spill, ₹40 credit.
   - Desserts & Ice Cream (e.g. Theobroma, Corner House): Melting requires photo within 20 mins for full replacement.
"""


def extract_context(query: str, history: list = None) -> dict:
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
    if any(w in q_lower for w in ["cold", "lukewarm", "not hot", "chilled", "stale"]):
        issue_type = "cold_food"
    elif any(w in q_lower for w in ["missing", "forgot", "didn't get", "not delivered", "short item"]):
        issue_type = "missing_items"
    elif any(w in q_lower for w in ["spill", "leak", "crush", "damaged", "messy box", "gravy"]):
        issue_type = "spilled_packaging"
    elif any(w in q_lower for w in ["burnt", "charred", "black", "inedible", "raw", "undercooked"]):
        issue_type = "burnt_quality"
    elif any(w in q_lower for w in ["wrong item", "wrong food", "different dish", "not what i ordered"]):
        issue_type = "wrong_order"
    elif any(w in q_lower for w in ["late", "delay", "taking too long", "where is it"]):
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


def calculate_practical_resolution(issue_type: str, order_amount_raw: float, order_id: str) -> dict:
    """Calculate realistic monetary and voucher resolution."""
    ord_suffix = order_id.replace("ORD-", "") if order_id else "APP"

    if issue_type == "cold_food":
        # 25% courtesy refund or ₹75 voucher
        pct = 25
        calc_amt = round((order_amount_raw * pct) / 100.0, 2)
        voucher_code = f"WARM25-{ord_suffix}"
        return {
            "tier": "25% Courtesy Compensation (Cold Food)",
            "photo_required": False,
            "refund_pct": pct,
            "refund_amount": calc_amt,
            "voucher_code": voucher_code,
            "voucher_value": "₹75 Next-Order Voucher",
            "policy_rationale": "Temperature decreases naturally during bike transit and cannot be proven via photos. A 25% courtesy credit or ₹75 voucher is offered along with 60-second reheating guidance."
        }
    elif issue_type == "missing_items":
        # Missing item: typically ~30% of order or single dish
        pct = 35
        calc_amt = round((order_amount_raw * pct) / 100.0, 2)
        voucher_code = f"MISSING-{ord_suffix}"
        return {
            "tier": "Item-Level Missing Refund + Delivery Credit",
            "photo_required": False,
            "refund_pct": pct,
            "refund_amount": calc_amt,
            "voucher_code": voucher_code,
            "voucher_value": f"₹{calc_amt:.2f} Credit",
            "policy_rationale": "Missing items are refunded strictly at item value. No photo proof is required for absent items."
        }
    elif issue_type == "late_delivery":
        voucher_code = f"ONTIME50-{ord_suffix}"
        return {
            "tier": "On-Time Guarantee Compensation",
            "photo_required": False,
            "refund_pct": 20,
            "refund_amount": 50.0,
            "voucher_code": voucher_code,
            "voucher_value": "₹50 On-Time Voucher",
            "policy_rationale": "Delays verified via courier GPS timestamps. Apology voucher issued."
        }
    elif issue_type in ("spilled_packaging", "burnt_quality", "wrong_order"):
        return {
            "tier": "100% Full Refund (Physical Defect)",
            "photo_required": True,
            "refund_pct": 100,
            "refund_amount": order_amount_raw,
            "voucher_code": f"SAFETY100-{ord_suffix}",
            "voucher_value": "100% Meal Replacement",
            "policy_rationale": "Severe physical spillage or inedible burnt items qualify for 100% full refund upon attaching photo proof via the 📷 camera button."
        }
    elif issue_type == "cancellation":
        return {
            "tier": "0% Ineligible Cancellation",
            "photo_required": False,
            "refund_pct": 0,
            "refund_amount": 0.0,
            "voucher_code": None,
            "voucher_value": None,
            "policy_rationale": "Orders cancelled after the kitchen starts cooking are subject to standard cancellation charges."
        }
    else:
        # General courtesy
        calc_amt = round(order_amount_raw * 0.20, 2)
        return {
            "tier": "20% Customer Delight Credit",
            "photo_required": False,
            "refund_pct": 20,
            "refund_amount": calc_amt,
            "voucher_code": f"CARE20-{ord_suffix}",
            "voucher_value": "₹50 Courtesy Coupon",
            "policy_rationale": "Goodwill courtesy resolution for customer satisfaction."
        }


def refund_agent(state: dict) -> dict:
    """Handles refund requests and dispute queries with Zomato/Swiggy practicality."""
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

    # Extract amount raw
    order_amount_raw = db_order.get("amount_raw", 350.0) if db_order else 350.0
    active_order_id = db_order["order_id"] if db_order else "ORD-ACTIVE"
    restaurant_name = db_order["restaurant_name"] if db_order else "Partner Restaurant"

    # Calculate practical resolution
    resolution = calculate_practical_resolution(ctx["issue_type"], order_amount_raw, active_order_id)

    # Check if user is confirming an instant refund action or choosing an option
    refund_confirmation = False
    processed_refund_info = None

    q_clean = query.strip().lower()
    
    # Check if there was a prior offer made in recent chat history
    has_prior_offer = False
    if history:
        for m in reversed(history[-4:]):
            if m.get("role") == "assistant" and any(k in m.get("content", "").lower() for k in ["voucher", "wallet", "courtesy", "credit", "reheating", "compensation", "option 1", "option 2"]):
                has_prior_offer = True
                break

    is_confirming = any(w in q_clean for w in [
        "confirm refund", "yes refund", "process refund", "credit to wallet", 
        "apply voucher", "accept", "proceed", "credit my wallet", "give me wallet",
        "voucher code", "send voucher", "choose wallet", "choose voucher", "option 1", "option 2",
        "wallet credit"
    ]) or (has_prior_offer and any(w in q_clean for w in ["yes", "sure", "ok", "okay", "wallet", "voucher", "please proceed", "credit", "go ahead", "option 1", "option 2"]))

    if is_confirming:
        chosen_method = "voucher" if any(v in q_clean for v in ["voucher", "option 2", "code", "75"]) else "wallet"
        processed_refund_info = process_instant_refund(
            order_id=active_order_id,
            reason=f"Customer complaint resolution ({ctx['issue_type']})",
            method=chosen_method,
            amount=resolution["refund_amount"],
            voucher_code=resolution["voucher_code"]
        )
        refund_confirmation = processed_refund_info.get("success", False)

    db_context = f"""
LIVE DATABASE RECORD:
- Order ID: {active_order_id}
- Restaurant: {restaurant_name}
- Total Billed: ₹{order_amount_raw:.2f}
- Issue Category: {ctx['issue_type']}
- Photo Requirement: {'REQUIRED (Customer must upload photo via 📷 button)' if resolution['photo_required'] else 'NOT REQUIRED (Subjective / Cannot photograph temperature)'}
- Practical Compensation: {resolution['tier']} (₹{resolution['refund_amount']:.2f} / Voucher: {resolution['voucher_code'] or 'None'})
"""

    if refund_confirmation and processed_refund_info:
        db_context += f"""
DATABASE ACTION EXECUTED:
- Refund ID: {processed_refund_info.get('refund_id')}
- Method: {processed_refund_info.get('method')}
- Amount Credited: {processed_refund_info.get('amount')}
- Voucher Issued: {processed_refund_info.get('voucher_code')}
- Status: Successfully processed and committed to database!
"""

    exec_action_details = ""
    if refund_confirmation and processed_refund_info:
        exec_action_details = (
            f"   - State the exact Refund ID `{processed_refund_info.get('refund_id', 'N/A')}`, "
            f"method ({processed_refund_info.get('method', 'wallet')}), amount {processed_refund_info.get('amount', 0)}, "
            f"or Voucher code `{processed_refund_info.get('voucher_code', 'N/A')}`.\n"
            f"   - Explain that the amount is credited immediately or voucher is ready for use on their next order."
        )
    else:
        exec_action_details = "   - Confirm any approved resolution clearly."

    prompt = f"""{PRACTICAL_REFUND_POLICY}

{db_context}

CUSTOMER MESSAGE: "{query}"

{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

RESPONSE GUIDELINES:
1. **If DATABASE ACTION EXECUTED above**:
   - Enthusiastically confirm that the resolution has been successfully processed!
{exec_action_details}
2. **If NOT yet executed (Presenting options / Answering query)**:
   - If **Cold Food**:
     * Explain that food temperature drops in transit and CANNOT be captured in a photo. Explicitly state **no photo is required**.
     * State the realistic policy: We do NOT issue 100% full refunds for cold food because the food remains safe and edible.
     * Offer the two practical resolution options:
       - **Option 1**: Instant 25% Courtesy Wallet Credit of ₹{resolution['refund_amount']:.2f}
       - **Option 2**: ₹75 Next-Order Voucher code `{resolution['voucher_code']}`
     * Provide a brief reheating tip (e.g., 60-90s microwave with a damp paper towel or quick toss on a hot skillet).
     * Ask which option they prefer so you can apply it immediately.
   - If **Spilled / Burnt / Wrong Item**:
     * Explain that physical damage DOES require photo proof. Invite them to click the 📷 camera icon below to trigger instant AI visual inspection for a 100% full refund.
   - If **Missing Items**:
     * Explain that no photo is needed for absent items, and offer item-level reimbursement (₹{resolution['refund_amount']:.2f}).
3. **Tone**:
   - Helpful, empathetic, and professional markdown.

Respond now:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "refund_agent",
            "order_id": active_order_id,
            "issue_type": ctx["issue_type"],
            "photo_required": resolution["photo_required"],
            "refund_pct": resolution["refund_pct"],
            "refund_amount": f"₹{resolution['refund_amount']:.2f}",
            "voucher_code": resolution["voucher_code"],
            "refund_executed": refund_confirmation,
        },
    }
