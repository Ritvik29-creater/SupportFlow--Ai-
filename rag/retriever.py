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


class FallbackRetriever:
    """Fallback in-memory keyword retriever if Chroma / PyArrow cannot be initialized."""
    def __init__(self, category_filter: str = None):
        self.category_filter = category_filter
        self.docs = []
        import glob
        from langchain_core.documents import Document

        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")
        if os.path.exists(base_dir):
            for filepath in glob.glob(os.path.join(base_dir, "**", "*.md"), recursive=True):
                cat = os.path.basename(os.path.dirname(filepath))
                if category_filter and cat.lower() != category_filter.lower():
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        sections = content.split("## ")
                        for idx, sec in enumerate(sections):
                            sec_text = ("## " + sec) if idx > 0 else sec
                            if sec_text.strip():
                                self.docs.append(Document(
                                    page_content=sec_text.strip(),
                                    metadata={"source": filepath, "category": cat}
                                ))
                except Exception:
                    pass

    def invoke(self, query: str):
        query_words = set(query.lower().split())
        scored = []
        for doc in self.docs:
            text = doc.page_content.lower()
            score = sum(1 for w in query_words if w in text and len(w) > 2)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored[:5]]
        if not results and self.docs:
            results = self.docs[:3]
        return results

    def as_retriever(self, **kwargs):
        return self


try:
    _vectorstore = load_vectorstore()
    retriever = _vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )
    mmr_retriever = _vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 15,
            "lambda_mult": 0.7,
        },
    )
    def get_category_retriever(category: str):
        return _vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "filter": {"category": category},
            },
        )
except Exception as _load_err:
    retriever = FallbackRetriever()
    mmr_retriever = FallbackRetriever()
    def get_category_retriever(category: str):
        return FallbackRetriever(category_filter=category)

