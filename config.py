"""
SupportFlow AI — Central Configuration
Uses Groq GPT-OSS 120B (primary) + Qwen 27B (fast) for maximum intelligence.
Architecture: deterministic Python routing, LLM never controls flow.
"""
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")
HF_CACHE_DIR = os.path.join(BASE_DIR, ".hf_cache")

# Ensure HuggingFace models cache to the project directory
os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", HF_CACHE_DIR)
os.environ.setdefault("TRANSFORMERS_CACHE", HF_CACHE_DIR)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# Disable LangSmith unless explicitly configured
_langsmith_key = os.getenv("LANGCHAIN_API_KEY", "")
if _langsmith_key:
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "SupportFlowAI")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

# ─── LLM Configuration ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Auto-detect best available model for this API key
# Primary: openai/gpt-oss-120b (best reasoning available on this key)
# Fast: qwen/qwen3.8-27b (fast classification tasks)
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    raise ValueError(
        "\n\nGROQ_API_KEY is not set!\n"
        "   1. Get your FREE key at: https://console.groq.com\n"
        "   2. Add to .env file: GROQ_API_KEY=your_key_here\n"
        "   3. Restart the server\n"
    )

# Primary LLM — GPT-OSS 120B (best available on this API key, great for reasoning)
LLM = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.1,
    max_tokens=2048,
)

# Fast LLM — Qwen 3.8-27B (fast, capable for intent/sentiment classification)
LLM_FAST = ChatGroq(
    model=GROQ_MODEL_FAST,
    api_key=GROQ_API_KEY,
    temperature=0.0,
    max_tokens=512,
)

# ─── App Metadata ─────────────────────────────────────────────────────────────
APP_NAME = "SupportFlow AI"
APP_VERSION = "3.0"
