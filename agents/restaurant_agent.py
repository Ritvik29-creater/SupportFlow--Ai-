"""
SupportFlow AI — Zomato-grade Restaurant & Culinary Agent v3
Handles:
1. Post-delivery food complaints (cold food, missing items, hygiene, spoiled food) with live SQLite order grounding.
2. Restaurant inquiries, menus, and recommendations across all 90+ restaurants in SQLite.
3. Authentic culinary recipes, ingredients, flavor profiles, and cooking processes.
"""
import re
from typing import Dict, Any, Optional
from config import LLM
from database.order_service import find_order_by_id, get_recent_orders
from database.restaurant_service import (
    search_restaurants_and_dishes,
    get_restaurant_catalog_summary,
    find_recipe_knowledge,
)


RESTAURANT_SYSTEM_PROMPT = """You are SupportFlow's restaurant specialist and master culinary expert — like Zomato's top customer advocate and head culinary curator combined.

YOUR CORE EXPERTISE:
1. 🛡️ Food Quality & Post-Delivery Complaints:
   - Cold food, delayed delivery complaints
   - Missing or incorrect items
   - Spilled packaging, damaged seals
   - Food hygiene violations, foreign objects, safety issues
   - Determining exact refunds (100% instant wallet credit vs 5-7 days bank refund) and compensation vouchers

2. 🍽️ Restaurant & Menu Intelligence (90+ Partner Restaurants):
   - Finding restaurants by cuisine, location, rating, price for two
   - Recommending signature dishes and best-sellers
   - Dietary suitability: Vegetarian (🟢), Non-Vegetarian (🔴), Vegan, Halal, Jain, High-protein

3. 👨‍🍳 Culinary Recipes & Food Knowledge:
   - Detailed authentic recipes and preparation processes (Dum Biryani, Neapolitan Pizza, Butter Chicken, Dal Makhani, Smashed Truffle Burgers, Mysore Masala Dosa, Tiramisu, etc.)
   - Key spices, marination secrets, cooking techniques (Dum, Tandoor, Dhungar smoke, Cold-ferment)
   - Ingredients, allergen alerts, and calorie/protein guidance

COMPLAINT COMPENSATION POLICY:
- 🔴 Food Safety / Foreign Object: Immediate 100% refund of order + ₹200 safety credit + restaurant flagged + Human Lead ticket
- 🟠 Stale / Spoiled / Wrong Items: 100% refund of affected items + ₹50-₹100 goodwill voucher
- 🟡 Arrived Cold / Spilled Packaging: 100% refund to SupportFlow Wallet (instant) or original payment (5-7 business days)
- 🟢 Missing Add-on / Sauce: Instant refund of missing items + ₹30 wallet credit

RESPONSE GUIDELINES:
- When an order ID or delivered order is mentioned, ground your answer directly in the real database order details.
- For complaints, show genuine empathy, state the exact eligible refund amount, and give clear resolution options.
- For recipes and food questions, provide mouth-watering, authentic, step-by-step culinary details.
- Use **bold** for restaurant names, dish names, refund amounts, and timelines.
"""


def classify_complaint_severity(query: str) -> str:
    """Classify the severity of a restaurant complaint."""
    q_lower = query.lower()

    critical_words = [
        "cockroach", "insect", "glass", "foreign object", "sick", "vomiting",
        "food poisoning", "ill", "hospital", "non-veg in veg", "plastic", "mold",
        "expired", "maggot", "worm"
    ]
    serious_words = [
        "stale", "spoiled", "rotten", "raw chicken", "undercooked meat",
        "rude", "threatened", "wrong order"
    ]
    moderate_words = [
        "cold", "wrong", "missing", "packaging", "damaged", "quality", "spilled",
        "leak", "soggy", "late", "complaint"
    ]

    if any(w in q_lower for w in critical_words):
        return "critical"
    elif any(w in q_lower for w in serious_words):
        return "serious"
    elif any(w in q_lower for w in moderate_words):
        return "moderate"
    return "minor"


def is_recipe_or_recommendation_query(query: str) -> bool:
    """Detect if query is about recipes, ingredients, recommendations, or menus."""
    q_lower = query.lower()
    recipe_terms = [
        "recipe", "how to make", "how is it made", "ingredients", "cook", "prepare",
        "preparation", "what is inside", "flavor", "spices", "recommend", "best",
        "suggest", "menu", "dishes", "what should i eat", "top rated", "places to eat"
    ]
    return any(term in q_lower for term in recipe_terms)


