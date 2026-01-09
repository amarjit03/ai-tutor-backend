# Quick Troubleshooting Guide

**Last Updated:** January 7, 2026

---

## Debugging the 500 Error

If you're getting a 500 Internal Server Error, follow these steps:

### Step 1: Check Server Logs

Look at the terminal where your FastAPI server is running. You should see:

```
ERROR: Error in [endpoint_name]: [error message]
Traceback (most recent call last):
  [Full stack trace here]
```

The error message and traceback will tell you exactly what went wrong.

---

### Step 2: Common Error Scenarios

#### ❌ `GROQ_API_KEY not set`
**Cause:** Missing or invalid Groq API key  
**Fix:**
```bash
# Add to .env file
GROQ_API_KEY=gsk_your_api_key_here
```

#### ❌ `Connection timeout to Groq API`
**Cause:** Network issues or Groq service unavailable  
**Fix:** Check your internet connection and Groq service status

#### ❌ `Session not found`
**Cause:** Using an invalid or expired session ID  
**Fix:** Create a new session first with `/session/create`

#### ❌ `No study plan`
**Cause:** Calling `/chat/start-teaching` before generating study plan  
**Fix:** Call `/chat/generate-plan` first

---

### Step 3: Test Individual Components

#### Test Session Creation
```bash
curl -X POST http://localhost:8000/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test_001",
    "student_name": "Test Student",
    "class_grade": 8,
    "subject": "Mathematics",
    "chapter": "Fractions"
  }'
```

Expected response with a valid `session_id`.

#### Test Diagnostic Start
```bash
curl -X POST "http://localhost:8000/chat/start-diagnostic?session_id=YOUR_SESSION_ID"
```

If this fails, check the error in the response and server logs.

#### Check Server Startup
```bash
# Start server and watch for errors
/home/amarjit-singh/Documents/ai-tutor-backend/.venv/bin/python main.py
```

Watch for any startup errors, especially:
- Missing API keys
- Port already in use
- Import errors

---

### Step 4: Enable Debug Mode

Edit `main.py` to enable verbose logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

This will show you detailed information about every request.

---

## Viewing Session Data

Sessions are stored as JSON files in `data/sessions/`:

```bash
# List all sessions
ls -la data/sessions/

# View a specific session
cat data/sessions/session_YOUR_SESSION_ID.json | python -m json.tool
```

This helps you understand the current state of any session.

---

## Environment Checklist

Before running the API, make sure:

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file exists with `GROQ_API_KEY`
- [ ] Port 8000 is available (not in use)
- [ ] `data/sessions/` directory exists
- [ ] `data/curriculum/` directory exists

---

## Common Fix Patterns

### Issue: "Address already in use"
**Solution:** Kill the existing process
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 PID
```

### Issue: "Module not found"
**Solution:** Install missing packages
```bash
pip install -r requirements.txt
pip install groq==0.10.0
```

### Issue: "No API key"
**Solution:** Set environment variable
```bash
# In terminal
export GROQ_API_KEY="your_key_here"

# Or in .env file
GROQ_API_KEY=your_key_here
```

---

## Getting More Help

### Check the Logs
The server will print detailed error messages. Copy the error and search for solutions.

### View the Documentation
- API Documentation: `API_DOCUMENTATION.md`
- Error Handling: `ERROR_HANDLING_FIXES.md`
- Architecture: Copilot Instructions

### Inspect Session Files
Session JSON files contain the complete state. You can manually check what data is being stored.

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point |
| `routers/chat.py` | Learning endpoints |
| `routers/session.py` | Session management endpoints |
| `services/tutor_orchestrator.py` | Core tutoring logic (WITH error handling) |
| `services/llm_service.py` | Groq API integration |
| `data/sessions/` | Session storage (JSON files) |
| `.env` | Configuration and secrets |

---

## Restart Procedure

If the API is behaving strangely:

1. Stop the server: `Ctrl+C`
2. Check `.env` file is correct
3. Clear old session data (optional): `rm data/sessions/*.json`
4. Restart: `/home/amarjit-singh/Documents/ai-tutor-backend/.venv/bin/python main.py`
5. Test with `/session/create` endpoint

---

## Get Stack Trace

When debugging, you want the full error. The improved error handling provides this automatically:

**In the API Response:**
```json
{
  "detail": "Error in start_diagnostic: connection refused"
}
```

**In the Server Console:**
```
ERROR: Error in start_diagnostic: connection refused
Traceback (most recent call last):
  File ".../tutor_orchestrator.py", line 211, in start_diagnostic
    result = self.llm.generate_sync(prompt)
    ... [full traceback] ...
```

Use the full traceback to identify the issue.

---

**Questions?** Check the API_DOCUMENTATION.md or review the code comments in the affected service files.
