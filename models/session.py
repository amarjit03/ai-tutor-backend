"""
Session models for tracking student learning progress
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PhaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ConceptStatus(str, Enum):
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    MASTERED = "mastered"
    NEEDS_REVIEW = "needs_review"
    SKIPPED = "skipped"


class LearningStyle(str, Enum):
    VISUAL = "visual"
    EXAMPLES = "examples"
    STEP_BY_STEP = "step_by_step"
    ANALOGY = "analogy"
    FORMAL = "formal"


class StudentMood(str, Enum):
    ENGAGED = "engaged"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    BORED = "bored"
    EXCITED = "excited"


# ============ Student Profile Models ============

class LearningPreferences(BaseModel):
    """Student's learning preferences"""
    learning_style: LearningStyle = LearningStyle.EXAMPLES
    pace: str = "medium"  # slow, medium, fast
    encouragement_level: str = "high"  # low, medium, high
    preferred_language: str = "English"


class StudentSnapshot(BaseModel):
    """Lightweight student info for session context"""
    student_id: str
    name: str
    class_grade: int  # 6-10
    board: str = "CBSE"
    preferences: LearningPreferences
    interests: List[str] = []
    known_weaknesses: List[str] = []


# ============ Diagnostic Models ============

class DiagnosticQuestion(BaseModel):
    """Record of a diagnostic question"""
    question_id: str
    question_text: str
    question_type: str
    difficulty: str
    concept_tested: str
    student_answer: Optional[str] = None
    correct_answer: str
    is_correct: Optional[bool] = None
    time_taken_seconds: Optional[int] = None
    hints_used: int = 0
    mistake_analysis: Optional[str] = None


class Misconception(BaseModel):
    """Identified student misconception"""
    id: str
    description: str
    severity: str  # low, medium, high
    related_concept: str


class DiagnosticAssessment(BaseModel):
    """Result of diagnostic phase"""
    overall_level: str  # beginner, intermediate, advanced
    score: float
    concepts_known: List[str]
    concepts_weak: List[str]
    misconceptions: List[Misconception]
    recommended_start_concept: str
    personalized_note: str


class DiagnosticPhase(BaseModel):
    """Complete diagnostic phase data"""
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    questions: List[DiagnosticQuestion] = []
    current_question_index: int = 0
    assessment: Optional[DiagnosticAssessment] = None


# ============ Study Plan Models ============

class ConceptPlan(BaseModel):
    """Single concept in study plan"""
    concept_id: str
    name: str
    description: str
    difficulty: str
    estimated_minutes: int
    order: int
    prerequisites: List[str] = []
    teaching_approach: LearningStyle = LearningStyle.EXAMPLES
    real_world_hook: Optional[str] = None
    
    # Progress tracking
    status: ConceptStatus = ConceptStatus.NOT_STARTED
    attempts: int = 0
    mastery_score: float = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    teaching_approaches_tried: List[str] = []


class StudyPlan(BaseModel):
    """Generated study plan for session"""
    generated_at: Optional[datetime] = None
    total_concepts: int = 0
    estimated_time_minutes: int = 0
    concepts: List[ConceptPlan] = []
    current_concept_index: int = 0


# ============ Teaching Log Models ============

class TeachingLogEntry(BaseModel):
    """Single entry in teaching log"""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    concept_id: str
    entry_type: str  # teaching, check_understanding, assessment, hint, retry, encouragement
    ai_message: str
    student_response: Optional[str] = None
    is_correct: Optional[bool] = None
    feedback_given: Optional[str] = None
    teaching_approach: Optional[str] = None
    hint_given: bool = False
    mistake_type: Optional[str] = None


# ============ Conversation Context ============

class Message(BaseModel):
    """Single message in conversation"""
    role: str  # user, assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Conversation state and context"""
    total_messages: int = 0
    recent_messages: List[Message] = []  # Keep last N messages
    student_mood: StudentMood = StudentMood.ENGAGED
    confusion_signals: int = 0
    frustration_signals: int = 0
    last_encouragement_at: Optional[datetime] = None


# ============ Session Stats ============

class SessionStats(BaseModel):
    """Statistics for current session"""
    duration_minutes: int = 0
    questions_attempted: int = 0
    questions_correct: int = 0
    accuracy_rate: float = 0
    hints_used: int = 0
    concepts_taught: int = 0
    concepts_mastered: int = 0
    xp_earned: int = 0
    streak_maintained: bool = True


# ============ AI Notes ============

class AINotes(BaseModel):
    """AI's observations and recommendations"""
    observations: List[str] = []
    teaching_adjustments_made: List[str] = []
    next_session_recommendations: List[str] = []


# ============ Main Session Model ============

class SessionMeta(BaseModel):
    """Session metadata"""
    subject: str
    class_grade: int
    board: str
    chapter: str
    chapter_number: int
    topic_requested: str
    session_type: str = "learning"
    estimated_duration_minutes: int = 30


class CurrentPhase(str, Enum):
    TOPIC_SELECTION = "topic_selection"
    DIAGNOSTIC = "diagnostic"
    PLAN_GENERATION = "plan_generation"
    TEACHING = "teaching"
    ASSESSMENT = "assessment"
    RETEACH = "reteach"
    WRAPUP = "wrapup"


class Session(BaseModel):
    """Complete session state"""
    # Identifiers
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Metadata
    meta: Optional[SessionMeta] = None
    
    # Student info
    student: StudentSnapshot
    
    # Current state
    current_phase: CurrentPhase = CurrentPhase.TOPIC_SELECTION
    
    # Phase data
    diagnostic: DiagnosticPhase = Field(default_factory=DiagnosticPhase)
    study_plan: StudyPlan = Field(default_factory=StudyPlan)
    
    # Logs
    teaching_log: List[TeachingLogEntry] = []
    conversation: ConversationContext = Field(default_factory=ConversationContext)
    
    # Stats
    stats: SessionStats = Field(default_factory=SessionStats)
    ai_notes: AINotes = Field(default_factory=AINotes)
    
    def update_timestamp(self):
        self.updated_at = datetime.utcnow()
