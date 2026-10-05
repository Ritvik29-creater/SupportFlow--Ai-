"""
SupportFlow AI — FastAPI Application
Main entry point for the REST API backend and Web Dashboard.
Chat endpoint does NOT require authentication — customers can chat directly.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from database.connection import create_tables
from api.routers import auth, orders, payments, refunds, restaurants, support, chat

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    try:
        create_tables()
        print("Database tables created/verified (SQLite)")
    except Exception as e:
        print(f"Database setup warning: {e}")
    print("SupportFlow AI is ready — open http://localhost:8000")
    yield
    print("SupportFlow AI shutting down")


app = FastAPI(
    title="SupportFlow AI",
    description="Agentic Food Delivery Customer Support Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all REST API routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(refunds.router)
app.include_router(restaurants.router)
app.include_router(support.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "SupportFlow AI"}


# Serve static web frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=False)
