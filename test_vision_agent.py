import httpx
import base64
import sys

# Configure UTF-8 for console output on Windows
sys.stdout.reconfigure(encoding='utf-8')


# Test 1: Spilled Gravy
svg_spilled = '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
<rect width="300" height="200" fill="#1e1b4b"/>
<text x="20" y="40" fill="#f87171" font-size="14">Cracked box with spilled curry</text>
<path d="M50 100 Q150 180 250 140 Z" fill="#ea580c"/>
</svg>'''
b64_spilled = "data:image/svg+xml;base64," + base64.b64encode(svg_spilled.encode()).decode()

payload_spilled = {
    "content": "My order arrived completely damaged! The curry container is cracked and gravy has completely spilled over the bag. Please verify this photo proof and approve my full refund.",
    "image_base64": b64_spilled,
    "image_type": "image/svg+xml"
}

print("=== TEST 1: GENUINE DAMAGE (SPILLED GRAVY) ===")
try:
    r = httpx.post("http://localhost:8000/api/chat/", json=payload_spilled, timeout=35.0)
    print("HTTP Status:", r.status_code)
    data = r.json()
    print("Agent Used:", data.get("agent_used"))
    va = data.get("visual_assessment") or {}
    print("Decision:", va.get("decision"))
    print("Damage Type:", va.get("damage_type"))
    print("Damage Severity:", va.get("damage_severity"))
    print("Refund Amount:", va.get("calculated_refund"))
    print("Fraud Score:", va.get("fraud_score"))
    print("\nBot Response Preview:\n", data.get("answer")[:300])
except Exception as e:
    print("Error:", e)

# Test 2: Intact Food / Fraud Attempt
svg_intact = '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
<rect width="300" height="200" fill="#022c22"/>
<text x="20" y="40" fill="#4ade80" font-size="14">Pristine intact fresh meal untouched</text>
<circle cx="150" cy="110" r="50" fill="#f59e0b"/>
</svg>'''
b64_intact = "data:image/svg+xml;base64," + base64.b64encode(svg_intact.encode()).decode()

payload_intact = {
    "content": "I want a full refund for this meal claiming the food is completely ruined. Inspect my photo and refund.",
    "image_base64": b64_intact,
    "image_type": "image/svg+xml"
}

print("\n=== TEST 2: FRAUD ATTEMPT (INTACT FRESH MEAL) ===")
try:
    r2 = httpx.post("http://localhost:8000/api/chat/", json=payload_intact, timeout=35.0)
    print("HTTP Status:", r2.status_code)
    data2 = r2.json()
    print("Agent Used:", data2.get("agent_used"))
    va2 = data2.get("visual_assessment") or {}
    print("Decision:", va2.get("decision"))
    print("Damage Type:", va2.get("damage_type"))
    print("Fraud Score:", va2.get("fraud_score"))
    print("Refund Amount:", va2.get("calculated_refund"))
    print("\nBot Response Preview:\n", data2.get("answer")[:300])
except Exception as e:
    print("Error:", e)
