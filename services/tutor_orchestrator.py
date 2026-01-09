"""
Tutor Orchestrator - Main brain that coordinates all services
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from models import (
    Session, CurrentPhase, SessionStatus, PhaseStatus, ConceptStatus,
    DiagnosticQuestion, DiagnosticAssessment, Misconception,
    ConceptPlan, StudyPlan, TeachingLogEntry, Message,
    QuestionType, Difficulty, LearningStyle,
    MultipleChoiceQuestion, MultipleChoiceOption,
    TrueFalseQuestion, NumericQuestion, EquationQuestion,
    FillBlankQuestion, ShortAnswerQuestion,
    MessageResponse, QuestionDisplay, FeedbackDisplay,
    StudyPlanDisplay, ProgressDisplay, CelebrationDisplay,
    APIResponse
)
from services.session_manager import session_manager
from services.prompt_builder import prompt_builder
from services.llm_service import llm_service
from config import settings


class TutorOrchestrator:
    """Main orchestrator that coordinates all tutoring logic"""
    
    def __init__(self):
        self.session_manager = session_manager
        self.prompt_builder = prompt_builder
        self.llm = llm_service
    
    # ============ Helper Methods ============
    
    def _parse_question_from_llm(self, q_data: Dict) -> Optional[Any]:
        """Convert LLM question data to proper question model"""
        q_type = q_data.get("type", "short_answer")
        
        base_data = {
            "question_id": q_data.get("question_id", str(uuid.uuid4())[:8]),
            "difficulty": Difficulty(q_data.get("difficulty", "medium")),
            "concept_tested": q_data.get("concept_tested", "general"),
            "hint": q_data.get("hint"),
            "explanation": q_data.get("explanation")
        }
        
        if q_type == "multiple_choice":
            options = q_data.get("options", [])
            correct = q_data.get("correct_answer", "")
            
            parsed_options = []
            correct_id = "a"
            
            for i, opt in enumerate(options):
                opt_id = chr(97 + i)  # a, b, c, d
                opt_text = opt
                
                # Handle "A) text" format
                if ")" in opt:
                    parts = opt.split(")", 1)
                    opt_text = parts[1].strip() if len(parts) > 1 else opt
                
                is_correct = (
                    opt.lower().startswith(correct.lower()[:1]) or 
                    opt_text.lower() == correct.lower() or
                    correct.lower() in opt.lower()
                )
                
                if is_correct:
                    correct_id = opt_id
                
                parsed_options.append(MultipleChoiceOption(
                    id=opt_id,
                    text=opt_text,
                    is_correct=is_correct
                ))
            
            return MultipleChoiceQuestion(
                question_text=q_data.get("question_text", ""),
                options=parsed_options,
                correct_option_id=correct_id,
                **base_data
            )
        
        elif q_type == "true_false":
            correct = q_data.get("correct_answer", "true")
            is_true = correct.lower() in ["true", "yes", "t"]
            
            return TrueFalseQuestion(
                statement=q_data.get("question_text", ""),
                correct_answer=is_true,
                **base_data
            )
        
        elif q_type == "numeric":
            try:
                correct = float(q_data.get("correct_answer", 0))
            except:
                correct = 0.0
            
            return NumericQuestion(
                question_text=q_data.get("question_text", ""),
                correct_answer=correct,
                tolerance=0.01,
                **base_data
            )
        
        elif q_type == "equation":
            try:
                correct = float(q_data.get("correct_answer", 0))
            except:
                correct = 0.0
            
            return EquationQuestion(
                question_text=q_data.get("question_text", ""),
                equation=q_data.get("equation", q_data.get("question_text", "")),
                correct_answer=correct,
                **base_data
            )
        
        elif q_type == "fill_blank":
            correct = q_data.get("correct_answer", "")
            answers = [correct] if isinstance(correct, str) else correct
            
            return FillBlankQuestion(
                question_text=q_data.get("question_text", ""),
                correct_answers=answers,
                **base_data
            )
        
        else:  # short_answer
            return ShortAnswerQuestion(
                question_text=q_data.get("question_text", ""),
                sample_answer=q_data.get("correct_answer", ""),
                **base_data
            )
    
    def _create_progress_display(self, session: Session) -> ProgressDisplay:
        """Create progress display from session"""
        current_concept = "Getting started"
        if session.study_plan.concepts and session.study_plan.current_concept_index < len(session.study_plan.concepts):
            current_concept = session.study_plan.concepts[session.study_plan.current_concept_index].name
        
        return ProgressDisplay(
            concepts_completed=session.stats.concepts_mastered,
            concepts_total=session.study_plan.total_concepts or 1,
            current_concept=current_concept,
            accuracy=session.stats.accuracy_rate,
            xp_earned=session.stats.xp_earned,
            time_spent_minutes=session.stats.duration_minutes
        )
    
    def _check_answer(self, question: Any, answer: Any) -> tuple[bool, float, str]:
        """Check if answer is correct, return (is_correct, partial_credit, correct_answer)"""
        if isinstance(question, MultipleChoiceQuestion):
            is_correct = str(answer).lower() == question.correct_option_id.lower()
            correct = question.correct_option_id
            return is_correct, 1.0 if is_correct else 0.0, correct
        
        elif isinstance(question, TrueFalseQuestion):
            student_bool = str(answer).lower() in ["true", "yes", "t", "1"]
            is_correct = student_bool == question.correct_answer
            return is_correct, 1.0 if is_correct else 0.0, str(question.correct_answer)
        
        elif isinstance(question, (NumericQuestion, EquationQuestion)):
            try:
                student_val = float(answer)
                is_correct = abs(student_val - question.correct_answer) <= question.tolerance
                return is_correct, 1.0 if is_correct else 0.0, str(question.correct_answer)
            except:
                return False, 0.0, str(question.correct_answer)
        
        elif isinstance(question, FillBlankQuestion):
            student_str = str(answer).strip().lower()
            for correct in question.correct_answers:
                if student_str == correct.strip().lower():
                    return True, 1.0, correct
            return False, 0.0, question.correct_answers[0]
        
        else:
            # For short answer, we'll use LLM evaluation
            return True, 0.5, str(getattr(question, 'sample_answer', ''))
    
    # ============ Main Flow Methods ============
    
    async def start_diagnostic(self, session_id: str) -> APIResponse:
        """Start diagnostic assessment phase"""
        try:
            session = self.session_manager.load_session(session_id)
            if not session:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.DIAGNOSTIC,
                    display=[],
                    error="Session not found"
                )
            
            # Update phase
            session.current_phase = CurrentPhase.DIAGNOSTIC
            session.diagnostic.status = PhaseStatus.IN_PROGRESS
            session.diagnostic.started_at = datetime.utcnow()
            
            # Generate first diagnostic question
            prompt = self.prompt_builder.build_diagnostic_prompt(
                session,
                question_number=1,
                is_first=True
            )
            
            result = self.llm.generate_sync(prompt)
            
            if not result["success"]:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.DIAGNOSTIC,
                    display=[MessageResponse(content="I'm having trouble starting. Let me try again...")],
                    error=result.get("error")
                )
            
            response_data = result["response"]
            
            # Parse the question
            question_data = response_data.get("question", {})
            question = self._parse_question_from_llm(question_data)
            
            # Store question in session
            diag_q = DiagnosticQuestion(
                question_id=question_data.get("question_id", "diag_q1"),
                question_text=question_data.get("question_text", ""),
                question_type=question_data.get("type", "short_answer"),
                difficulty=question_data.get("difficulty", "medium"),
                concept_tested=question_data.get("concept_tested", "general"),
                correct_answer=question_data.get("correct_answer", "")
            )
            session.diagnostic.questions.append(diag_q)
            
            # Add message to conversation
            message = response_data.get("message_to_student", "Let's start with a warm-up question!")
            session = self.session_manager.add_message(session, "assistant", message)
            
            # Save session
            self.session_manager.save_session(session)
            
            # Build response
            display = []
            
            if message:
                display.append(MessageResponse(content=message))
            
            if question:
                display.append(QuestionDisplay(
                    question=question,
                    show_hint_button=True
                ))
            
            return APIResponse(
                success=True,
                session_id=session_id,
                current_phase=CurrentPhase.DIAGNOSTIC,
                display=display,
                progress=self._create_progress_display(session)
            )
        
        except Exception as e:
            import traceback
            error_msg = f"Error in start_diagnostic: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.DIAGNOSTIC,
                display=[],
                error=str(e)
            )
    
    async def submit_diagnostic_answer(
        self, 
        session_id: str, 
        question_id: str,
        answer: Any
    ) -> APIResponse:
        """Process a diagnostic answer and continue assessment"""
        try:
            session = self.session_manager.load_session(session_id)
            if not session:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.DIAGNOSTIC,
                    display=[],
                    error="Session not found"
                )
            
            # Find the question
            current_q = None
            for q in session.diagnostic.questions:
                if q.question_id == question_id:
                    current_q = q
                    break
            
            if not current_q:
                # Handle case where question not found
                current_q = session.diagnostic.questions[-1] if session.diagnostic.questions else None
            
            if current_q:
                current_q.student_answer = str(answer)
            
            # Record student message
            session = self.session_manager.add_message(session, "user", str(answer))
            
            # Build evaluation prompt
            prompt = self.prompt_builder.build_diagnostic_eval_prompt(
                session,
                student_answer=str(answer),
                correct_answer=current_q.correct_answer if current_q else "",
                concept_tested=current_q.concept_tested if current_q else "general",
                questions_asked=len(session.diagnostic.questions)
            )
            
            result = self.llm.generate_sync(prompt)
            
            if not result["success"]:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.DIAGNOSTIC,
                    display=[MessageResponse(content="Let me think about that...")],
                    error=result.get("error")
                )
            
            response_data = result["response"]
            
            # Update question with evaluation
            eval_data = response_data.get("evaluation", {})
            if current_q:
                current_q.is_correct = eval_data.get("is_correct", False)
                current_q.mistake_analysis = eval_data.get("misconception")
            
            # Update stats
            session.stats.questions_attempted += 1
            if eval_data.get("is_correct"):
                session.stats.questions_correct += 1
            session.stats.accuracy_rate = session.stats.questions_correct / max(1, session.stats.questions_attempted)
            
            # Add feedback message
            feedback = response_data.get("feedback_to_student", "")
            session = self.session_manager.add_message(session, "assistant", feedback)
            
            display = []
            
            # Check if diagnostic is complete
            if response_data.get("diagnostic_complete") or len(session.diagnostic.questions) >= settings.MAX_DIAGNOSTIC_QUESTIONS:
                # Store final assessment
                final = response_data.get("final_assessment", {})
                session.diagnostic.assessment = DiagnosticAssessment(
                    overall_level=final.get("overall_level", "beginner"),
                    score=session.stats.accuracy_rate,
                    concepts_known=final.get("concepts_known", []),
                    concepts_weak=final.get("concepts_weak", []),
                    misconceptions=[
                        Misconception(
                            id=f"misc_{i}",
                            description=m,
                            severity="medium",
                            related_concept="general"
                        ) for i, m in enumerate(final.get("misconceptions", []))
                    ],
                    recommended_start_concept=final.get("recommended_start_concept", "basics"),
                    personalized_note="Assessment complete"
                )
                session.diagnostic.status = PhaseStatus.COMPLETED
                session.diagnostic.completed_at = datetime.utcnow()
                
                # Move to plan generation
                session.current_phase = CurrentPhase.PLAN_GENERATION
                
                display.append(FeedbackDisplay(
                    is_correct=eval_data.get("is_correct", False),
                    message=feedback,
                    next_action="generate_plan"
                ))
                
                display.append(MessageResponse(
                    content="Great job completing the warm-up! Let me create a personalized study plan for you... 📚",
                    is_encouragement=True
                ))
            else:
                # Add feedback and next question
                display.append(FeedbackDisplay(
                    is_correct=eval_data.get("is_correct", False),
                    message=feedback,
                    correct_answer=current_q.correct_answer if current_q and not eval_data.get("is_correct") else None,
                    next_action="next_question"
                ))
                
                # Parse and add next question
                next_q_data = response_data.get("next_question", {})
                if next_q_data:
                    next_question = self._parse_question_from_llm(next_q_data)
                    
                    # Store question
                    diag_q = DiagnosticQuestion(
                        question_id=next_q_data.get("question_id", f"diag_q{len(session.diagnostic.questions)+1}"),
                        question_text=next_q_data.get("question_text", ""),
                        question_type=next_q_data.get("type", "short_answer"),
                        difficulty=next_q_data.get("difficulty", "medium"),
                        concept_tested=next_q_data.get("concept_tested", "general"),
                        correct_answer=next_q_data.get("correct_answer", "")
                    )
                    session.diagnostic.questions.append(diag_q)
                    
                    if next_question:
                        display.append(QuestionDisplay(
                            question=next_question,
                            show_hint_button=True
                        ))
            
            self.session_manager.save_session(session)
            
            return APIResponse(
                success=True,
                session_id=session_id,
                current_phase=session.current_phase,
                display=display,
                progress=self._create_progress_display(session)
            )
        
        except Exception as e:
            import traceback
            error_msg = f"Error in submit_diagnostic_answer: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.DIAGNOSTIC,
                display=[],
                error=str(e)
            )
    
    async def generate_study_plan(self, session_id: str) -> APIResponse:
        """Generate personalized study plan"""
        try:
            session = self.session_manager.load_session(session_id)
            if not session:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.PLAN_GENERATION,
                    display=[],
                    error="Session not found"
                )
            
            prompt = self.prompt_builder.build_study_plan_prompt(session)
            result = self.llm.generate_sync(prompt)
            
            if not result["success"]:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.PLAN_GENERATION,
                    display=[MessageResponse(content="Let me create your study plan...")],
                    error=result.get("error")
                )
            
            response_data = result["response"]
            plan_data = response_data.get("study_plan", {})
            
            # Build study plan
            concepts = []
            for i, c in enumerate(plan_data.get("concepts", [])):
                concept = ConceptPlan(
                    concept_id=c.get("concept_id", f"c{i+1}"),
                    name=c.get("name", f"Concept {i+1}"),
                    description=c.get("description", ""),
                    difficulty=c.get("difficulty", "medium"),
                    estimated_minutes=c.get("estimated_minutes", 5),
                    order=i + 1,
                    prerequisites=c.get("prerequisites", []),
                    teaching_approach=LearningStyle(c.get("teaching_approach", "examples")),
                    real_world_hook=c.get("real_world_hook"),
                    status=ConceptStatus.NOT_STARTED
                )
                concepts.append(concept)
            
            session.study_plan = StudyPlan(
                generated_at=datetime.utcnow(),
                total_concepts=len(concepts),
                estimated_time_minutes=plan_data.get("estimated_time_minutes", 30),
                concepts=concepts,
                current_concept_index=0
            )
            
            session.current_phase = CurrentPhase.TEACHING
            
            message = response_data.get("message_to_student", "Here's your personalized study plan!")
            session = self.session_manager.add_message(session, "assistant", message)
            
            self.session_manager.save_session(session)
            
            # Build display
            display = [
                MessageResponse(content=message),
                StudyPlanDisplay(
                    message="Let's get started!",
                    total_concepts=len(concepts),
                    estimated_minutes=plan_data.get("estimated_time_minutes", 30),
                    concepts=[{
                    "id": c.concept_id,
                    "name": c.name,
                    "description": c.description,
                    "difficulty": c.difficulty,
                    "estimated_minutes": c.estimated_minutes,
                    "status": c.status.value
                } for c in concepts]
                )
            ]
            
            return APIResponse(
                success=True,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=display,
                progress=self._create_progress_display(session)
            )
        
        except Exception as e:
            import traceback
            error_msg = f"Error in generate_study_plan: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.PLAN_GENERATION,
                display=[],
                error=str(e)
            )
    
    async def start_teaching_concept(self, session_id: str) -> APIResponse:
        """Start teaching the current concept"""
        try:
            session = self.session_manager.load_session(session_id)
            if not session:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.TEACHING,
                    display=[],
                    error="Session not found"
                )
            
            if not session.study_plan.concepts:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.TEACHING,
                    display=[MessageResponse(content="No concepts to teach. Let me generate a plan...")],
                    error="No study plan"
                )
            
            idx = session.study_plan.current_concept_index
            if idx >= len(session.study_plan.concepts):
                # All concepts done - wrap up
                return await self.wrap_up_session(session_id)
            
            concept = session.study_plan.concepts[idx]
            concept.status = ConceptStatus.LEARNING
            concept.started_at = datetime.utcnow()
            concept.attempts = 0
            
            prompt = self.prompt_builder.build_teaching_prompt(session, concept)
            result = self.llm.generate_sync(prompt)
            
            if not result["success"]:
                return APIResponse(
                    success=False,
                    session_id=session_id,
                    current_phase=CurrentPhase.TEACHING,
                    display=[MessageResponse(content=f"Let's learn about {concept.name}...")],
                    error=result.get("error")
                )
            
            response_data = result["response"]
            
            # Store teaching content
            teaching_content = response_data.get("teaching_content", "")
            encouragement = response_data.get("encouragement", "")
            
            session = self.session_manager.add_message(session, "assistant", teaching_content)
            
            # Log teaching entry
            session.teaching_log.append(TeachingLogEntry(
                concept_id=concept.concept_id,
                entry_type="teaching",
                ai_message=teaching_content,
                teaching_approach=concept.teaching_approach.value
            ))
            
            display = [
                MessageResponse(content=teaching_content),
            ]
            
            # Add practice question
            q_data = response_data.get("practice_question", {})
            if q_data:
                question = self._parse_question_from_llm(q_data)
                
                if encouragement:
                    display.append(MessageResponse(content=encouragement))
                
                if question:
                    display.append(QuestionDisplay(
                        question=question,
                        show_hint_button=True,
                        attempts_remaining=3
                    ))
                
                # Store current question info for later evaluation
                session.teaching_log.append(TeachingLogEntry(
                    concept_id=concept.concept_id,
                    entry_type="check_understanding",
                    ai_message=q_data.get("question_text", ""),
                ))
            
            session.stats.concepts_taught += 1
            self.session_manager.save_session(session)
            
            return APIResponse(
                success=True,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=display,
                progress=self._create_progress_display(session)
            )
        
        except Exception as e:
            import traceback
            error_msg = f"Error in start_teaching_concept: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=[],
                error=str(e)
            )
    
    async def submit_practice_answer(
        self,
        session_id: str,
        question_id: str,
        answer: Any
    ) -> APIResponse:
        """Process practice/assessment answer during teaching"""
        session = self.session_manager.load_session(session_id)
        if not session:
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=[],
                error="Session not found"
            )
        
        idx = session.study_plan.current_concept_index
        concept = session.study_plan.concepts[idx] if idx < len(session.study_plan.concepts) else None
        
        if not concept:
            return await self.wrap_up_session(session_id)
        
        concept.attempts += 1
        session = self.session_manager.add_message(session, "user", str(answer))
        
        # Find question details from teaching log
        last_question = None
        for entry in reversed(session.teaching_log):
            if entry.entry_type in ["check_understanding", "assessment"]:
                last_question = entry
                break
        
        question_text = last_question.ai_message if last_question else ""
        
        # Get LLM evaluation
        prompt = self.prompt_builder.build_answer_eval_prompt(
            session,
            concept,
            question_text=question_text,
            student_answer=str(answer),
            correct_answer="",  # LLM will evaluate
            attempt_number=concept.attempts,
            hints_given=session.stats.hints_used
        )
        
        result = self.llm.generate_sync(prompt)
        
        if not result["success"]:
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=[MessageResponse(content="Let me check that...")],
                error=result.get("error")
            )
        
        response_data = result["response"]
        eval_data = response_data.get("evaluation", {})
        
        is_correct = eval_data.get("is_correct", False)
        feedback = response_data.get("feedback", "")
        xp = response_data.get("xp_earned", 10 if is_correct else 0)
        next_action = response_data.get("next_action", "next_question")
        
        # Update stats
        session.stats.questions_attempted += 1
        if is_correct:
            session.stats.questions_correct += 1
            concept.mastery_score += 0.25
        session.stats.xp_earned += xp
        session.stats.accuracy_rate = session.stats.questions_correct / max(1, session.stats.questions_attempted)
        
        # Log response
        session.teaching_log.append(TeachingLogEntry(
            concept_id=concept.concept_id,
            entry_type="assessment",
            ai_message=question_text,
            student_response=str(answer),
            is_correct=is_correct,
            feedback_given=feedback
        ))
        
        session = self.session_manager.add_message(session, "assistant", feedback)
        
        display = [
            FeedbackDisplay(
                is_correct=is_correct,
                message=feedback,
                xp_earned=xp,
                next_action=next_action
            )
        ]
        
        # Handle next action
        if next_action == "next_concept" or (is_correct and concept.mastery_score >= 0.75):
            concept.status = ConceptStatus.MASTERED
            concept.completed_at = datetime.utcnow()
            session.stats.concepts_mastered += 1
            session.study_plan.current_concept_index += 1
            
            # Celebration
            display.append(CelebrationDisplay(
                title="Concept Mastered! 🎉",
                message=f"You've mastered {concept.name}!",
                xp_earned=xp + 20
            ))
            session.stats.xp_earned += 20
            
            # Check if more concepts
            if session.study_plan.current_concept_index >= len(session.study_plan.concepts):
                display.append(MessageResponse(
                    content="Amazing! You've completed all concepts for today! Let me wrap up your session...",
                    is_encouragement=True
                ))
                session.current_phase = CurrentPhase.WRAPUP
            else:
                next_concept = session.study_plan.concepts[session.study_plan.current_concept_index]
                display.append(MessageResponse(
                    content=f"Ready for the next concept? We'll learn about: {next_concept.name}",
                    is_encouragement=True
                ))
        
        elif next_action == "reteach":
            session.current_phase = CurrentPhase.RETEACH
            display.append(MessageResponse(
                content="No worries! Let me explain this differently...",
                is_encouragement=True
            ))
        
        elif next_action == "give_hint":
            hint = response_data.get("hint", "Think about it step by step...")
            session.stats.hints_used += 1
            display.append(MessageResponse(content=f"💡 Hint: {hint}"))
        
        elif next_action in ["next_question", "retry"]:
            next_q = response_data.get("next_question", {})
            if next_q:
                question = self._parse_question_from_llm(next_q)
                if question:
                    display.append(QuestionDisplay(
                        question=question,
                        show_hint_button=True,
                        attempts_remaining=max(0, 3 - concept.attempts)
                    ))
                    session.teaching_log.append(TeachingLogEntry(
                        concept_id=concept.concept_id,
                        entry_type="check_understanding",
                        ai_message=next_q.get("question_text", "")
                    ))
        
        self.session_manager.save_session(session)
        
        return APIResponse(
            success=True,
            session_id=session_id,
            current_phase=session.current_phase,
            display=display,
            progress=self._create_progress_display(session)
        )
    
    async def get_hint(self, session_id: str, question_id: str) -> APIResponse:
        """Get hint for current question"""
        session = self.session_manager.load_session(session_id)
        if not session:
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.TEACHING,
                display=[],
                error="Session not found"
            )
        
        session.stats.hints_used += 1
        
        # Find recent question
        hint = "Try breaking down the problem into smaller steps. What do you know for sure?"
        
        for entry in reversed(session.teaching_log):
            if entry.entry_type == "check_understanding":
                hint = f"Think about: {entry.ai_message[:100]}... What's the first step?"
                break
        
        self.session_manager.save_session(session)
        
        return APIResponse(
            success=True,
            session_id=session_id,
            current_phase=session.current_phase,
            display=[MessageResponse(content=f"💡 {hint}")],
            progress=self._create_progress_display(session)
        )
    
    async def wrap_up_session(self, session_id: str) -> APIResponse:
        """Wrap up the session with summary"""
        session = self.session_manager.load_session(session_id)
        if not session:
            return APIResponse(
                success=False,
                session_id=session_id,
                current_phase=CurrentPhase.WRAPUP,
                display=[],
                error="Session not found"
            )
        
        session.current_phase = CurrentPhase.WRAPUP
        session.status = SessionStatus.COMPLETED
        
        # Calculate duration
        if session.created_at:
            created = session.created_at if isinstance(session.created_at, datetime) else datetime.fromisoformat(str(session.created_at).replace('Z', '+00:00'))
            session.stats.duration_minutes = int((datetime.utcnow() - created.replace(tzinfo=None)).total_seconds() / 60)
        
        prompt = self.prompt_builder.build_wrapup_prompt(session)
        result = self.llm.generate_sync(prompt)
        
        display = []
        
        if result["success"]:
            data = result["response"]
            
            display.append(CelebrationDisplay(
                title="Session Complete! 🎉",
                message=data.get("celebration_message", "Great work today!"),
                xp_earned=session.stats.xp_earned,
                streak_days=data.get("xp_summary", {}).get("streak_days", 1)
            ))
            
            from models.schemas import SessionSummary
            display.append(SessionSummary(
                duration_minutes=session.stats.duration_minutes,
                concepts_covered=session.stats.concepts_taught,
                concepts_mastered=session.stats.concepts_mastered,
                accuracy=session.stats.accuracy_rate,
                xp_earned=session.stats.xp_earned,
                highlights=data.get("highlights", []),
                areas_to_practice=data.get("areas_to_practice", []),
                next_session_preview=data.get("next_session_preview", "More exciting concepts await!")
            ))
        else:
            display.append(MessageResponse(
                content=f"Great work today, {session.student.name}! You covered {session.stats.concepts_mastered} concepts. See you next time! 👋",
                is_encouragement=True
            ))
        
        self.session_manager.save_session(session)
        
        return APIResponse(
            success=True,
            session_id=session_id,
            current_phase=CurrentPhase.WRAPUP,
            display=display,
            progress=self._create_progress_display(session)
        )


# Singleton instance
tutor = TutorOrchestrator()
