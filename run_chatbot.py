"""
SupportFlow AI — One-Command Startup Script
Run this file to start the chatbot server.

Usage:
    python run_chatbot.py

Then open: http://localhost:8000
"""
import os
import sys
import subprocess


def check_env():
    """Check that .env exists and has GROQ_API_KEY."""
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your_groq_api_key_here":
        print("\n" + "="*60)
        print("❌  GROQ_API_KEY not configured!")
        print("="*60)
        print("\n📋 Quick Setup (2 minutes):")
        print("  1. Go to https://console.groq.com and sign up (free)")
        print("  2. Create an API key")
        print("  3. Create a file named '.env' in this folder")
        print("  4. Add this line to the .env file:")
        print("       GROQ_API_KEY=your_actual_key_here")
        print("  5. Run this script again")
        print("\n" + "="*60)
        sys.exit(1)
    print(f"✅ GROQ_API_KEY found (model: {os.getenv('GROQ_MODEL', 'llama3-8b-8192')})")


def setup_rag():
    """Ingest docs into ChromaDB if not already done."""
    from config import CHROMA_DIR, DOCS_DIR
    
    # Check if ChromaDB already has data
    chroma_data = os.path.join(CHROMA_DIR, "chroma.sqlite3")
    if os.path.exists(chroma_data):
        print("✅ ChromaDB knowledge base already exists — skipping ingestion")
        return
    
    # Check that docs exist
    import glob
    docs = glob.glob(os.path.join(DOCS_DIR, "**", "*.md"), recursive=True)
    if not docs:
        print("⚠️  No documents found in data/docs/ — RAG will use fallback mode")
        return
    
    print(f"📚 Ingesting {len(docs)} policy documents into ChromaDB...")
    print("   (This only runs once and takes ~30 seconds)")
    from rag.ingestion import ingest_docs
    ingest_docs()


def setup_database():
    """Create SQLite database tables."""
    from database.connection import create_tables
    create_tables()
    print("✅ SQLite database initialized")


def start_server():
    """Start the FastAPI server."""
    import uvicorn
    print("\n" + "="*60)
    print("🚀 SupportFlow AI Chatbot is starting...")
    print("="*60)
    print("📍 Open in browser: http://localhost:8000")
    print("📖 API Docs:        http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="warning",  # Reduce noise; errors still shown
    )


if __name__ == "__main__":
    print("\n🤖 SupportFlow AI — Food Delivery Support Chatbot")
    print("─" * 50)
    
    # Step 1: Validate environment
    check_env()
    
    # Step 2: Setup database
    setup_database()
    
    # Step 3: Setup RAG knowledge base
    setup_rag()
    
    # Step 4: Start server
    start_server()
