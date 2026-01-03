"""
Configuration settings for AI Tutor Backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GROQ_API_KEY: str = ""
    
    # LLM Settings
    LLM_MODEL: str = "llama-3.3-70b-versatile"  # Groq's fast model
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    
    # Application Settings
    APP_NAME: str = "AI Tutor Backend"
    DEBUG: bool = True
    
    # Data Paths
    SESSIONS_DIR: str = "data/sessions"
    CURRICULUM_DIR: str = "data/curriculum"
    
    # Session Settings
    MAX_DIAGNOSTIC_QUESTIONS: int = 6
    MASTERY_THRESHOLD: float = 0.7  # 70% to pass
    MAX_CONCEPT_ATTEMPTS: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
