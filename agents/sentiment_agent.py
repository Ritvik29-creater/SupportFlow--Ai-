"""
SupportFlow AI — Sentiment & Emotion Detection Agent
Analyzes customer emotional state to calibrate response tone.
Detects urgency, frustration, distress, and satisfaction levels.
"""
from config import LLM_FAST
import re
import json


SENTIMENT_KEYWORDS = {
    "very_upset": [
        "disgusting", "horrible", "terrible", "worst", "pathetic", "cheated", "fraud",
        "scam", "ridiculous", "unacceptable", "outraged", "furious", "livid",
        "cockroach", "food poisoning", "hospital", "sick", "vomiting", "sued",
        "consumer court", "legal action", "complain to media", "social media"
    ],
    "frustrated": [
        "frustrated", "annoyed", "angry", "upset", "disappointed", "irritated",
        "ridiculous", "seriously", "again", "every time", "always", "never",
        "waited", "still waiting", "no update", "no response", "ignored"
    ],
    "urgent": [
        "urgent", "immediately", "right now", "asap", "emergency", "hungry",
        "baby", "diabetic", "medicine", "hospital", "elderly", "sick",
        "need it now", "can't wait", "please hurry"
    ],
    "sad_disappointed": [
        "sad", "let down", "ruined", "spoiled occasion", "birthday", "anniversary",
        "special occasion", "kids waiting", "family waiting", "hungry kids",
        "celebration ruined"
    ],
    "neutral": [],
    "positive": [
        "thanks", "thank you", "great", "good", "appreciate", "helpful",
        "resolved", "sorted", "perfect", "excellent"
    ]
}


def detect_sentiment(query: str, history: list = None) -> dict:
    """
    Fast rule-based sentiment detection with LLM fallback.
    Returns: {sentiment, urgency, needs_extra_empathy, tone_modifier}
    """
    q_lower = query.lower()
    full_text = q_lower

    # Check history for escalating frustration
    if history:
        prev_queries = " ".join(
            m["content"].lower() for m in history[-4:] if m["role"] == "user"
        )
        full_text = prev_queries + " " + q_lower

    # Rule-based detection (fast path)
    if any(w in full_text for w in SENTIMENT_KEYWORDS["very_upset"]):
        sentiment = "very_upset"
        urgency = "high"
        needs_extra_empathy = True
    elif any(w in full_text for w in SENTIMENT_KEYWORDS["urgent"]):
        sentiment = "frustrated"
        urgency = "high"
        needs_extra_empathy = True
    elif any(w in full_text for w in SENTIMENT_KEYWORDS["frustrated"]):
        # Check for repeated complaints (multi-turn frustration)
        sentiment = "frustrated"
        urgency = "medium"
        needs_extra_empathy = True
    elif any(w in full_text for w in SENTIMENT_KEYWORDS["sad_disappointed"]):
        sentiment = "sad_disappointed"
        urgency = "medium"
        needs_extra_empathy = True
    elif any(w in full_text for w in SENTIMENT_KEYWORDS["positive"]):
        sentiment = "positive"
        urgency = "low"
        needs_extra_empathy = False
    else:
        sentiment = "neutral"
        urgency = "low"
        needs_extra_empathy = False

    # Multi-turn frustration escalation — if customer has sent 3+ messages
    if history and len([m for m in history if m["role"] == "user"]) >= 3:
        if sentiment in ["neutral", "frustrated"]:
            urgency = "medium"
            needs_extra_empathy = True

    # Tone modifier for LLM prompt injection
    tone_map = {
        "very_upset": (
            "The customer is VERY upset or distressed. Lead with a strong, genuine apology. "
            "Acknowledge their specific pain point. Be extra warm and reassuring. "
            "Do NOT use generic phrases like 'I understand your concern' — be specific and human."
        ),
        "frustrated": (
            "The customer is frustrated. Show empathy first, then solution. "
            "Avoid corporate-speak. Be direct and action-oriented."
        ),
        "urgent": (
            "The customer has an urgent situation. Prioritize speed of resolution. "
            "Lead with immediate action steps. Mention fastest possible resolution path."
        ),
        "sad_disappointed": (
            "The customer is sad or disappointed, possibly about a ruined occasion. "
            "Be extra gentle and compassionate. Acknowledge the emotional impact, not just the practical issue."
        ),
        "neutral": "The customer is neutral/calm. Be friendly, professional, and helpful.",
        "positive": "The customer seems positive. Be warm, efficient, and match their energy.",
    }

    return {
        "sentiment": sentiment,
        "urgency": urgency,
        "needs_extra_empathy": needs_extra_empathy,
        "tone_modifier": tone_map.get(sentiment, tone_map["neutral"]),
    }


def sentiment_agent(state: dict) -> dict:
    """Detect customer sentiment and inject tone guidance into state."""
    query = state.get("user_query", "")
    history = state.get("conversation_history", [])
    result = detect_sentiment(query, history)
    return {"sentiment_data": result}
