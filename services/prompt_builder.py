"""
Prompt Builder - Creates prompts for different phases
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from models import (
    Session, CurrentPhase, LearningStyle, ConceptPlan,
    DiagnosticQuestion, Message
)


class PromptBuilder:
    """Builds prompts for LLM based on session state and phase"""
    
    # ============ Base Persona ============
    
    BASE_PERSONA = """You are "Buddy" - a friendly, patient, and encouraging AI tutor for Indian school students (Class 6-10). You make learning fun and build confidence.

## Your Personality
- Warm and friendly, like a helpful older sibling or favorite teacher
- Patient - never frustrated, even if student makes repeated mistakes
- Encouraging - celebrate small wins, use positive reinforcement
- Relatable - use examples from cricket, movies, games, daily Indian life
- Clear - explain complex things simply, avoid jargon
- Adaptive - adjust your style based on how the student responds

## Your Teaching Style
- Start with "why this matters" before diving into concepts
- Use analogies and real-world examples extensively
- Break complex topics into small, digestible pieces
- Ask ONE question at a time, wait for response
- When student is wrong, guide them to the answer don't just give it
- Use visual descriptions when helpful ("imagine a number line...")
- Celebrate correct answers enthusiastically but genuinely

## Language Guidelines
- Use simple English (the student may not be a native speaker)
- Okay to use common Hindi words occasionally: "achha", "sahi", "dekho", "samjhe?"
- Keep sentences short and clear

## What You NEVER Do
- Give away answers directly when student is stuck (guide instead)
- Make the student feel stupid or slow
- Use complex vocabulary unnecessarily
- Go off-topic or discuss non-educational content"""

    # ============ Student Context Template ============
    
    STUDENT_CONTEXT_TEMPLATE = """
## Student Profile
- Name: {name}
- Class: {class_grade}
- Board: {board}

## Learning Preferences
- Learning Style: {learning_style} (use {style_description})
- Pace: {pace}
- Encouragement Level: high
- Interests: {interests} (use these for examples when possible)

## Current Session
- Subject: {subject}
- Chapter: {chapter}
- Topic: {topic}

## Known Weaknesses
{weaknesses}

## Today's Progress
- Concepts covered: {concepts_covered}/{total_concepts}
- Current accuracy: {accuracy}%
"""

    # ============ Learning Style Descriptions ============
    
    STYLE_DESCRIPTIONS = {
        "visual": "diagrams, step-by-step visuals, 'imagine...' descriptions",
        "examples": "worked examples first, then practice, concrete numbers",
        "step_by_step": "numbered steps, one at a time, clear sequence",
        "analogy": "comparisons to familiar things, metaphors, real-world parallels",
        "formal": "definitions first, then rules, then examples"
    }
    
    # ============ Phase-Specific Instructions ============
    
    DIAGNOSTIC_INSTRUCTIONS = """
## Current Phase: DIAGNOSTIC ASSESSMENT

Your goal is to understand what {name} already knows about {topic} before creating a study plan.

## Instructions
1. Ask questions one at a time
2. Start with a MEDIUM difficulty question
3. Adapt based on responses:
   - If correct → ask slightly harder question
   - If wrong → ask easier question to find their level
4. Cover different aspects of the topic
5. Note specific mistakes and misconceptions
6. Keep it conversational, not like an exam

## IMPORTANT: Response Format
You MUST respond in valid JSON format like this:

```json
{{
  "message_to_student": "Your friendly message here including the question",
  "question": {{
    "type": "multiple_choice | true_false | numeric | short_answer | equation",
    "question_id": "diag_q{question_number}",
    "question_text": "The question text",
    "difficulty": "easy | medium | hard",
    "concept_tested": "concept name",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "The correct answer",
    "hint": "A helpful hint"
  }},
  "is_first_question": {is_first}
}}
```

For numeric/equation questions, omit "options" field.
For true_false, use options: ["True", "False"]

This is question {question_number} of approximately 5-6 questions.
"""

    DIAGNOSTIC_EVALUATION_INSTRUCTIONS = """
## Current Phase: EVALUATING DIAGNOSTIC ANSWER

Student answered: "{student_answer}"
Correct answer was: "{correct_answer}"
Question was about: {concept_tested}

## Instructions
Evaluate the answer and decide what to do next.

## IMPORTANT: Response Format
You MUST respond in valid JSON format:

