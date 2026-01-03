"""
Chat Router - Endpoints for learning interactions
"""
from fastapi import APIRouter, HTTPException
from typing import Any

from models import (
    SubmitAnswerRequest,
    SendMessageRequest,
    RequestHintRequest,
    SkipConceptRequest,
    EndSessionRequest,
    APIResponse,
    CurrentPhase
)
from services import tutor, session_manager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/start-diagnostic", response_model=APIResponse)
async def start_diagnostic(session_id: str):
    """
    Start the diagnostic assessment
    
    Begins the initial assessment to understand student's current level.
    Returns the first diagnostic question.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.start_diagnostic(session_id)
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/submit-diagnostic-answer", response_model=APIResponse)
async def submit_diagnostic_answer(
    session_id: str,
    question_id: str,
    answer: str
):
    """
    Submit an answer during diagnostic assessment
    
    Evaluates the answer and returns feedback along with the next question
    or final assessment results.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.submit_diagnostic_answer(session_id, question_id, answer)
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/generate-plan", response_model=APIResponse)
async def generate_study_plan(session_id: str):
    """
    Generate personalized study plan
    
    Creates a study plan based on diagnostic results.
    Should be called after diagnostic is complete.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.generate_study_plan(session_id)
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/start-teaching", response_model=APIResponse)
async def start_teaching(session_id: str):
    """
    Start teaching the current concept
    
    Begins teaching the next concept in the study plan.
    Returns teaching content and practice question.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.start_teaching_concept(session_id)
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/submit-answer", response_model=APIResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer during teaching/practice
    
    Evaluates the answer and decides next steps:
    - Correct: Move to next question or concept
    - Wrong: Provide hint, allow retry, or reteach
    """
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.submit_practice_answer(
        request.session_id,
        request.question_id,
        request.answer
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/get-hint", response_model=APIResponse)
async def get_hint(request: RequestHintRequest):
    """
    Request a hint for current question
    
    Returns a helpful hint without giving away the answer.
    Tracks hint usage in session stats.
    """
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.get_hint(request.session_id, request.question_id)
    
    return response


@router.post("/skip-concept", response_model=APIResponse)
async def skip_concept(request: SkipConceptRequest):
    """
    Skip current concept
    
    Allows student to skip a concept they find too difficult.
    Marks concept for review and moves to next.
    """
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_manager.load_session(request.session_id)
    
    if session.study_plan.concepts:
        idx = session.study_plan.current_concept_index
        if idx < len(session.study_plan.concepts):
            from models import ConceptStatus
            session.study_plan.concepts[idx].status = ConceptStatus.SKIPPED
            session.study_plan.current_concept_index += 1
            session_manager.save_session(session)
    
    # Start next concept or wrap up
    response = await tutor.start_teaching_concept(request.session_id)
    
    return response


@router.post("/end-session", response_model=APIResponse)
async def end_session(request: EndSessionRequest):
    """
    End the current session
    
    Wraps up the session with a summary of progress and achievements.
    """
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await tutor.wrap_up_session(request.session_id)
    
    return response


@router.post("/message")
async def send_message(request: SendMessageRequest):
    """
    Send a free-form message
    
    For general chat interactions outside the structured flow.
    Can be used for questions, clarifications, etc.
    """
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_manager.load_session(request.session_id)
    
    # Add message to conversation
    session = session_manager.add_message(session, "user", request.message)
    session_manager.save_session(session)
    
    # For MVP, route to appropriate handler based on current phase
    if session.current_phase == CurrentPhase.DIAGNOSTIC:
        # Treat as diagnostic answer
        last_q = session.diagnostic.questions[-1] if session.diagnostic.questions else None
        if last_q:
            return await tutor.submit_diagnostic_answer(
                request.session_id,
                last_q.question_id,
                request.message
            )
    
    elif session.current_phase == CurrentPhase.TEACHING:
        # Treat as practice answer
        return await tutor.submit_practice_answer(
            request.session_id,
            "current",
            request.message
        )
    
    # Default response
    return APIResponse(
        success=True,
        session_id=request.session_id,
        current_phase=session.current_phase,
        display=[{
            "type": "message",
            "content": "I'm here to help! Let's continue with our learning session."
        }]
    )


# ============ Convenience Endpoints ============

@router.post("/next")
async def next_step(session_id: str):
    """
    Proceed to next step in the learning flow
    
    Automatically determines and executes the next action based on
    current session state. Useful for "Continue" button.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_manager.load_session(session_id)
    
    # Route based on current phase
    if session.current_phase == CurrentPhase.TOPIC_SELECTION:
        return await tutor.start_diagnostic(session_id)
    
    elif session.current_phase == CurrentPhase.DIAGNOSTIC:
        # Check if diagnostic is complete
        if session.diagnostic.status.value == "completed":
            return await tutor.generate_study_plan(session_id)
        else:
            # Continue diagnostic (shouldn't reach here normally)
            return await tutor.start_diagnostic(session_id)
    
    elif session.current_phase == CurrentPhase.PLAN_GENERATION:
        return await tutor.generate_study_plan(session_id)
    
    elif session.current_phase in [CurrentPhase.TEACHING, CurrentPhase.RETEACH, CurrentPhase.ASSESSMENT]:
        return await tutor.start_teaching_concept(session_id)
    
    elif session.current_phase == CurrentPhase.WRAPUP:
        return await tutor.wrap_up_session(session_id)
    
    else:
        return APIResponse(
            success=True,
            session_id=session_id,
            current_phase=session.current_phase,
            display=[{
                "type": "message",
                "content": "Let's continue learning!"
            }]
        )
