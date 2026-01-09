# AI Tutor Backend - Copilot Instructions

## Architecture Overview

**AI Tutor Backend** is a FastAPI-based adaptive tutoring system for Indian school students (Classes 6-10). It uses Groq's Llama 3.3 70B LLM to deliver personalized, interactive learning experiences.

### Core Components

- **TutorOrchestrator** (`services/tutor_orchestrator.py`): Main coordination engine orchestrating diagnostic assessment → study plan generation → concept teaching → question evaluation
- **SessionManager** (`services/session_manager.py`): Persistent JSON-based session storage in `data/sessions/`
- **LLMService** (`services/llm_service.py`): Wrapper around Groq API for structured prompt execution
- **PromptBuilder** (`services/prompt_builder.py`): Constructs context-aware prompts for diagnostic, teaching, and evaluation tasks
- **Routers** (`routers/`): FastAPI endpoints for session management (`/session/`) and learning interactions (`/chat/`)

### Data Models Architecture

All models in `models/` use Pydantic v2 for validation:
- **Session**: Core data structure tracking student, progress, phase status, concept mastery, and session log
- **Questions**: Polymorphic union type (`QuestionUnion`) supporting Multiple Choice, True/False, Numeric, Equation, Fill-Blank, Short Answer
- **Enums**: `SessionStatus`, `PhaseStatus`, `ConceptStatus`, `LearningStyle`, `QuestionType`, `Difficulty`

### Learning Flow

1. **Create Session** → `/session/create` (student info, learning style, pace)
2. **Diagnostic Assessment** → `/chat/start-diagnostic` + `/chat/submit-diagnostic-answer` (6 questions max)
3. **Generate Plan** → `/chat/generate-plan` (creates prioritized concept list)
4. **Teach & Practice** → `/chat/start-teaching` + `/chat/submit-answer` (loop per concept)
5. **Wrap Up** → `/chat/end-session` (summary with XP, achievements)

## Critical Patterns

### Prompt Engineering
- All LLM calls go through `prompt_builder` which injects `session_context` (student profile, past misconceptions, current mood)
- Prompts use **JSON schema injection** to force structured LLM output (questions, feedback, plan)
- Key prompt templates: `diagnostic_prompt`, `teach_prompt`, `evaluate_answer_prompt`, `hint_prompt`

### Question Parsing
- LLM returns question JSON; `tutor._parse_question_from_llm()` converts to Pydantic models
- Handles flexible option formats: `"A) option"`, `"option"`, or structured objects
- Question ID generation uses UUID shorthand (first 8 chars)

### Session Persistence
- Every session operation calls `session_manager.save_session(session)` at the end
- Sessions are loaded fresh for each request (stateless API design)
- JSON schema matches Pydantic `Session.model_dump_json()`

### Error Handling
- All endpoints return `APIResponse(success, data, error)` format
- LLM errors don't crash; they're caught and returned in response
- Always validate `session_exists()` before operations

## Configuration

All settings in `config.py` use Pydantic v2 `BaseSettings` with `SettingsConfigDict`:
- `GROQ_API_KEY`: Required in `.env` or environment
- `LLM_MODEL`: Default "llama-3.3-70b-versatile" (do NOT change without testing)
- `LLM_TEMPERATURE`: 0.7 for balanced creativity
- `MAX_DIAGNOSTIC_QUESTIONS`: 6 (tuned for quick assessment)
- `MASTERY_THRESHOLD`: 0.7 (70% to pass a concept)

**Critical Fix Applied**: Pydantic v2 requires `model_config = SettingsConfigDict(...)` not `class Config`

## Common Tasks

### Adding a New Question Type
1. Create class in `models/questions.py` inheriting `QuestionBase`
2. Add to `QuestionUnion` type alias
3. Update `_parse_question_from_llm()` in `tutor_orchestrator.py` to handle new type
4. Add validation example in docstring

### Modifying Learning Flow
- Edit `tutor_orchestrator.py` methods (e.g., `submit_answer()`, `start_teaching_concept()`)
- Update session state: `session.current_phase`, `session.phases[phase].status`
- Always save session after state changes

### Adjusting LLM Prompts
- Modify templates in `prompt_builder.py`
- Test with `test_api.py` using curl examples from README
- Monitor LLM output quality; adjust `LLM_TEMPERATURE` if needed

## Testing & Debugging

**Run API**: `python main.py` (runs on `http://localhost:8000`)

**Test Endpoints**: Use `test_api.py` or curl examples in README (requires `.env` with `GROQ_API_KEY`)

**Debug Sessions**: Inspect JSON in `data/sessions/session_<id>.json` to trace state flow

**Common Issues**:
- 404 on session endpoint: Check `SESSIONS_DIR` path in config
- LLM errors: Verify `GROQ_API_KEY` is set and valid
- Pydantic validation errors: Check question JSON matches schema in `models/questions.py`

## Files to Read First

1. [main.py](main.py) - App setup, lifespan, router registration
2. [services/tutor_orchestrator.py](services/tutor_orchestrator.py#L1-L100) - Core orchestration logic
3. [models/session.py](models/session.py) - Session state structure
4. [models/questions.py](models/questions.py) - Question types
5. [services/prompt_builder.py](services/prompt_builder.py) - LLM prompt construction
