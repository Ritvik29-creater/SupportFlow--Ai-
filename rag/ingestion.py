"""
Knowledge Base Ingestion Script for SupportFlow AI
Parses markdown documentation from data/docs and indexes into ChromaDB with HuggingFace embeddings.
"""
import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from config import CHROMA_DIR, DOCS_DIR


def ingest_docs():
    print(f"🚀 Starting ingestion from: {DOCS_DIR}")
    
    # 1. Collect all markdown files
    md_files = glob.glob(os.path.join(DOCS_DIR, "**", "*.md"), recursive=True)
    if not md_files:
        print("⚠️ No markdown files found in data/docs!")
        return

    print(f"📄 Found {len(md_files)} knowledge base documents:")
    for f in md_files:
        print(f"   - {os.path.relpath(f, DOCS_DIR)}")

    # 2. Setup Markdown Header Splitter & Recursive Splitter
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80
    )

    all_chunks = []
    for file_path in md_files:
        loader = TextLoader(file_path, encoding="utf-8")
        raw_docs = loader.load()
        for doc in raw_docs:
            md_splits = markdown_splitter.split_text(doc.page_content)
            for split in md_splits:
                # Retain source file path in metadata
                split.metadata["source"] = os.path.basename(file_path)
                category = os.path.basename(os.path.dirname(file_path))
                split.metadata["category"] = category
                sub_chunks = text_splitter.split_documents([split])
                all_chunks.extend(sub_chunks)

    print(f"✂️ Created {len(all_chunks)} chunked documents.")

    # 3. Setup embeddings model
    print("🧠 Initializing HuggingFace Embeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 4. Ingest into ChromaDB
    print(f"💾 Storing vectors in ChromaDB directory: {CHROMA_DIR}...")
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    print("✅ Ingestion complete! Knowledge base is ready for RAG.")


if __name__ == "__main__":
    ingest_docs()
