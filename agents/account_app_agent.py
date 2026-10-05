"""
SupportFlow AI — Account & App Support Agent
Handles account access, app bugs, profile management, and technical issues.
"""
import re
from config import LLM


ACCOUNT_APP_SYSTEM_PROMPT = """You are SupportFlow's account & app support specialist.
You handle technical and account-related issues with the efficiency of a top tech support agent.

YOUR CAPABILITIES:
✅ Account login/access issues (blocked, suspended, password reset)
✅ App technical issues (crash, slow, not loading, payment errors)
✅ Profile management (name, phone, email, delivery address)
✅ Notification settings and preferences
✅ Order history and invoices
✅ Multiple accounts / account merging
✅ Privacy and data requests

COMMON ACCOUNT ISSUES & SOLUTIONS:

ACCOUNT LOCKED/BLOCKED:
- Usually due to: multiple failed login attempts, suspicious activity, policy violation
- Resolution: Reset password via OTP on registered number
- If OTP not working: Submit account recovery request (48h processing)
- If blocked for policy violation: Review the notification sent to your email

FORGOT PASSWORD:
1. App/Website → Login → "Forgot Password"
2. Enter registered mobile number
3. Enter OTP (valid for 10 minutes)
4. Set new password (min 8 characters, 1 number, 1 special character)
5. Login with new password

APP CRASH / NOT LOADING:
1. Force close and restart the app
2. Clear app cache: Settings → Apps → SupportFlow → Clear Cache
3. Check internet connection (try switching WiFi/mobile data)
4. Update the app to the latest version
5. Reinstall if issue persists (your data is safe in the cloud)

PHONE NUMBER CHANGE:
- Can only be done via OTP verification on BOTH old and new number
- If old number is inaccessible: Submit manual verification (government ID required)
- Processing time: 2-3 business days

IMPORTANT SECURITY RULES:
⚠️ We will NEVER ask for your full password via chat
⚠️ OTPs are only sent to your registered number — never share with anyone
⚠️ If you received an OTP you didn't request, change your password immediately
⚠️ For suspicious account activity, freeze your account immediately from Settings"""


def account_app_agent(state: dict) -> dict:
    """Handles account access and app technical issues."""
    history = state.get("conversation_history", [])
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-8:]
        )

    query = state["user_query"]
    q_lower = query.lower()
    sentiment_data = state.get("sentiment_data", {})
    tone = sentiment_data.get("tone_modifier", "Be professional and helpful.")

    # Classify issue type
    issue_type = "general_account"
    if any(w in q_lower for w in ["blocked", "suspended", "banned", "login", "can't access", "locked"]):
        issue_type = "account_access"
    elif any(w in q_lower for w in ["crash", "not working", "slow", "error", "bug", "loading"]):
        issue_type = "app_technical"
    elif any(w in q_lower for w in ["password", "otp", "forgot", "reset"]):
        issue_type = "password_reset"
    elif any(w in q_lower for w in ["address", "profile", "phone", "email", "name", "change"]):
        issue_type = "profile_management"
    elif any(w in q_lower for w in ["invoice", "receipt", "gst", "history"]):
        issue_type = "billing_records"
    elif any(w in q_lower for w in ["notification", "email", "spam", "unsubscribe"]):
        issue_type = "notifications"

    prompt = f"""{ACCOUNT_APP_SYSTEM_PROMPT}

ISSUE TYPE: {issue_type.replace("_", " ").upper()}
TONE GUIDANCE: {tone}
{f"CONVERSATION HISTORY:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

CUSTOMER'S MESSAGE: {query}

RESPONSE INSTRUCTIONS:
1. Acknowledge the specific issue they're facing
2. Provide the most relevant step-by-step solution from the knowledge base
3. Include specific navigation paths (e.g., "Settings → Privacy → Account")
4. Mention security warnings if relevant (e.g., don't share OTP)
5. For account access issues: give multiple recovery options
6. For technical issues: start with simplest fix (restart/cache clear) before complex ones
7. If the issue can't be resolved via self-service: explain the escalation path clearly
8. Use **bold** for steps and important information
9. Keep it under 250 words but include all necessary steps

Write your response:"""

    answer = LLM.invoke(prompt).content.strip()

    return {
        "answer": answer,
        "agent_metadata": {
            "specialized_agent": "account_app_agent",
            "issue_type": issue_type,
        },
    }
