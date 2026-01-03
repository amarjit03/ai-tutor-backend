"""
AI Tutor Backend - Main Application

A FastAPI-based backend for an adaptive AI tutoring system
for Indian school students (Class 6-10).
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from config import settings
from routers import session_router, chat_router


# ============ Application Lifespan ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("🚀 Starting AI Tutor Backend...")
    
    # Ensure data directories exist
    os.makedirs(settings.SESSIONS_DIR, exist_ok=True)
    os.makedirs(settings.CURRICULUM_DIR, exist_ok=True)
    
    # Check Groq API key
    if not settings.GROQ_API_KEY:
        print("⚠️  WARNING: GROQ_API_KEY not set! Set it in .env file or environment.")
    else:
        print("✅ Groq API key configured")
    
    print(f"📁 Sessions directory: {settings.SESSIONS_DIR}")
    print(f"🤖 LLM Model: {settings.LLM_MODEL}")
    print("✅ AI Tutor Backend ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down AI Tutor Backend...")


# ============ Create Application ============

app = FastAPI(
    title="AI Tutor Backend",
    description="""
    An adaptive AI tutoring system for Indian school students (Class 6-10).
    
    ## Features
    - 📊 Diagnostic Assessment - Understand student's current level
    - 📚 Personalized Study Plans - Based on student's needs
    - 🎓 Adaptive Teaching - Multiple teaching approaches
    - ❓ Interactive Questions - MCQ, True/False, Numeric, and more
    - 🎮 Gamification - XP, streaks, and achievements
    
    ## Flow
    1. Create a session
    2. Complete diagnostic assessment
    3. Get personalized study plan
    4. Learn concepts with practice questions
    5. Session wrap-up with summary
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ============ CORS Middleware ============

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Include Routers ============

app.include_router(session_router)
app.include_router(chat_router)


# ============ Root Endpoints ============

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Tutor Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "model": settings.LLM_MODEL
    }


# ============ Error Handlers ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )


# ============ Run Application ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