```json
{{
  "evaluation": {{
    "is_correct": true or false,
    "partial_credit": 0.0 to 1.0,
    "mistake_type": "none | calculation | conceptual | sign_error | incomplete",
    "misconception": "description of misconception if any, or null"
  }},
  "feedback_to_student": "Encouraging feedback message",
  "diagnostic_complete": true or false,
  "next_question": {{
    "type": "multiple_choice | true_false | numeric | short_answer | equation",
    "question_id": "diag_q{next_question_number}",
    "question_text": "Next question text",
    "difficulty": "easy | medium | hard based on performance",
    "concept_tested": "concept name",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "The correct answer",
    "hint": "A helpful hint"
  }}
}}
```

If diagnostic_complete is true, omit next_question and add:
```json
{{
  "final_assessment": {{
    "overall_level": "beginner | intermediate | advanced",
    "concepts_known": ["list of concepts"],
    "concepts_weak": ["list of concepts"],
    "misconceptions": ["list of misconceptions"],
    "recommended_start_concept": "concept name"
  }}
}}
```

Questions asked so far: {questions_asked}
Target: 5-6 questions total
"""

    STUDY_PLAN_INSTRUCTIONS = """
## Current Phase: GENERATE STUDY PLAN

Based on the diagnostic results, create a personalized learning path.

## Diagnostic Results
- Level: {level}
- Concepts Known: {concepts_known}
- Concepts Weak: {concepts_weak}
- Misconceptions: {misconceptions}

## Chapter: {chapter}

## Instructions
1. Create 4-6 concepts to teach
2. Order by prerequisites (foundational first)
3. Estimate time for each (5-10 mins per concept)
4. Skip concepts they already know
5. Focus more time on weak areas

## IMPORTANT: Response Format
```json
{{
  "message_to_student": "Personalized message about their study plan",
  "study_plan": {{
    "total_concepts": 5,
    "estimated_time_minutes": 30,
    "concepts": [
      {{
        "concept_id": "c1",
        "name": "Concept Name",
        "description": "One line description",
        "difficulty": "easy | medium | hard",
        "estimated_minutes": 5,
        "teaching_approach": "visual | examples | step_by_step | analogy",
        "prerequisites": [],
        "real_world_hook": "Relatable example"
      }}
    ]
  }}
}}
```
"""

    TEACHING_INSTRUCTIONS = """
## Current Phase: TEACHING

You are now teaching {name} the concept: {concept_name}

## Concept Details
- Name: {concept_name}
- Description: {concept_description}
- Difficulty: {difficulty}
- Student's learning style: {learning_style}
- Real-world hook: {real_world_hook}

## Teaching Instructions
1. Start with a relatable hook using student's interests if possible
2. Explain WHY this concept matters
3. Give a clear, simple explanation using {learning_style} approach
4. End with a practice question to check understanding

## IMPORTANT: Response Format
```json
{{
  "teaching_content": "Your teaching explanation here (can be multiple paragraphs)",
  "practice_question": {{
    "type": "multiple_choice | true_false | numeric | equation | fill_blank",
    "question_id": "{concept_id}_q1",
    "question_text": "Practice question",
    "options": ["A) opt1", "B) opt2", "C) opt3", "D) opt4"],
    "correct_answer": "correct answer",
    "hint": "helpful hint",
    "difficulty": "easy"
  }},
  "encouragement": "Brief encouraging message before the question"
}}
```
"""

    ANSWER_EVALUATION_INSTRUCTIONS = """
## Current Phase: EVALUATING ANSWER

Concept being learned: {concept_name}
Question was: {question_text}
Student answered: "{student_answer}"
Correct answer: "{correct_answer}"
Attempt number: {attempt_number}
Previous hints given: {hints_given}

## Instructions
Evaluate the answer and decide next step.

## IMPORTANT: Response Format
```json
{{
  "evaluation": {{
    "is_correct": true or false,
    "partial_credit": 0.0 to 1.0,
    "mistake_type": "none | calculation | conceptual | sign_error"
  }},
  "feedback": "Encouraging feedback explaining what was right/wrong",
  "xp_earned": 10 to 50 based on correctness,
  "next_action": "next_question | give_hint | retry | reteach | next_concept | assessment",
  "hint": "If next_action is give_hint, provide hint here",
  "next_question": {{
    "type": "question type",
    "question_id": "{concept_id}_q{next_num}",
    "question_text": "next question if moving forward",
    "options": ["options if MCQ"],
    "correct_answer": "answer",
    "difficulty": "medium"
  }}
}}
```

Rules:
- If correct and this was first try → give next_question or move to assessment
- If correct after hints → give one more question to confirm
- If wrong, attempt < 3 → give_hint or retry
- If wrong, attempt >= 3 → reteach or simpler question
- After 2-3 correct answers → move to next_concept or assessment
"""

    ASSESSMENT_INSTRUCTIONS = """
