"""
RAG Retriever — ChromaDB with HuggingFace embeddings.
Loads and indexes food delivery support documentation.
Supports both similarity and MMR (max marginal relevance) retrieval.
"""
import os
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from config import CHROMA_DIR


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    return vectorstore


_vectorstore = load_vectorstore()

# Standard similarity retriever — top 5 most relevant chunks
retriever = _vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# MMR retriever — maximizes relevance + diversity (avoids repetitive chunks)
# fetch_k=15 candidates, pick best 6 with diversity penalty
mmr_retriever = _vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 6,           # Return 6 results
        "fetch_k": 15,    # Fetch 15 candidates first
        "lambda_mult": 0.7,  # 0.7 = balance between relevance and diversity
    },
)


def get_category_retriever(category: str):
    """Get a retriever filtered by document category."""
    return _vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5,
            "filter": {"category": category},
        },
    )
