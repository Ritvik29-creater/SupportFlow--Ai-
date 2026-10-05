from config import LLM

def is_grounded(answer: str, context: str) -> bool:
    prompt = f"""
    You are checking for hallucinations.

    Context:
    {context}

    Answer:
    {answer}

    Question:
    Is every factual claim in the answer supported by the context?

    Reply in ONLY one word :
    YES or NO

    """


    verdict = LLM.invoke(prompt).content.strip().upper()
    
    return verdict == "YES"