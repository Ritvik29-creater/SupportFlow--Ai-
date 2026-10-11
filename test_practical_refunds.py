"""
SupportFlow AI — Comprehensive Refund & Policy Test Suite (Zero-Photo Flow)
Tests:
1. Spilled packaging at Meghana Foods (Severe damage) -> 100% full refund offered WITHOUT any photo demand.
2. Confirming wallet refund -> SQLite database commitment with live Refund ID and credit amount.
3. Melted ice cream at Corner House -> Zero-Melt cold-chain policy triggers 100% refund.
4. Cold food at Domino's -> 25% courtesy refund or ₹75 voucher + skillet reheating tip.
5. Dietary violation (Non-veg delivered for Veg) -> 100% refund + ₹200 apology voucher (RESPECT200).
6. Missing item -> Item-level price + ₹30 delivery credit.
"""
import sys
from core.graph import build_graph

sys.stdout.reconfigure(encoding='utf-8')

graph = build_graph()

def run_turn(query: str, session_id: str, history: list):
    state = {
        "user_query": query,
        "session_id": session_id,
        "customer_id": "test_user",
        "order_id": None,
        "image_base64": None,
        "image_type": None,
        "conversation_history": history,
        "force_escalate": False,
        "retrieved_docs": [],
        "agent_metadata": {},
        "sentiment_data": {},
    }
    result = graph.invoke(state)
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": result.get("answer", "")})
    return result

print("="*70)
print("TEST 1: SPILLED GRAVY COMPLAINT (MEGHANA FOODS) - ZERO PHOTO PROOF")
print("="*70)
sess_1 = []
r1 = run_turn(
    "My order ORD-11253 from Meghana Foods arrived with curry leaked all over the bag and the biryani box was broken and soaked through! Can I get a full refund?",
    "sess_spill_meghana",
    sess_1
)
print("Agent:", r1.get("agent_metadata", {}).get("specialized_agent"))
print("Refund Tier:", r1.get("agent_metadata", {}).get("decision"))
print("Bot Answer:\n", r1.get("answer"))

print("\n" + "="*70)
print("TEST 2: CUSTOMER CONFIRMS OPTION 1 (INSTANT WALLET CREDIT)")
print("="*70)
r2 = run_turn(
    "Yes, please credit Option 1 to my SupportFlow wallet immediately.",
    "sess_spill_meghana",
    sess_1
)
print("Refund Executed in DB:", r2.get("agent_metadata", {}).get("refund_executed"))
print("Refund Amount:", r2.get("agent_metadata", {}).get("refund_amount"))
print("Bot Answer:\n", r2.get("answer"))

print("\n" + "="*70)
print("TEST 3: MELTED ICE CREAM COMPLAINT (CORNER HOUSE) - ZERO-MELT POLICY")
print("="*70)
sess_3 = []
r3 = run_turn(
    "My Death By Chocolate from Corner House arrived completely melted into warm soup! What is your policy?",
    "sess_corner_house",
    sess_3
)
print("Agent:", r3.get("agent_metadata", {}).get("specialized_agent"))
print("Bot Answer:\n", r3.get("answer"))

print("\n" + "="*70)
print("TEST 4: COLD FOOD COMPLAINT (DOMINO'S PIZZA)")
print("="*70)
sess_4 = []
r4 = run_turn(
    "My pizza order ORD-84512 from Napoli Woodfired Pizza arrived cold and lukewarm. I want a refund.",
    "sess_cold_pizza",
    sess_4
)
print("Agent:", r4.get("agent_metadata", {}).get("specialized_agent"))
print("Bot Answer:\n", r4.get("answer"))

print("\n" + "="*70)
print("TEST 5: DIETARY VIOLATION (NON-VEG DELIVERED ON VEG ORDER)")
print("="*70)
sess_5 = []
r5 = run_turn(
    "This is unacceptable! I am strictly pure vegetarian and ordered Paneer Biryani, but you delivered chicken meat in my box! I am furious!",
    "sess_dietary_violation",
    sess_5
)
print("Agent:", r5.get("agent_metadata", {}).get("specialized_agent"))
print("Bot Answer:\n", r5.get("answer"))

print("\n" + "="*70)
print("TEST 6: MISSING ITEM COMPLAINT (ITEM-LEVEL REFUND)")
print("="*70)
sess_6 = []
r6 = run_turn(
    "My order ORD-11253 was missing the Apollo Fish starter! It was not delivered.",
    "sess_missing_item",
    sess_6
)
print("Agent:", r6.get("agent_metadata", {}).get("specialized_agent"))
print("Bot Answer:\n", r6.get("answer"))
print("\n" + "="*70)
print("ALL TESTS COMPLETED!")
print("="*70)