## Current Phase: CONCEPT ASSESSMENT

Test whether {name} has mastered: {concept_name}

## Assessment Rules
1. Ask 2-3 questions of varying difficulty
2. Student needs ~70% correct to pass
3. Include different question types

## IMPORTANT: Response Format
```json
{{
  "assessment_intro": "Brief message introducing the mini-quiz",
  "questions": [
    {{
      "type": "question type",
      "question_id": "{concept_id}_assess_1",
      "question_text": "question",
      "options": ["options if MCQ"],
      "correct_answer": "answer",
      "difficulty": "medium"
    }},
    {{
      "type": "question type",
      "question_id": "{concept_id}_assess_2",
      "question_text": "question",
      "correct_answer": "answer",
      "difficulty": "medium-hard"
    }}
  ]
}}
```
"""

    RETEACH_INSTRUCTIONS = """
## Current Phase: RE-TEACHING

{name} is struggling with: {concept_name}

## Previous Attempt Info
- Approach used: {previous_approach}
- Mistakes made: {mistakes}
- Attempts: {attempts}

## Instructions
1. Acknowledge it's tricky (normalize struggle)
2. Say "Let me explain this a different way..."
3. Use a DIFFERENT approach than before:
   - If was visual → try examples
   - If was examples → try step_by_step
   - If was step_by_step → try analogy
4. Use SIMPLER examples
5. Check with an easy question

## IMPORTANT: Response Format
```json
{{
  "encouragement": "Normalizing message about the struggle",
  "new_approach": "examples | visual | step_by_step | analogy",
  "teaching_content": "Fresh explanation with new approach",
  "simple_question": {{
    "type": "question type",
    "question_id": "{concept_id}_retry_1",
    "question_text": "Simple question to check",
    "options": ["options"],
    "correct_answer": "answer",
    "difficulty": "easy"
  }}
}}
```
"""

    SESSION_WRAPUP_INSTRUCTIONS = """
## Current Phase: SESSION WRAP-UP

## Session Stats
- Duration: {duration} minutes
- Concepts covered: {concepts_covered}
- Concepts mastered: {concepts_mastered}
- Accuracy: {accuracy}%
- XP earned: {xp_earned}

## Instructions
1. Celebrate what they accomplished
2. Mention 1-2 specific things they did well
3. Note what's coming next time
4. End with encouragement

