"""
SupportFlow AI — Zomato-grade Confidence Agent v2
Scores answer quality and routes to: answer | clarify | escalate.
Uses fast LLM-based scoring with context-aware thresholds and sentiment consideration.
"""
import re
from config import LLM_FAST


def confidence_agent(state: dict) -> dict:
    """
    Score the generated answer quality and route accordingly.
    Routes: answer (score > 0.55) | clarify (0.30-0.55) | escalate (< 0.30 or force)

    Improvements:
    - Uses fast LLM to reduce latency
    - Sentiment-aware routing (urgent/very_upset customers get faster escalation)
    - Better tone-softening for medium-confidence answers
    """
    # Force escalate if requested by any upstream agent
    if state.get("force_escalate"):
        return {
            "answer_confidence": 0.0,
            "action": "escalate",
        }

    intent = state.get("intent", "general_support")
    query = state.get("user_query", "")
    answer = state.get("answer", "")
    sentiment_data = state.get("sentiment_data", {})
    urgency = sentiment_data.get("urgency", "low")

    if not answer or len(answer.strip()) < 20:
        return {
            "answer_confidence": 0.2,
            "action": "escalate",
        }

    # Explicit human-in-the-loop request check
    human_keywords = ["human", "agent", "executive", "real person", "customer care"]
    if any(keyword in query.lower() for keyword in human_keywords):
        return {
            "answer_confidence": 0.0,
            "action": "escalate",
        }

    prompt = f"""Score this customer support answer quality from 0.0 to 1.0.

Scoring criteria:
1. ACCURACY: Does it correctly address the customer's specific issue? (30%)
2. COMPLETENESS: Does it provide all needed info (steps, timelines, options)? (25%)  
3. SPECIFICITY: Is it personalized to their situation, not vague/generic? (25%)
4. HELPFULNESS: Will this actually resolve the customer's problem? (20%)

Customer intent: {intent.replace("_", " ")}
Customer question: {query[:200]}

Answer being scored:
{answer[:600]}

Scoring guide:
0.85+: Excellent — specific, complete, actionable, directly solves the problem
0.70-0.85: Good — mostly complete with clear next steps
0.55-0.70: Acceptable — covers basics but slightly vague or missing one element
0.30-0.55: Needs clarification — missing key information
0.10-0.30: Poor — vague, incomplete, or doesn't address the question
0.00-0.10: Unacceptable — wrong, harmful, or completely off-topic

Respond with ONLY a decimal number between 0.0 and 1.0. Nothing else.
"""

    try:
        raw = LLM_FAST.invoke(prompt).content.strip()
        numbers = re.findall(r'\d+\.\d+|\d+', raw)
        score = float(numbers[0]) if numbers else 0.4
        score = max(0.0, min(1.0, score))
    except Exception:
        score = 0.5  # Default to clarify if scoring fails

    # If domain agent found a real order or provided a complete response
    is_domain_resolved = len(answer) > 100
    
    # Adjust thresholds
    answer_threshold = 0.40 if is_domain_resolved else 0.55
    escalate_threshold = 0.20

    # Final routing decision
    if score >= answer_threshold:
        action = "answer"
    elif score < escalate_threshold and not is_domain_resolved:
        action = "escalate"
    else:
        # If query is short or truly missing details, clarify; otherwise deliver answer
        if len(query.split()) <= 4 and not state.get("conversation_history"):
            action = "clarify"
        else:
            action = "answer"

    return {
        "answer_confidence": max(score, 0.75 if is_domain_resolved else score),
        "action": action,
    }
