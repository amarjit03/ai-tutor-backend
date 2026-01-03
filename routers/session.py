"""
Session Router - Endpoints for session management
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from models import (
    CreateSessionRequest,
    SessionCreatedResponse,
    ErrorResponse,
    Session,
    CurrentPhase
)
from services import session_manager

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/create", response_model=SessionCreatedResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new tutoring session
    
    This initializes a new session for a student with their preferences
    and the topic they want to study.
    """
    try:
        session = session_manager.create_session(
            student_id=request.student_id,
            student_name=request.student_name,
            class_grade=request.class_grade,
            board=request.board,
            subject=request.subject,
            chapter=request.chapter,
            topic=request.topic or request.chapter,
            interests=request.interests,
            learning_style=request.learning_style.value,
            pace=request.pace
        )
        
        return SessionCreatedResponse(
            success=True,
            session_id=session.session_id,
            message=f"Hi {request.student_name}! Ready to learn {request.subject}? Let's start with a quick warm-up to see what you already know!",
            student_name=request.student_name,
            subject=request.subject,
            chapter=request.chapter
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: str):
    """
    Get session details
    
    Returns the full session state including progress, current phase,
    and all session data.
    """
    session = session_manager.load_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session": {
            "session_id": session.session_id,
            "student_id": session.student_id,
            "student_name": session.student.name,
            "status": session.status.value,
            "current_phase": session.current_phase.value,
            "subject": session.meta.subject if session.meta else None,
            "chapter": session.meta.chapter if session.meta else None,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "stats": {
                "duration_minutes": session.stats.duration_minutes,
                "questions_attempted": session.stats.questions_attempted,
                "questions_correct": session.stats.questions_correct,
                "accuracy_rate": session.stats.accuracy_rate,
                "concepts_mastered": session.stats.concepts_mastered,
                "xp_earned": session.stats.xp_earned
            },
            "study_plan": {
                "total_concepts": session.study_plan.total_concepts,
                "current_concept_index": session.study_plan.current_concept_index,
                "concepts": [
                    {
                        "id": c.concept_id,
                        "name": c.name,
                        "status": c.status.value,
                        "mastery_score": c.mastery_score
                    }
                    for c in session.study_plan.concepts
                ]
            } if session.study_plan.concepts else None,
            "diagnostic": {
                "status": session.diagnostic.status.value,
                "questions_asked": len(session.diagnostic.questions),
                "assessment": {
                    "level": session.diagnostic.assessment.overall_level,
                    "score": session.diagnostic.assessment.score
                } if session.diagnostic.assessment else None
            }
        }
    }


@router.get("/{session_id}/progress")
async def get_progress(session_id: str):
    """
    Get session progress summary
    
    Returns a lightweight progress summary for UI updates.
    """
    session = session_manager.load_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    current_concept = "Getting started"
    if session.study_plan.concepts and session.study_plan.current_concept_index < len(session.study_plan.concepts):
        current_concept = session.study_plan.concepts[session.study_plan.current_concept_index].name
    
    return {
        "success": True,
        "progress": {
            "current_phase": session.current_phase.value,
            "concepts_completed": session.stats.concepts_mastered,
            "concepts_total": session.study_plan.total_concepts or 1,
            "current_concept": current_concept,
            "accuracy": session.stats.accuracy_rate,
            "xp_earned": session.stats.xp_earned,
            "questions_attempted": session.stats.questions_attempted,
            "questions_correct": session.stats.questions_correct
        }
    }


@router.get("/list/{student_id}")
async def list_sessions(student_id: str):
    """
    List all sessions for a student
    
    Returns a list of all sessions (active and completed) for a student.
    """
    sessions = session_manager.list_sessions(student_id)
    
    return {
        "success": True,
        "count": len(sessions),
        "sessions": sessions
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session
    
    Permanently removes a session and its data.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    
    return {
        "success": True,
        "message": "Session deleted successfully"
    }
