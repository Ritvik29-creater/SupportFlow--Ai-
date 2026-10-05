"""
SupportFlow AI — Delivery Partner Complaint Agent
Handles complaints about rude delivery partners, wrong deliveries, safety issues.
These are taken extremely seriously — delivery partner behavior affects platform trust.
"""
import re
from config import LLM


DELIVERY_PARTNER_SYSTEM_PROMPT = """You are SupportFlow's delivery partner complaint specialist.
Delivery partner behavior issues are taken VERY seriously — they affect customer safety and platform trust.

YOUR CAPABILITIES:
✅ Handle reports of rude/abusive/threatening delivery partners
✅ Address wrong delivery (delivered to wrong person/location)
✅ Resolve delivery partner not responding or offline
✅ Handle delivery partner harassment or safety concerns
✅ Process delivery partner feedback (positive or negative)
✅ Assist with delivery partner contact during active order

SEVERITY CLASSIFICATION:
🔴 CRITICAL (immediate escalation):
- Physical threat or aggression from delivery partner
- Sexual harassment or inappropriate behavior
- Delivery partner under influence of alcohol/drugs
- Partner demanded extra payment/bribe
- Delivery partner took food and became unresponsive

🟠 SERIOUS (priority escalation):
- Delivery partner was extremely rude or verbally abusive
- Partner refused to deliver to doorstep (despite accessibility)
- Partner delivered to wrong address after being corrected

🟡 MODERATE (standard handling):
- Partner not responding on calls/chat
- Partner's location on map not updating
- Partner delivered to wrong person accidentally
- Difficulty communicating with partner

WHAT WE DO AFTER COMPLAINT:
1. Delivery partner account is flagged immediately
2. Our safety team reviews the case within 2 hours
3. Serious violations result in temporary suspension pending investigation
4. Critical violations result in immediate account deactivation
5. Police assistance coordinated if physical safety is at risk

IMPORTANT RULES:
- For physical threats/safety concerns: Offer to call emergency services guidance
- NEVER minimize a safety complaint — take it with full seriousness
- Always get the partner's name/ID (visible in the order screen) if possible
- Reassure the customer that this WILL be investigated
- For safety-critical situations, immediately escalate to human agent"""


def classify_dp_severity(query: str) -> str:
    """Classify severity of delivery partner complaint."""
    q_lower = query.lower()

    critical_words = [
        "threaten", "threatened", "hit", "push", "assault", "abuse",
        "harass", "sexual", "drunk", "drugs", "bribe", "extra money",
        "demanded", "stole", "took food", "not delivered", "ran away"
    ]
    serious_words = [
        "rude", "abusive", "yelled", "shouted", "argument", "fight",
        "refused", "wrong address", "wrong person", "not picking up"
    ]
    if any(w in q_lower for w in critical_words):
        return "critical"
    elif any(w in q_lower for w in serious_words):
        return "serious"
    return "moderate"


def delivery_partner_agent(state: dict) -> dict:
    """Handles delivery partner complaints and issues."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-8:]
        )

    query = state["user_query"]
    severity = classify_dp_severity(query)
    sentiment_data = state.get("sentiment_data", {})
    tone = sentiment_data.get("tone_modifier", "Be professional and empathetic.")

    severity_guidance = {
        "critical": (
            "🔴 CRITICAL safety complaint. "
            "1) Immediately express serious concern for their safety. "
            "2) Ask if they are currently safe. "
            "3) Confirm the delivery partner account will be immediately flagged and suspended. "
            "4) Tell them to document everything (screenshots, call logs). "
            "5) For physical threats: advise contacting local police if needed. "
            "6) Create urgent escalation ticket — human review within 30 minutes. "
            "7) Do NOT ask them to try resolving with the partner again."
        ),
        "serious": (
            "🟠 Serious misconduct complaint. "
            "1) Acknowledge the unacceptable behavior. "
            "2) Confirm formal complaint is being filed against the partner. "
            "3) Explain they will face disciplinary action. "
            "4) Process refund if applicable. "
            "5) Escalate to safety team for review within 2 hours."
        ),
        "moderate": (
            "🟡 Moderate delivery issue. "
            "1) Acknowledge the inconvenience. "
            "2) Give step-by-step guidance for the specific issue. "
            "3) Explain how to contact the partner during active order. "
            "4) Offer compensation if order was affected. "
            "5) Log the complaint for partner performance review."
        ),
    }

    force_escalate = severity == "critical"

    prompt = f"""{DELIVERY_PARTNER_SYSTEM_PROMPT}

COMPLAINT SEVERITY: {severity.upper()}
TONE GUIDANCE: {tone}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S COMPLAINT: {query}

RESPONSE GUIDANCE: {severity_guidance[severity]}

RESPONSE RULES:
1. Match the severity — critical complaints require immediate serious response
2. ALWAYS start with genuine empathy for what the customer experienced
3. Clearly state what action will be taken against the delivery partner
4. For safety concerns: customer safety is #1 priority
5. If refund is applicable (food not delivered, wrong delivery), state so clearly
6. Use **bold** for key actions, timelines, and important information
7. For serious/critical: clearly state this is being escalated to a human team
8. End with your ticket number or escalation confirmation
9. Keep under 250 words but be complete

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "force_escalate": force_escalate,
        "agent_metadata": {
            "specialized_agent": "delivery_partner_agent",
            "complaint_severity": severity,
        },
    }
