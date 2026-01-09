# AI Tutor Backend - API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Response Format](#response-format)
4. [Error Handling](#error-handling)
5. [Session Management](#session-management)
6. [Learning Flow](#learning-flow)
7. [Question Types](#question-types)
8. [Data Models](#data-models)
9. [Integration Guide](#integration-guide)

---

## Overview

The AI Tutor Backend is a FastAPI-based adaptive tutoring system for Indian school students (Classes 6-10). It provides personalized learning experiences through:

- **Diagnostic Assessment** - Evaluates student's current knowledge level
- **Adaptive Teaching** - Personalized content based on learning style and pace
- **Interactive Questions** - Multiple question types with instant feedback
- **Progress Tracking** - Real-time XP, achievements, and mastery scores
- **Gamification** - Streaks, badges, and rewards system

### Key Features

✅ Adaptive learning paths  
✅ Multiple question types (MCQ, True/False, Numeric, Equations, etc.)  
✅ Real-time feedback and hints  
✅ Session persistence  
✅ Progress tracking with XP system  
✅ Concept mastery scoring  

---

## Authentication

Currently, the API does **not require authentication** tokens. In production, implement bearer token authentication.

**Future Implementation:**
```bash
Authorization: Bearer <token>
```

---

## Response Format

### Standard Success Response

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "teaching",
  "display": [
    {
      "type": "message",
      "content": "Great! Let's learn about fractions...",
      "is_encouragement": false
    },
    {
      "type": "question",
      "question": { ... },
      "context_message": "Try this practice problem:",
      "show_hint_button": true,
      "attempts_remaining": 3
    }
  ],
  "progress": {
    "type": "progress",
    "concepts_completed": 2,
    "concepts_total": 8,
    "current_concept": "Fractions",
    "accuracy": 0.75,
    "xp_earned": 150,
    "time_spent_minutes": 15
  },
  "timestamp": "2026-01-07T10:30:00Z",
  "error": null
}
```

### Error Response

```json
{
  "detail": "Session not found"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |

---

## Error Handling

All errors follow this pattern:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

| Scenario | Status | Response |
|----------|--------|----------|
| Session ID not found | 404 | `{"detail": "Session not found"}` |
| Invalid request | 400 | `{"detail": "Invalid request format"}` |
| Server error | 500 | `{"detail": "Internal server error"}` |

---

## Session Management

### 1. Create Session

**Endpoint:** `POST /session/create`

Creates a new tutoring session for a student.

**Request:**
```json
{
  "student_id": "student_001",
  "student_name": "Raj Kumar",
  "class_grade": 8,
  "board": "CBSE",
  "subject": "Mathematics",
  "chapter": "Fractions and Decimals",
  "topic": "Adding Fractions",
  "interests": ["sports", "music"],
  "learning_style": "examples",
  "pace": "medium"
}
```

**Parameters:**

| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `student_id` | string | Yes | - | Unique student identifier |
| `student_name` | string | Yes | - | Student's full name |
| `class_grade` | integer | Yes | 6-10 | Student's class (6-10) |
| `board` | string | No | "CBSE", "ICSE" | Educational board |
| `subject` | string | Yes | - | Subject (e.g., Mathematics) |
| `chapter` | string | Yes | - | Chapter/Unit to study |
| `topic` | string | No | - | Specific topic (defaults to chapter) |
| `interests` | array | No | - | Student interests for personalization |
| `learning_style` | enum | No | "examples", "stories", "visual", "practice" | Preferred learning style |
| `pace` | string | No | "slow", "medium", "fast" | Learning pace preference |

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Hi Raj Kumar! Ready to learn Mathematics? Let's start with a quick warm-up to see what you already know!",
  "student_name": "Raj Kumar",
  "subject": "Mathematics",
  "chapter": "Fractions and Decimals"
}
```

---

### 2. Get Session Details

**Endpoint:** `GET /session/{session_id}`

Retrieves full session state including progress, phases, and statistics.

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "student_id": "student_001",
    "student_name": "Raj Kumar",
    "status": "active",
    "current_phase": "teaching",
    "subject": "Mathematics",
    "chapter": "Fractions and Decimals",
    "created_at": "2026-01-07T10:00:00Z",
    "updated_at": "2026-01-07T10:30:00Z",
    "stats": {
      "duration_minutes": 30,
      "questions_attempted": 10,
      "questions_correct": 7,
      "accuracy_rate": 0.7,
      "concepts_mastered": 2,
      "xp_earned": 250
    },
    "study_plan": {
      "total_concepts": 8,
      "current_concept_index": 2,
      "concepts": [
        {
          "id": "concept_001",
          "name": "Fractions Basics",
          "status": "mastered",
          "mastery_score": 0.85
        },
        {
          "id": "concept_002",
          "name": "Adding Fractions",
          "status": "in_progress",
          "mastery_score": 0.65
        }
      ]
    },
    "diagnostic": {
      "status": "completed",
      "questions_asked": 6,
      "assessment": {
        "level": "intermediate",
        "score": 70
      }
    }
  }
}
```

---

### 3. Get Progress Summary

**Endpoint:** `GET /session/{session_id}/progress`

Returns lightweight progress data for UI updates.

**Response:**
```json
{
  "success": true,
  "progress": {
    "current_phase": "teaching",
    "concepts_completed": 2,
    "concepts_total": 8,
    "current_concept": "Adding Fractions",
    "accuracy": 0.75,
    "xp_earned": 250,
    "questions_attempted": 10,
    "questions_correct": 7
  }
}
```

---

### 4. List Student Sessions

**Endpoint:** `GET /session/list/{student_id}`

Lists all sessions for a specific student.

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "subject": "Mathematics",
      "chapter": "Fractions and Decimals",
      "status": "active",
      "created_at": "2026-01-07T10:00:00Z",
      "progress": {
        "accuracy": 0.75,
        "xp_earned": 250
      }
    }
  ]
}
```

---

## Learning Flow

The complete learning journey consists of these phases:

```
1. Create Session
    ↓
2. Diagnostic Assessment (6 questions max)
    ↓
3. Generate Study Plan (based on diagnostic results)
    ↓
4. Teach & Practice (loop per concept)
    ↓
5. Session Wrap-up
```

### Phase 1: Diagnostic Assessment

#### Start Diagnostic

**Endpoint:** `POST /chat/start-diagnostic`

Begins the initial assessment to understand student's current level.

**Query Parameters:**
| Parameter | Type | Required |
|-----------|------|----------|
| `session_id` | string | Yes |

**Request:**
```bash
POST /chat/start-diagnostic?session_id=550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "diagnostic",
  "display": [
    {
      "type": "message",
      "content": "Let's start with a warm-up assessment! This will help me understand your current level."
    },
    {
      "type": "question",
      "question": {
        "type": "multiple_choice",
        "question_id": "diag_001",
        "question_text": "What is 1/2 + 1/4?",
        "options": [
          { "id": "opt_1", "text": "2/6" },
          { "id": "opt_2", "text": "3/4" },
          { "id": "opt_3", "text": "1/6" },
          { "id": "opt_4", "text": "2/4" }
        ],
        "difficulty": "easy",
        "concept_tested": "Fractions"
      }
    }
  ],
  "timestamp": "2026-01-07T10:30:00Z"
}
```

---

#### Submit Diagnostic Answer

**Endpoint:** `POST /chat/submit-diagnostic-answer`

Submits an answer during diagnostic assessment.

**Query Parameters:**
| Parameter | Type | Required |
|-----------|------|----------|
| `session_id` | string | Yes |
| `question_id` | string | Yes |
| `answer` | string | Yes |

**Request:**
```bash
POST /chat/submit-diagnostic-answer?session_id=550e8400-e29b-41d4-a716-446655440000&question_id=diag_001&answer=opt_2
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "diagnostic",
  "display": [
    {
      "type": "feedback",
      "is_correct": true,
      "message": "Perfect! 1/2 + 1/4 = 2/4 + 1/4 = 3/4. You understand fraction addition!",
      "xp_earned": 10,
      "next_action": "next_question"
    },
    {
      "type": "question",
      "question": {
        "type": "numeric",
        "question_id": "diag_002",
        "question_text": "What is 25% of 80?",
        "unit": null,
        "difficulty": "easy",
        "concept_tested": "Percentages"
      }
    }
  ]
}
```

---

### Phase 2: Generate Study Plan

**Endpoint:** `POST /chat/generate-plan`

Creates personalized study plan based on diagnostic results.

**Query Parameters:**
| Parameter | Type | Required |
|-----------|------|----------|
| `session_id` | string | Yes |

**Request:**
```bash
POST /chat/generate-plan?session_id=550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "planning",
  "display": [
    {
      "type": "message",
      "content": "Based on your assessment, here's your personalized learning path..."
    },
    {
      "type": "study_plan",
      "message": "I've created a focused study plan for you!",
      "total_concepts": 5,
      "estimated_minutes": 45,
      "concepts": [
        {
          "id": "concept_001",
          "name": "Fractions Basics",
          "priority": "high",
          "estimated_time": 10
        },
        {
          "id": "concept_002",
          "name": "Adding Fractions",
          "priority": "high",
          "estimated_time": 12
        }
      ]
    }
  ]
}
```

---

### Phase 3: Teach & Practice

#### Start Teaching

**Endpoint:** `POST /chat/start-teaching`

Starts teaching the current/next concept in the study plan.

**Query Parameters:**
| Parameter | Type | Required |
|-----------|------|----------|
| `session_id` | string | Yes |

**Request:**
```bash
POST /chat/start-teaching?session_id=550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "teaching",
  "display": [
    {
      "type": "message",
      "content": "Let's learn about **Adding Fractions**!\n\nWhen you add fractions with the same denominator, you just add the numerators.\n\nFor example: 1/4 + 2/4 = 3/4\n\nBut when denominators are different, you need to find a common denominator first."
    },
    {
      "type": "question",
      "question": {
        "type": "numeric",
        "question_id": "teach_001",
        "question_text": "What is 1/3 + 1/6? (Express as a decimal)",
        "tolerance": 0.01,
        "difficulty": "medium",
        "concept_tested": "Adding Fractions"
      },
      "context_message": "Try this practice problem:",
      "show_hint_button": true,
      "attempts_remaining": 3
    }
  ],
  "progress": {
    "type": "progress",
    "concepts_completed": 1,
    "concepts_total": 5,
    "current_concept": "Adding Fractions",
    "accuracy": 1.0,
    "xp_earned": 50
  }
}
```

---

#### Submit Practice Answer

**Endpoint:** `POST /chat/submit-answer`

Evaluates student's answer during practice/teaching phase.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_id": "teach_001",
  "question_type": "numeric",
  "answer": 0.5,
  "time_taken_seconds": 45
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Session identifier |
| `question_id` | string | Yes | Question identifier |
| `question_type` | enum | Yes | Type of question (see below) |
| `answer` | any | Yes | Student's answer (format depends on question type) |
| `time_taken_seconds` | integer | No | Time spent on question |

**Question Type Values:**
- `multiple_choice` - Answer is option ID
- `true_false` - Answer is "true" or "false"
- `numeric` - Answer is a number
- `fill_blank` - Answer is string text
- `short_answer` - Answer is string text
- `equation` - Answer is numeric solution
- `match_pairs` - Answer is list of matched pair IDs

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "teaching",
  "display": [
    {
      "type": "feedback",
      "is_correct": true,
      "message": "Excellent! 1/3 + 1/6 = 2/6 + 1/6 = 3/6 = 1/2 = 0.5 ✓",
      "explanation": "We found a common denominator (6), then added.",
      "xp_earned": 25,
      "next_action": "next_question"
    },
    {
      "type": "celebration",
      "title": "Great Job!",
      "message": "You've mastered Adding Fractions! 🎉",
      "xp_earned": 50,
      "badge_earned": "Fraction Master"
    }
  ],
  "progress": {
    "type": "progress",
    "concepts_completed": 2,
    "concepts_total": 5,
    "current_concept": "Multiplying Fractions",
    "accuracy": 0.8,
    "xp_earned": 125
  }
}
```

