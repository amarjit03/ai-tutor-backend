# AI Tutor Backend 🎓

An adaptive AI tutoring system backend for Indian school students (Class 6-10). Built with FastAPI and Groq LLM.

## Features

- 📊 **Diagnostic Assessment** - Understands student's current level
- 📚 **Personalized Study Plans** - Based on student's strengths and gaps
- 🎓 **Adaptive Teaching** - Multiple teaching approaches (visual, examples, step-by-step)
- ❓ **Interactive Questions** - MCQ, True/False, Numeric, Fill-in-blanks, and more
- 🎮 **Gamification** - XP, streaks, and achievements
- 💾 **Session Persistence** - JSON-based session storage

## Tech Stack

- **Framework**: FastAPI
- **LLM**: Groq API (Llama 3.3 70B)
- **Data Validation**: Pydantic
- **Session Storage**: JSON files

## Quick Start

### 1. Clone and Setup

```bash
cd ai-tutor-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get your free Groq API key from: https://console.groq.com/

### 3. Run the Server

```bash
python main.py
# or
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

### 4. View API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/session/create` | POST | Create new tutoring session |
| `/session/{id}` | GET | Get session details |
| `/session/{id}/progress` | GET | Get progress summary |
| `/session/list/{student_id}` | GET | List student's sessions |
| `/session/{id}` | DELETE | Delete a session |

### Learning Flow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/start-diagnostic` | POST | Start diagnostic assessment |
| `/chat/submit-diagnostic-answer` | POST | Submit diagnostic answer |
| `/chat/generate-plan` | POST | Generate study plan |
| `/chat/start-teaching` | POST | Start teaching a concept |
| `/chat/submit-answer` | POST | Submit practice answer |
| `/chat/get-hint` | POST | Request a hint |
| `/chat/skip-concept` | POST | Skip current concept |
| `/chat/end-session` | POST | End session with summary |
| `/chat/next` | POST | Auto-proceed to next step |

## API Usage Examples

### Create a Session

```bash
curl -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_001",
    "student_name": "Arjun",
    "class_grade": 8,
    "board": "CBSE",
    "subject": "Mathematics",
    "chapter": "Linear Equations",
    "interests": ["cricket", "video games"],
    "learning_style": "examples",
    "pace": "medium"
  }'
```

### Start Diagnostic

```bash
curl -X POST "http://localhost:8000/chat/start-diagnostic?session_id=<SESSION_ID>"
```

### Submit Answer

```bash
curl -X POST "http://localhost:8000/chat/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<SESSION_ID>",
    "question_id": "q1",
    "question_type": "multiple_choice",
    "answer": "b"
  }'
```

## Response Format

All learning endpoints return a structured response:

```json
{
  "success": true,
  "session_id": "uuid",
  "current_phase": "teaching",
  "display": [
    {
      "type": "message",
      "content": "AI tutor message here"
    },
    {
      "type": "question",
      "question": {
        "type": "multiple_choice",
        "question_id": "q1",
        "question_text": "What is 2 + 2?",
        "options": [
          {"id": "a", "text": "3"},
          {"id": "b", "text": "4"},
          {"id": "c", "text": "5"}
        ],
        "difficulty": "easy"
      }
    }
  ],
  "progress": {
    "concepts_completed": 2,
    "concepts_total": 5,
    "accuracy": 0.8,
    "xp_earned": 150
  }
}
```

## Question Types

The backend supports multiple question types for rich UI:

| Type | Description | Answer Format |
|------|-------------|---------------|
| `multiple_choice` | MCQ with options | Option ID (a, b, c, d) |
| `true_false` | True/False statement | "true" or "false" |
| `numeric` | Numerical answer | Number |
| `equation` | Math equation | Number (solution) |
| `fill_blank` | Fill in the blank | String |
| `short_answer` | Open text | String |

## Project Structure

```
ai-tutor-backend/
├── main.py                 # FastAPI application entry
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
│
├── models/
│   ├── __init__.py
│   ├── questions.py        # Question type models
│   ├── session.py          # Session data models
│   └── schemas.py          # API request/response schemas
│
├── services/
│   ├── __init__.py
│   ├── llm_service.py      # Groq LLM integration
│   ├── session_manager.py  # JSON session management
│   ├── prompt_builder.py   # Prompt templates
│   └── tutor_orchestrator.py  # Main tutoring logic
│
├── routers/
│   ├── __init__.py
│   ├── session.py          # Session endpoints
│   └── chat.py             # Learning endpoints
│
└── data/
    ├── sessions/           # Session JSON files
    └── curriculum/         # Curriculum reference files
```

## Frontend Integration Guide

### Learning Flow

1. **Create Session** → Get `session_id`
2. **Start Diagnostic** → Receive first question
3. **Loop: Submit Answer** → Receive feedback + next question
4. **Diagnostic Complete** → Generate study plan
5. **Start Teaching** → Receive content + practice question
6. **Loop: Submit Answer** → Feedback + next question/concept
7. **End Session** → Summary + achievements

### Display Types to Handle

Your frontend should render these `display` types:

- `message` - Text message from AI
- `question` - Interactive question component
- `feedback` - Answer evaluation result
- `study_plan` - Study plan overview
- `progress` - Progress bar/stats
- `celebration` - Achievement popup
- `session_summary` - End-of-session summary

### Question Component Examples

```jsx
// For type: "multiple_choice"
<MCQQuestion 
  question={data.question_text}
  options={data.options}
  onSelect={(optionId) => submitAnswer(optionId)}
/>

// For type: "true_false"
<TrueFalseQuestion
  statement={data.statement}
  onSelect={(value) => submitAnswer(value)}
/>

// For type: "numeric"
<NumericInput
  question={data.question_text}
  unit={data.unit}
  onSubmit={(value) => submitAnswer(value)}
/>
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (required) | - |
| `LLM_MODEL` | LLM model to use | llama-3.3-70b-versatile |
| `LLM_TEMPERATURE` | Response creativity | 0.7 |
| `LLM_MAX_TOKENS` | Max response tokens | 2048 |
| `DEBUG` | Enable debug mode | true |
| `SESSIONS_DIR` | Session storage path | data/sessions |

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## License

MIT License
