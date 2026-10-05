"""
Test realistic, Zomato-grade refund policies:
1. Cold food -> NO photo required, 25% courtesy refund or ₹75 voucher, reheating tips.
2. Confirm cold food refund -> Credits 25% to wallet.
3. Missing item -> NO photo required, item-level refund.
4. Spilled food -> Photo required for 100% full refund.
"""
import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Case 1: Cold Food (No Photo Needed, 25% Courtesy)
print("=== TEST 1: COLD FOOD COMPLAINT ===")
payload1 = {
    "content": "My delivered food for order ORD-33205 arrived cold and lukewarm. I want a refund.",
    "session_id": "test_cold_sess_1"
}
r1 = httpx.post("http://localhost:8000/api/chat/", json=payload1, timeout=30.0)
print("Status:", r1.status_code)
d1 = r1.json()
print("Agent Used:", d1.get("agent_used"))
print("\nBot Response:\n", d1.get("answer"))

# Case 2: Confirming 25% Credit
print("\n=== TEST 2: CUSTOMER ACCEPTS 25% WALLET CREDIT ===")
payload2 = {
    "content": "Yes, please confirm and process the 25% courtesy refund to my wallet.",
    "session_id": "test_cold_sess_1"
}
r2 = httpx.post("http://localhost:8000/api/chat/", json=payload2, timeout=30.0)
print("Status:", r2.status_code)
d2 = r2.json()
print("Agent Used:", d2.get("agent_used"))
print("\nBot Response:\n", d2.get("answer"))

# Case 3: Missing Item (No Photo Needed)
print("\n=== TEST 3: MISSING ITEM COMPLAINT ===")
payload3 = {
    "content": "My order ORD-33205 was missing the chutney and dip! What should I do?",
    "session_id": "test_missing_sess"
}
r3 = httpx.post("http://localhost:8000/api/chat/", json=payload3, timeout=30.0)
print("Status:", r3.status_code)
d3 = r3.json()
print("Agent Used:", d3.get("agent_used"))
print("\nBot Response:\n", d3.get("answer"))