---

#### Request Hint

**Endpoint:** `POST /chat/get-hint`

Requests a hint for current question without revealing the answer.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_id": "teach_001"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "teaching",
  "display": [
    {
      "type": "message",
      "content": "💡 **Hint:** Try finding a common denominator first. What's a number that both 3 and 6 divide into?",
      "is_encouragement": false
    }
  ]
}
```

---

#### Skip Concept

**Endpoint:** `POST /chat/skip-concept`

Allows student to skip a difficult concept and move to next.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Too difficult"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "teaching",
  "display": [
    {
      "type": "message",
      "content": "No problem! We can come back to this later. Let's move on to the next topic for now."
    },
    {
      "type": "question",
      "question": {
        "type": "multiple_choice",
        "question_id": "teach_005",
        "question_text": "What is 2/3 × 3/4?",
        "options": [
          { "id": "opt_1", "text": "6/12 (or 1/2)" },
          { "id": "opt_2", "text": "5/7" },
          { "id": "opt_3", "text": "6/7" }
        ],
        "difficulty": "medium",
        "concept_tested": "Multiplying Fractions"
      }
    }
  ]
}
```

---

### Phase 4: Session Wrap-up

**Endpoint:** `POST /chat/end-session`

Ends the session and provides comprehensive summary.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "completed",
  "display": [
    {
      "type": "session_summary",
      "duration_minutes": 45,
      "concepts_covered": 4,
      "concepts_mastered": 3,
      "accuracy": 0.8,
      "xp_earned": 450,
      "highlights": [
        "Mastered Fractions Basics",
        "Strong performance in Adding Fractions",
        "Impressive improvement in accuracy!"
      ],
      "areas_to_practice": [
        "Multiplying Fractions",
        "Complex word problems"
      ],
      "next_session_preview": "Next time, we can focus on multiplying and dividing fractions with different denominators."
    }
  ]
}
```

---

## Question Types

### 1. Multiple Choice

```json
{
  "type": "multiple_choice",
  "question_id": "q_001",
  "question_text": "What is 1/2 + 1/4?",
  "options": [
    { "id": "opt_a", "text": "2/6" },
    { "id": "opt_b", "text": "3/4" },
    { "id": "opt_c", "text": "1/6" },
    { "id": "opt_d", "text": "2/4" }
  ],
  "difficulty": "easy",
  "concept_tested": "Fractions",
  "hint": "Find a common denominator"
}
```

**Expected Answer:** Option ID (string)  
**Example:** `"opt_b"`

---

### 2. True/False

```json
{
  "type": "true_false",
  "question_id": "q_002",
  "statement": "The sum of angles in a triangle is 180 degrees",
  "difficulty": "easy",
  "concept_tested": "Geometry",
  "hint": "Think about basic geometry rules"
}
```

**Expected Answer:** `"true"` or `"false"` (string)

---

### 3. Numeric

```json
{
  "type": "numeric",
  "question_id": "q_003",
  "question_text": "What is 25% of 80?",
  "unit": null,
  "difficulty": "easy",
  "concept_tested": "Percentages",
  "hint": "25% is 1/4"
}
```

**Expected Answer:** Number (float)  
**Example:** `20` or `20.0`

---

### 4. Fill in the Blank

```json
{
  "type": "fill_blank",
  "question_id": "q_004",
  "question_text": "The chemical formula for water is H₂___",
  "case_sensitive": false,
  "difficulty": "easy",
  "concept_tested": "Chemistry",
  "hint": "Oxygen..."
}
```

**Expected Answer:** String text  
**Example:** `"O"` or `"o"`

---

### 5. Short Answer

```json
{
  "type": "short_answer",
  "question_id": "q_005",
  "question_text": "Explain what a fraction is in your own words",
  "expected_keywords": ["part", "whole", "divide"],
  "max_length": 500,
  "difficulty": "medium",
  "concept_tested": "Fractions"
}
```

**Expected Answer:** String text (AI evaluates)  
**Example:** `"A fraction represents a part of a whole"`

---

### 6. Equation Solving

```json
{
  "type": "equation",
  "question_id": "q_006",
  "question_text": "Solve for x: 2x + 5 = 13",
  "equation": "2x + 5 = 13",
  "variable": "x",
  "show_steps": true,
  "difficulty": "easy",
  "concept_tested": "Algebra"
}
```

**Expected Answer:** Number (float)  
**Example:** `4` or `4.0`

---

### 7. Match Pairs

```json
{
  "type": "match_pairs",
  "question_id": "q_007",
  "instruction": "Match the continents with their capitals",
  "pairs": [
    {
      "id": "pair_1",
      "left": "India",
      "right": "New Delhi"
    },
    {
      "id": "pair_2",
      "left": "France",
      "right": "Paris"
    }
  ],
  "difficulty": "easy",
  "concept_tested": "Geography"
}
```

**Expected Answer:** Array of matched pair IDs  
**Example:** `["pair_1", "pair_2"]` (in correct order)

---

## Data Models

### Session Status

```
enum SessionStatus:
  - "not_started" - Session created but not yet started
  - "in_progress" - Session is active
  - "completed" - Session finished
  - "paused" - Session temporarily paused
