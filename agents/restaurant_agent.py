"""
SupportFlow AI — Zomato-grade Restaurant Agent
Handles food quality complaints, restaurant issues, hygiene concerns.
Files formal complaints and determines appropriate compensation.
"""
import re
from config import LLM


RESTAURANT_SYSTEM_PROMPT = """You are SupportFlow's restaurant quality & complaint specialist.
You handle restaurant-related issues with the seriousness they deserve — especially food safety.

YOUR CAPABILITIES:
✅ File formal food quality complaints against restaurants
✅ Handle hygiene/safety concerns (cockroach, mold, foreign objects)
✅ Process compensation for food quality issues
✅ Provide restaurant contact information
✅ Report restaurant violations to the platform team
✅ Handle wrong/missing items ordered from a specific restaurant

COMPLAINT SEVERITY LEVELS:

🔴 CRITICAL (immediate escalation + compensation):
- Foreign objects in food (cockroach, glass, hair, plastic)
- Severe hygiene violation
- Food caused illness (vomiting, stomach issues)
- Non-vegetarian item in confirmed vegetarian order
- Severely undercooked meat/chicken (food safety risk)
Actions: Immediate 100% refund + ₹100-200 compensation credit + restaurant flagged for investigation

🟠 SERIOUS (priority resolution):
- Completely stale or spoiled food
- Significantly wrong order (totally different items)
- Raw/undercooked food (non-safety-critical)
- Rude/threatening behavior from restaurant staff
Actions: Full refund + restaurant receives formal complaint + possible suspension review

🟡 MODERATE (standard resolution):
- Food arrived cold
- Wrong quantity/portion size  
- Missing sauces, sides, or add-ons
- Packaging damaged or open
- Food quality lower than expected (different from photo)
Actions: Partial refund (50-100% of affected item) or wallet credit

🟢 MINOR (goodwill gesture):
- Spice level wrong despite instructions
- Presentation different from menu photo
- Slightly late (within 30 min of ETA)
Actions: ₹30-₹50 wallet credit as goodwill

WHAT HAPPENS AFTER YOU FILE A COMPLAINT:
1. Restaurant receives formal notification from SupportFlow team
2. Restaurant has 24 hours to respond with their explanation
3. If 3+ complaints in 30 days → restaurant under quality review
4. If critical violation confirmed → temporary suspension
5. Customer receives confirmation and compensation within 2-4 hours

PHOTO EVIDENCE GUIDE:
- Required for: quality issues, wrong order, hygiene concerns
- Not required for: missing items, restaurant cancellation
- Tips: Take photo before eating, show full item and packaging
- Upload: Orders → Report Issue → Add Photo

RESTAURANT CONTACT:
- During active order: "Contact Restaurant" button in order tracking
- After delivery: Restaurant number in order details (24 hours post-delivery)
- For serious complaints: Route through support (we manage escalation)

IMPORTANT RULES:
- Take ALL hygiene/safety complaints very seriously
- For food illness cases, recommend customer see a doctor AND file complaint
- Never minimize a food safety concern
- For critical issues, escalate to human team immediately
- Always offer refund + compensation for quality failures"""


def classify_complaint_severity(query: str) -> str:
    """Classify the severity of a restaurant complaint."""
    q_lower = query.lower()

    critical_words = ["cockroach", "insect", "glass", "foreign object", "sick", "vomiting",
                      "food poisoning", "ill", "hospital", "non-veg in veg", "plastic", "mold",
                      "expired", "maggot", "worm"]
    serious_words = ["stale", "spoiled", "rotten", "raw chicken", "undercooked meat",
                     "rude", "threatened", "wrong order"]
    moderate_words = ["cold", "wrong", "missing", "packaging", "damaged", "quality"]

    if any(w in q_lower for w in critical_words):
        return "critical"
    elif any(w in q_lower for w in serious_words):
        return "serious"
    elif any(w in q_lower for w in moderate_words):
        return "moderate"
    return "minor"


def restaurant_agent(state: dict) -> dict:
    """Handles restaurant quality complaints — Zomato-grade seriousness."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-8:]
        )

    query = state["user_query"]
    severity = classify_complaint_severity(query)

    # Extract restaurant name
    restaurants = [
        "behrouz", "dominos", "domino", "kfc", "mcdonalds", "pizza hut", "subway",
        "burger king", "wow momo", "barbeque nation", "paradise biryani", "biryani by kilo",
        "bbk", "theobroma", "haldirams", "starbucks", "chaayos", "freshmenu", "licious",
        "swiggy", "zomato", "inner chef", "eatfit", "fasoos", "box8"
    ]
    restaurant_mentioned = None
    q_lower = query.lower()
    for r in restaurants:
        if r in q_lower:
            restaurant_mentioned = r.title()
            break

    severity_guidance = {
        "critical": (
            "This is a CRITICAL food safety issue. "
            "Immediately: 1) Express serious concern and apology 2) Confirm 100% refund + ₹100-200 compensation 3) "
            "Explain the restaurant will be investigated 4) If food illness mentioned, recommend doctor visit 5) "
            "Escalate to human team — this is too serious for AI-only handling. Create an urgent ticket."
        ),
        "serious": (
            "This is a SERIOUS quality complaint. "
            "1) Acknowledge the seriousness 2) Confirm full refund eligibility 3) "
            "Explain formal complaint process and what happens to restaurant 4) Offer compensation credit 5) "
            "Escalate to restaurant quality team."
        ),
        "moderate": (
            "This is a moderate quality complaint. "
            "1) Acknowledge the frustration 2) Confirm partial-to-full refund eligibility 3) "
            "Give step-by-step complaint process 4) Mention photo requirement 5) "
            "Offer wallet credit as fastest resolution."
        ),
        "minor": (
            "This is a minor quality issue. "
            "1) Apologize for the experience 2) Offer ₹30-50 goodwill wallet credit 3) "
            "Encourage them to rate the restaurant to help future customers 4) "
            "Assure that feedback reaches the restaurant."
        ),
    }

    force_escalate = severity in ["critical"]

    prompt = f"""{RESTAURANT_SYSTEM_PROMPT}

COMPLAINT SEVERITY: {severity.upper()}
{f"RESTAURANT MENTIONED: {restaurant_mentioned}" if restaurant_mentioned else ""}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S COMPLAINT: {query}

RESPONSE GUIDANCE: {severity_guidance[severity]}

RESPONSE RULES:
1. Match the severity — critical complaints need immediate seriousness, not routine replies
2. Always start with genuine empathy and acknowledgment of the specific issue
3. State what compensation/refund they're eligible for
4. Explain the step-by-step complaint filing process
5. For CRITICAL/SERIOUS issues, clearly state the restaurant will face consequences
6. For food illness: recommend visiting a doctor AND filing the complaint
7. Always ask for photo evidence if not mentioned (except critical safety cases where you escalate immediately)
8. Use **bold** for compensation amounts, timelines, and action steps
9. Close with the escalation offer

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "force_escalate": force_escalate,  # Critical issues always escalate to human
        "agent_metadata": {
            "specialized_agent": "restaurant_agent",
            "complaint_severity": severity,
            "restaurant": restaurant_mentioned,
        },
    }
