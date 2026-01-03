"""
Question type models for different UI components
These models define the structure of questions sent to frontend
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class QuestionType(str, Enum):
    """Types of questions that can be rendered in UI"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    NUMERIC = "numeric"
    EQUATION = "equation"
    MATCH_PAIRS = "match_pairs"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============ Question Models for Frontend UI ============

class MultipleChoiceOption(BaseModel):
    """Single option in MCQ"""
    id: str
    text: str
    is_correct: bool = False  # Only used internally, not sent to frontend


class MultipleChoiceQuestion(BaseModel):
    """Multiple choice question structure"""
    type: Literal["multiple_choice"] = "multiple_choice"
    question_id: str
    question_text: str
    options: List[MultipleChoiceOption]
    correct_option_id: str  # Hidden from frontend initially
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None
    explanation: Optional[str] = None  # Shown after answering


class TrueFalseQuestion(BaseModel):
    """True/False question structure"""
    type: Literal["true_false"] = "true_false"
    question_id: str
    statement: str
    correct_answer: bool
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None
    explanation: Optional[str] = None


class FillBlankQuestion(BaseModel):
    """Fill in the blank question"""
    type: Literal["fill_blank"] = "fill_blank"
    question_id: str
    question_text: str  # Use ___ for blank
    correct_answers: List[str]  # Accept multiple correct answers
    case_sensitive: bool = False
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None
    explanation: Optional[str] = None


class ShortAnswerQuestion(BaseModel):
    """Short answer / open text question"""
    type: Literal["short_answer"] = "short_answer"
    question_id: str
    question_text: str
    expected_keywords: List[str] = []  # For AI evaluation
    sample_answer: str  # For AI comparison
    max_length: int = 500
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None


class NumericQuestion(BaseModel):
    """Numeric answer question"""
    type: Literal["numeric"] = "numeric"
    question_id: str
    question_text: str
    correct_answer: float
    tolerance: float = 0.01  # Allow small margin of error
    unit: Optional[str] = None  # e.g., "cm", "kg"
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None
    explanation: Optional[str] = None


class EquationQuestion(BaseModel):
    """Math equation solving question"""
    type: Literal["equation"] = "equation"
    question_id: str
    question_text: str
    equation: str  # e.g., "2x + 5 = 13"
    variable: str = "x"
    correct_answer: float
    tolerance: float = 0.01
    show_steps: bool = True
    difficulty: Difficulty
    concept_tested: str
    hint: Optional[str] = None
    solution_steps: Optional[List[str]] = None


class MatchPair(BaseModel):
    """Single pair for matching"""
    id: str
    left: str
    right: str


class MatchPairsQuestion(BaseModel):
    """Match the pairs question"""
    type: Literal["match_pairs"] = "match_pairs"
    question_id: str
    instruction: str
    pairs: List[MatchPair]
    difficulty: Difficulty
    concept_tested: str


# ============ Union type for any question ============

from typing import Union

QuestionUnion = Union[
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    FillBlankQuestion,
    ShortAnswerQuestion,
    NumericQuestion,
    EquationQuestion,
    MatchPairsQuestion
]


# ============ Response Models ============

class QuestionResponse(BaseModel):
    """Wrapper for sending question to frontend"""
    question: QuestionUnion
    context_message: Optional[str] = None  # AI's message before question
    show_hint_button: bool = True
    time_limit_seconds: Optional[int] = None


class AnswerSubmission(BaseModel):
    """Student's answer submission"""
    session_id: str
    question_id: str
    question_type: QuestionType
    answer: str | float | bool | List[str]  # Varies by question type
    time_taken_seconds: Optional[int] = None


class AnswerEvaluation(BaseModel):
    """Result of evaluating student's answer"""
    is_correct: bool
    partial_credit: float = Field(ge=0, le=1)
    feedback: str
    correct_answer: Optional[str] = None  # Revealed after wrong answer
    explanation: Optional[str] = None
    show_next: Literal["next_question", "hint", "retry", "reteach", "next_concept"]
    xp_earned: int = 0