```

### Current Phase

```
enum CurrentPhase:
  - "diagnostic" - Taking diagnostic assessment
  - "planning" - Study plan being generated
  - "teaching" - Learning concepts
  - "wrap_up" - Session conclusion
  - "completed" - Session finished
```

### Learning Style

```
enum LearningStyle:
  - "examples" - Learn through examples
  - "stories" - Learn through storytelling
  - "visual" - Learn through visual aids
  - "practice" - Learn through practice problems
```

### Difficulty Level

```
enum Difficulty:
  - "easy" - Basic level
  - "medium" - Intermediate level
  - "hard" - Advanced level
```

### UI Actions

The `next_action` field in feedback tells frontend what to do:

```
- "next_question" - Show next question
- "retry" - Allow student to retry
- "hint" - Suggest asking for hint
- "next_concept" - Move to next concept
- "reteach" - Show reteaching content
- "end_session" - End the session
```

---

## Integration Guide

### 1. Frontend Setup

```javascript
// Base configuration
const API_BASE_URL = "http://localhost:8000";

// Helper function for API calls
async function apiCall(endpoint, method = "GET", body = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
  return response.json();
}
```

---

### 2. Session Creation Flow

```javascript
// Create a session
async function createSession(studentData) {
  const response = await apiCall("/session/create", "POST", {
    student_id: studentData.id,
    student_name: studentData.name,
    class_grade: studentData.grade,
    board: "CBSE",
    subject: studentData.subject,
    chapter: studentData.chapter,
    learning_style: "examples",
    pace: "medium",
  });

  if (response.success) {
    return response.session_id;
  } else {
    console.error("Failed to create session", response);
  }
}
```

---

### 3. Diagnostic Phase

```javascript
// Start diagnostic
async function startDiagnostic(sessionId) {
  const response = await apiCall(
    `/chat/start-diagnostic?session_id=${sessionId}`,
    "POST"
  );
  return response;
}