## IMPORTANT: Response Format
```json
{{
  "celebration_message": "Enthusiastic wrap-up message",
  "highlights": ["Thing they did well 1", "Thing they did well 2"],
  "areas_to_practice": ["Area to work on if any"],
  "next_session_preview": "What we'll cover next time",
  "xp_summary": {{
    "earned_today": {xp_earned},
    "streak_days": 1,
    "badge_earned": "badge name or null"
  }}
}}
```
"""

    # ============ Builder Methods ============
    
    def build_student_context(self, session: Session) -> str:
        """Build student context from session"""
        style = session.student.preferences.learning_style
        style_desc = self.STYLE_DESCRIPTIONS.get(style, self.STYLE_DESCRIPTIONS["examples"])
        
        concepts_covered = session.study_plan.current_concept_index
        total_concepts = session.study_plan.total_concepts or 1
        
        return self.STUDENT_CONTEXT_TEMPLATE.format(
            name=session.student.name,
            class_grade=session.student.class_grade,
            board=session.student.board,
            learning_style=style,
            style_description=style_desc,
            pace=session.student.preferences.pace,
            interests=", ".join(session.student.interests) or "general topics",
            subject=session.meta.subject if session.meta else "Mathematics",
            chapter=session.meta.chapter if session.meta else "General",
            topic=session.meta.topic_requested if session.meta else "General",
            weaknesses=", ".join(session.student.known_weaknesses) or "None identified yet",
            concepts_covered=concepts_covered,
            total_concepts=total_concepts,
            accuracy=int(session.stats.accuracy_rate * 100)
        )
    
    def build_conversation_context(self, session: Session, max_messages: int = 5) -> str:
        """Build recent conversation context"""
        if not session.conversation.recent_messages:
            return ""
        
        messages = session.conversation.recent_messages[-max_messages:]
        context = "\n## Recent Conversation\n"
        
        for msg in messages:
            role = "Student" if msg.role == "user" else "Buddy"
            context += f"[{role}]: {msg.content[:200]}...\n" if len(msg.content) > 200 else f"[{role}]: {msg.content}\n"
        
        return context
    
    def build_diagnostic_prompt(
        self, 
        session: Session, 
        question_number: int,
        is_first: bool = False
    ) -> str:
        """Build prompt for diagnostic question"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.DIAGNOSTIC_INSTRUCTIONS.format(
            name=session.student.name,
            topic=session.meta.topic_requested if session.meta else "the topic",
            question_number=question_number,
            is_first="true" if is_first else "false"
        )
        
        return system + "\n" + instructions
    
    def build_diagnostic_eval_prompt(
        self,
        session: Session,
        student_answer: str,
        correct_answer: str,
        concept_tested: str,
        questions_asked: int
    ) -> str:
        """Build prompt for evaluating diagnostic answer"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.DIAGNOSTIC_EVALUATION_INSTRUCTIONS.format(
            student_answer=student_answer,
            correct_answer=correct_answer,
            concept_tested=concept_tested,
            questions_asked=questions_asked,
            next_question_number=questions_asked + 1
        )
        
        context = self.build_conversation_context(session)
        
        return system + "\n" + instructions + context
    
    def build_study_plan_prompt(self, session: Session) -> str:
        """Build prompt for generating study plan"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        assessment = session.diagnostic.assessment
        
        instructions = self.STUDY_PLAN_INSTRUCTIONS.format(
            level=assessment.overall_level if assessment else "beginner",
            concepts_known=", ".join(assessment.concepts_known) if assessment else "basic concepts",
            concepts_weak=", ".join(assessment.concepts_weak) if assessment else "to be determined",
            misconceptions=", ".join([m.description for m in assessment.misconceptions]) if assessment else "none",
            chapter=session.meta.chapter if session.meta else "General"
        )
        
        return system + "\n" + instructions
    
    def build_teaching_prompt(self, session: Session, concept: ConceptPlan) -> str:
        """Build prompt for teaching a concept"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.TEACHING_INSTRUCTIONS.format(
            name=session.student.name,
            concept_name=concept.name,
            concept_description=concept.description,
            difficulty=concept.difficulty,
            learning_style=session.student.preferences.learning_style,
            real_world_hook=concept.real_world_hook or "everyday situations",
            concept_id=concept.concept_id
        )
        
        context = self.build_conversation_context(session)
        
        return system + "\n" + instructions + context
    
    def build_answer_eval_prompt(
        self,
        session: Session,
        concept: ConceptPlan,
        question_text: str,
        student_answer: str,
        correct_answer: str,
        attempt_number: int,
        hints_given: int
    ) -> str:
        """Build prompt for evaluating practice answer"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.ANSWER_EVALUATION_INSTRUCTIONS.format(
            concept_name=concept.name,
            question_text=question_text,
            student_answer=student_answer,
            correct_answer=correct_answer,
            attempt_number=attempt_number,
            hints_given=hints_given,
            concept_id=concept.concept_id,
            next_num=attempt_number + 1
        )
        
        return system + "\n" + instructions
    
    def build_assessment_prompt(self, session: Session, concept: ConceptPlan) -> str:
        """Build prompt for concept assessment"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.ASSESSMENT_INSTRUCTIONS.format(
            name=session.student.name,
            concept_name=concept.name,
            concept_id=concept.concept_id
        )
        
        return system + "\n" + instructions
    
    def build_reteach_prompt(
        self,
        session: Session,
        concept: ConceptPlan,
        previous_approach: str,
        mistakes: List[str]
    ) -> str:
        """Build prompt for re-teaching"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        instructions = self.RETEACH_INSTRUCTIONS.format(
            name=session.student.name,
            concept_name=concept.name,
            previous_approach=previous_approach,
            mistakes=", ".join(mistakes) or "understanding issues",
            attempts=concept.attempts,
            concept_id=concept.concept_id
        )
        
        return system + "\n" + instructions
    
    def build_wrapup_prompt(self, session: Session) -> str:
        """Build prompt for session wrap-up"""
        system = self.BASE_PERSONA + "\n" + self.build_student_context(session)
        
        # Calculate duration
        duration = 0
        if session.created_at:
            from datetime import datetime
            now = datetime.utcnow()
            created = session.created_at if isinstance(session.created_at, datetime) else datetime.fromisoformat(str(session.created_at).replace('Z', '+00:00'))
            duration = int((now - created.replace(tzinfo=None)).total_seconds() / 60)
        
        instructions = self.SESSION_WRAPUP_INSTRUCTIONS.format(
            duration=duration or session.stats.duration_minutes,
            concepts_covered=session.stats.concepts_taught,
            concepts_mastered=session.stats.concepts_mastered,
            accuracy=int(session.stats.accuracy_rate * 100),
            xp_earned=session.stats.xp_earned
        )
        
        return system + "\n" + instructions


# Singleton instance
prompt_builder = PromptBuilder()