def restaurant_agent(state: dict) -> dict:
    """
    Handles:
    - Post-delivery food complaints with real SQLite order details.
    - Restaurant menus & recommendations across 90+ places.
    - Authentic culinary recipes & ingredients.
    """
    query = state["user_query"]
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
        )

    # 1. Check for Order ID in query or recent conversation
    order_id = None
    match = re.search(r"ORD-[\w\d]+", query, re.IGNORECASE)
    if match:
        order_id = match.group(0).upper()
    else:
        # Check conversation history for order ID
        for m in reversed(history):
            h_match = re.search(r"ORD-[\w\d]+", m.get("content", ""), re.IGNORECASE)
            if h_match:
                order_id = h_match.group(0).upper()
                break

    # Look up order in SQLite
    order_data = None
    if order_id:
        order_data = find_order_by_id(order_id)
    if not order_data:
        recent = get_recent_orders(limit=1)
        if recent and any(w in query.lower() for w in ["order", "delivered", "cold", "food", "refund", "complaint"]):
            order_data = find_order_by_id(recent[0]["order_id"])

    # 2. Check for Recipe / Culinary inquiry
    recipe_info = find_recipe_knowledge(query)

    # 3. Check for Restaurant / Dish search in SQLite
    rest_matches = search_restaurants_and_dishes(query, limit=5)
    catalog_summary = get_restaurant_catalog_summary(limit=6) if is_recipe_or_recommendation_query(query) else []

    # 4. Check complaint severity
    severity = classify_complaint_severity(query)
    force_escalate = severity == "critical"

    # Context assembly
    context_sections = []

    if order_data:
        items_str = ", ".join(f"{it['qty']}x {it['name']} ({it['price']})" for it in order_data.get("items", []))
        context_sections.append(
            f"REAL DATABASE ORDER RECORD:\n"
            f"- Order ID: {order_data['order_id']}\n"
            f"- Current Status: {order_data['status']}\n"
            f"- Restaurant: {order_data['restaurant_name']} ({order_data.get('cuisine', '')})\n"
            f"- Total Paid: {order_data['total_amount']}\n"
            f"- Items: {items_str}\n"
            f"- Delivery Address: {order_data.get('delivery_address', 'Bengaluru')}\n"
            f"- Delivered At: {order_data.get('delivered_at', 'Recently')}\n"
            f"- Driver: {order_data.get('driver_name', 'Delivery Partner')}\n"
            f"- Existing Refunds: {order_data.get('refund_count', 0)}"
        )

    if recipe_info:
        context_sections.append(
            f"CULINARY RECIPE KNOWLEDGE BASE:\n"
            f"Dish: {recipe_info['name']} ({recipe_info['origin']})\n"
            f"Key Ingredients: {', '.join(recipe_info['key_ingredients'])}\n"
            f"Authentic Process:\n{recipe_info['cooking_process']}\n"
            f"Flavor Profile: {recipe_info['flavor_profile']}\n"
            f"Dietary Info: {recipe_info['dietary']}"
        )

    if rest_matches:
        matches_text = []
        for r in rest_matches[:4]:
            if r["type"] == "restaurant":
                dish_names = ", ".join(d["name"] + " (" + d["price"] + ")" for d in r.get("dishes", [])[:3])
                matches_text.append(f"• {r['name']} ({r['cuisine']}, ⭐ {r['rating']}, {r['address']}) — Signature: {dish_names}")
            else:
                matches_text.append(f"• Dish '{r['matched_dish']}' ({r['dish_price']}) at {r['restaurant_name']} (⭐ {r['rating']}, {r['address']})")
        context_sections.append("MATCHING RESTAURANTS & DISHES FROM SQLITE:\n" + "\n".join(matches_text))

    elif catalog_summary:
        cat_text = [
            f"• {c['name']} (⭐ {c['rating']}, {c['cuisine']}, {c['location']}) — Best-sellers: {', '.join(c['signature_dishes'])}"
            for c in catalog_summary[:4]
        ]
        context_sections.append("TOP PARTNER RESTAURANTS IN BENGALURU:\n" + "\n".join(cat_text))

    grounding_context = "\n\n".join(context_sections)

    prompt = f"""{RESTAURANT_SYSTEM_PROMPT}

{f"DATABASE & CULINARY CONTEXT:{chr(10)}{grounding_context}{chr(10)}" if grounding_context else ""}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}
CUSTOMER QUERY: {query}
COMPLAINT SEVERITY: {severity.upper()}

SPECIFIC INSTRUCTIONS FOR THIS TURN:
- If this is a post-delivery complaint for a real order ({order_data['order_id'] if order_data else 'provided in context'}):
  1. Acknowledge the delivered order specifically (Restaurant: {order_data['restaurant_name'] if order_data else ''}, Amount: {order_data['total_amount'] if order_data else ''}).
  2. Apologize with genuine warmth for the issue (cold food / missing item / spoiled).
  3. Offer a full or itemized refund: choice of **instant credit to SupportFlow Wallet** (immediate) or **refund to original payment** (5-7 business days).
  4. Offer an extra **₹50-₹100 goodwill compensation voucher** for their next order.
  5. Mention that a quality report has been logged against the restaurant.
  6. If CRITICAL (foreign object/food poisoning): immediately confirm 100% refund + ₹200 safety credit and escalate to our Human Escalation Lead!

- If this is a recipe or food preparation question:
  1. Share the rich authentic culinary recipe, key spices/ingredients, and step-by-step cooking method.
  2. Explain flavor profile and dietary notes (veg/non-veg/protein).
  3. Highlight which top partner restaurants on SupportFlow prepare this dish authentically!

- If this is a restaurant recommendation or menu question:
  1. Give specific, top-rated restaurant recommendations from the database with ratings, locations, and prices.
  2. Suggest signature dishes they should try.

Write your response directly to the customer:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "force_escalate": force_escalate,
        "agent_metadata": {
            "specialized_agent": "restaurant_agent",
            "complaint_severity": severity,
            "order_id": order_data["order_id"] if order_data else None,
            "recipe_matched": recipe_info["name"] if recipe_info else None,
        },
    }