// Submit diagnostic answer
async function submitDiagnosticAnswer(sessionId, questionId, answer) {
  const response = await apiCall(
    `/chat/submit-diagnostic-answer?session_id=${sessionId}&question_id=${questionId}&answer=${answer}`,
    "POST"
  );
  return response;
}
```

---

### 4. Teaching Phase

```javascript
// Start teaching
async function startTeaching(sessionId) {
  const response = await apiCall(
    `/chat/start-teaching?session_id=${sessionId}`,
    "POST"
  );
  return response;
}

// Submit answer
async function submitAnswer(sessionId, questionId, questionType, answer) {
  const response = await apiCall("/chat/submit-answer", "POST", {
    session_id: sessionId,
    question_id: questionId,
    question_type: questionType,
    answer: answer,
    time_taken_seconds: 30,
  });
  return response;
}
```

---

### 5. UI Rendering Logic

```javascript
// Handle different display types
function renderDisplay(displayItems) {
  displayItems.forEach((item) => {
    switch (item.type) {
      case "message":
        renderMessage(item.content, item.is_encouragement);
        break;

      case "question":
        renderQuestion(item.question);
        break;

      case "feedback":
        renderFeedback(
          item.is_correct,
          item.message,
          item.xp_earned,
          item.next_action
        );
        break;

      case "study_plan":
        renderStudyPlan(item.concepts, item.estimated_minutes);
        break;

      case "celebration":
        renderCelebration(item.title, item.message, item.xp_earned);
        break;

      case "session_summary":
        renderSessionSummary(item);
        break;

      default:
        console.warn("Unknown display type:", item.type);
    }
  });
}
```

---

### 6. Handling Different Question Types

```javascript
// Render question based on type
function renderQuestion(question) {
  switch (question.type) {
    case "multiple_choice":
      renderMultipleChoice(question);
      break;

    case "true_false":
      renderTrueFalse(question);
      break;

    case "numeric":
      renderNumericInput(question);
      break;

    case "fill_blank":
      renderFillBlank(question);
      break;

    case "short_answer":
      renderTextArea(question);
      break;

    case "equation":
      renderEquationSolver(question);
      break;

    case "match_pairs":
      renderMatchPairs(question);
      break;
  }
}

