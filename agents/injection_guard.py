INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore previous commands",
    "system prompt",
    "you are allowed to",
    "developer message",
    "bypass",
    "override rules"
]

def is_prompt_injection(query: str) -> bool:
    q = query.lower()
    return any(p in q for p in INJECTION_PATTERNS)

def sanitize_context(text: str) -> str:
    banned = ["ignore", "override", "system:", "assistant:"]
    for b in banned:
        text = text.replace(b, "")
    return text
