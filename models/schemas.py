"""
API Request and Response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum

from .session import (
    Session, SessionStatus, CurrentPhase, LearningStyle,
    StudyPlan, ConceptPlan, SessionStats, StudentSnapshot,
    LearningPreferences
)
from .questions import QuestionUnion, QuestionType, AnswerEvaluation


# ============ Request Models ============

class CreateSessionRequest(BaseModel):
    """Request to create a new session"""
    student_id: str
    student_name: str
    class_grade: int = Field(ge=6, le=10)
    board: str = "CBSE"
    subject: str
    chapter: str
    topic: Optional[str] = None
    interests: List[str] = []
    learning_style: LearningStyle = LearningStyle.EXAMPLES
    pace: str = "medium"


class StartDiagnosticRequest(BaseModel):
    """Request to start diagnostic assessment"""
    session_id: str


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer"""
    session_id: str
    question_id: str
    question_type: QuestionType
    answer: Any  # str, float, bool, or list depending on type
    time_taken_seconds: Optional[int] = None


class SendMessageRequest(BaseModel):
    """Request for free-form chat message"""
    session_id: str
    message: str


class RequestHintRequest(BaseModel):
    """Request a hint for current question"""
    session_id: str
    question_id: str


class SkipConceptRequest(BaseModel):
    """Request to skip current concept"""
    session_id: str
    reason: Optional[str] = None


class EndSessionRequest(BaseModel):
    """Request to end session"""
    session_id: str


# ============ Response Models ============

class UIAction(str, Enum):
    """Actions frontend should take"""
    SHOW_QUESTION = "show_question"
    SHOW_MESSAGE = "show_message"
    SHOW_FEEDBACK = "show_feedback"
    SHOW_STUDY_PLAN = "show_study_plan"
    SHOW_PROGRESS = "show_progress"
    SHOW_CELEBRATION = "show_celebration"
    END_SESSION = "end_session"
    REQUEST_INPUT = "request_input"


class MessageResponse(BaseModel):
    """AI message to display"""
    type: str = "message"
    content: str
    is_encouragement: bool = False


class QuestionDisplay(BaseModel):
    """Question to display in UI"""
    type: str = "question"
    question: QuestionUnion
    context_message: Optional[str] = None  # AI message before question
    show_hint_button: bool = True
    time_limit_seconds: Optional[int] = None
    attempts_remaining: int = 3


class FeedbackDisplay(BaseModel):
    """Feedback after answer"""
    type: str = "feedback"
    is_correct: bool
    partial_credit: float = 0
    message: str
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    xp_earned: int = 0
    next_action: str  # next_question, retry, hint, next_concept, reteach


class StudyPlanDisplay(BaseModel):
    """Study plan for UI"""
    type: str = "study_plan"
    message: str
    total_concepts: int
    estimated_minutes: int
    concepts: List[Dict[str, Any]]


class ProgressDisplay(BaseModel):
    """Progress update for UI"""
    type: str = "progress"
    concepts_completed: int
    concepts_total: int
    current_concept: str
    accuracy: float
    xp_earned: int
    time_spent_minutes: int


class CelebrationDisplay(BaseModel):
    """Celebration/achievement UI"""
    type: str = "celebration"
    title: str
    message: str
    xp_earned: int
    badge_earned: Optional[str] = None
    streak_days: Optional[int] = None


class SessionSummary(BaseModel):
    """Session summary for wrap-up"""
    type: str = "session_summary"
    duration_minutes: int
    concepts_covered: int
    concepts_mastered: int
    accuracy: float
    xp_earned: int
    highlights: List[str]
    areas_to_practice: List[str]
    next_session_preview: str


# ============ Main API Response ============

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    session_id: str
    current_phase: CurrentPhase
    
    # What to display (can be multiple items)
    display: List[Any]  # List of MessageResponse, QuestionDisplay, etc.
    
    # Current progress (always included)
    progress: Optional[ProgressDisplay] = None
    
    # Session metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Error info if any
    error: Optional[str] = None


class SessionCreatedResponse(BaseModel):
    """Response after creating session"""
    success: bool = True
    session_id: str
    message: str
    student_name: str
    subject: str
    chapter: str


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