// Example: Get answer based on question type
function getAnswerByType(questionType, userInput) {
  switch (questionType) {
    case "numeric":
    case "equation":
      return parseFloat(userInput);

    case "true_false":
      return userInput.toLowerCase() === "true" ? "true" : "false";

    case "multiple_choice":
      return userInput; // Option ID string

    case "match_pairs":
      return userInput; // Array of pair IDs

    default:
      return userInput; // String for fill_blank, short_answer
  }
}
```

---

### 7. Error Handling

```javascript
async function apiCallWithErrorHandling(endpoint, method = "GET", body = null) {
  try {
    const response = await apiCall(endpoint, method, body);

    if (response.status === 404) {
      showError("Session not found. Please create a new session.");
    } else if (response.status === 500) {
      showError("Server error. Please try again later.");
    } else if (response.status === 400) {
      showError("Invalid request format.");
    }

    return response;
  } catch (error) {
    console.error("API Error:", error);
    showError("Network error. Please check your connection.");
  }
}
```

---

## Code Examples

### Complete Learning Session Flow

```javascript
// Complete session flow example
async function runLearningSession(studentData) {
  // 1. Create session
  const sessionId = await createSession(studentData);
  console.log("Session created:", sessionId);

  // 2. Start diagnostic
  const diagnosticStart = await startDiagnostic(sessionId);
  renderDisplay(diagnosticStart.display);

  // 3. Answer diagnostic questions (loop)
  let diagnosticDone = false;
  while (!diagnosticDone) {
    const answer = await getUserAnswer();
    const diagnosticResult = await submitDiagnosticAnswer(
      sessionId,
      diagnosticStart.question.question_id,
      answer
    );
    renderDisplay(diagnosticResult.display);
    diagnosticDone = diagnosticResult.current_phase !== "diagnostic";
  }

  // 4. Generate study plan
  const planResponse = await apiCall(
    `/chat/generate-plan?session_id=${sessionId}`,
    "POST"
  );
  renderDisplay(planResponse.display);

  // 5. Teaching loop
  let sessionActive = true;
  while (sessionActive) {
    const teachingStart = await startTeaching(sessionId);
    renderDisplay(teachingStart.display);

    const question = teachingStart.display.find((d) => d.type === "question");
    if (!question) break;

    const answer = await getUserAnswer();
    const feedback = await submitAnswer(
      sessionId,
      question.question.question_id,
      question.question.type,
      answer
    );

    renderDisplay(feedback.display);
    renderProgress(feedback.progress);

    sessionActive = feedback.current_phase === "teaching";
  }

  // 6. End session
  const endResponse = await apiCall(
    `/chat/end-session?session_id=${sessionId}`,
    "POST"
  );
  renderDisplay(endResponse.display);
}
```

---

## Testing the API

### Using cURL

```bash
# Create a session
curl -X POST http://localhost:8000/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_001",
    "student_name": "Raj Kumar",
    "class_grade": 8,
    "board": "CBSE",
    "subject": "Mathematics",
    "chapter": "Fractions and Decimals",
    "learning_style": "examples",
    "pace": "medium"
  }'

# Get session details
curl http://localhost:8000/session/{session_id}

# Start diagnostic
curl -X POST "http://localhost:8000/chat/start-diagnostic?session_id={session_id}"
```

---

## Performance Considerations

- **Response Time:** Each API call typically responds in < 3 seconds
- **LLM Latency:** First response in diagnostic/teaching phases may take 2-5 seconds due to LLM processing
- **Concurrent Sessions:** Backend handles multiple concurrent sessions efficiently
- **Session Persistence:** All session data automatically saved to disk

---

## Support & Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS Errors | Backend is configured with CORS middleware, should work from any origin |
| 404 on session | Verify session ID is correct and was created successfully |
| LLM Timeouts | Check GROQ_API_KEY is valid and Groq service is accessible |
| Invalid Question JSON | Ensure question types match defined schema |

### Debug Mode

Enable detailed logging by checking `/data/sessions/` directory:
```bash
ls /data/sessions/  # See all session JSON files
cat /data/sessions/session_{id}.json  # View full session state
```

---

## Changelog

### Version 1.0.0 (January 2026)

- ✅ Complete API implementation
- ✅ All 7 question types
- ✅ Diagnostic assessment with adaptive difficulty
- ✅ Personalized study plans
- ✅ Real-time progress tracking
- ✅ XP and gamification system
- ✅ Session persistence
- ✅ Multi-phase learning flow

---

## License

This API is part of the AI Tutor Backend project. All documentation and code are proprietary.

---

**Last Updated:** January 7, 2026  
**API Status:** Production Ready ✅
