"""
Test script for AI Tutor Backend

Run this after starting the server to test the full flow.
Usage: python test_api.py
"""
import requests
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing health endpoint...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {resp.json()}")
    return resp.json()["status"] == "healthy"


def test_full_flow():
    """Test complete tutoring flow"""
    
    print("\n" + "="*60)
    print("🎓 AI TUTOR API TEST")
    print("="*60)
    
    # 1. Create Session
    print("\n📝 Step 1: Creating session...")
    resp = requests.post(f"{BASE_URL}/session/create", json={
        "student_id": "test_student_001",
        "student_name": "Arjun",
        "class_grade": 8,
        "board": "CBSE",
        "subject": "Mathematics",
        "chapter": "Linear Equations",
        "topic": "Solving linear equations",
        "interests": ["cricket", "video games"],
        "learning_style": "examples",
        "pace": "medium"
    })
    
    if resp.status_code != 200:
        print(f"   ❌ Failed: {resp.text}")
        return False
    
    data = resp.json()
    session_id = data["session_id"]
    print(f"   ✅ Session created: {session_id}")
    print(f"   Message: {data['message']}")
    
    # 2. Start Diagnostic
    print("\n📊 Step 2: Starting diagnostic assessment...")
    resp = requests.post(f"{BASE_URL}/chat/start-diagnostic?session_id={session_id}")
    
    if resp.status_code != 200:
        print(f"   ❌ Failed: {resp.text}")
        return False
    
    data = resp.json()
    print(f"   ✅ Phase: {data['current_phase']}")
    
    for item in data.get("display", []):
        if item.get("type") == "message":
            print(f"   💬 AI: {item['content'][:100]}...")
        elif item.get("type") == "question":
            q = item.get("question", {})
            print(f"   ❓ Question: {q.get('question_text', 'N/A')[:80]}...")
            print(f"      Type: {q.get('type')}")
    
    # 3. Submit a diagnostic answer
    print("\n✍️  Step 3: Submitting diagnostic answer...")
    
    # Find the question from previous response
    question_id = None
    for item in data.get("display", []):
        if item.get("type") == "question":
            question_id = item.get("question", {}).get("question_id", "diag_q1")
            break
    
    resp = requests.post(
        f"{BASE_URL}/chat/submit-diagnostic-answer",
        params={
            "session_id": session_id,
            "question_id": question_id or "diag_q1",
            "answer": "4"  # Sample answer
        }
    )
    
    if resp.status_code != 200:
        print(f"   ❌ Failed: {resp.text}")
        return False
    
    data = resp.json()
    print(f"   ✅ Response received")
    
    for item in data.get("display", []):
        if item.get("type") == "feedback":
            print(f"   📝 Correct: {item.get('is_correct')}")
            print(f"   💬 Feedback: {item.get('message', '')[:80]}...")
    
    # 4. Get session progress
    print("\n📈 Step 4: Checking progress...")
    resp = requests.get(f"{BASE_URL}/session/{session_id}/progress")
    
    if resp.status_code != 200:
        print(f"   ❌ Failed: {resp.text}")
        return False
    
    progress = resp.json().get("progress", {})
    print(f"   ✅ Questions attempted: {progress.get('questions_attempted', 0)}")
    print(f"   ✅ Questions correct: {progress.get('questions_correct', 0)}")
    print(f"   ✅ Accuracy: {progress.get('accuracy', 0)*100:.0f}%")
    
    # 5. Cleanup
    print("\n🧹 Step 5: Cleaning up...")
    resp = requests.delete(f"{BASE_URL}/session/{session_id}")
    print(f"   ✅ Session deleted")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    return True


def test_without_api_key():
    """Test what happens without API key"""
    print("\n⚠️  Note: Full flow requires GROQ_API_KEY to be set")
    print("   Without it, LLM calls will fail but API structure works")


if __name__ == "__main__":
    print("\n🚀 AI Tutor Backend Test Suite")
    print("-" * 40)
    
    # Check if server is running
    try:
        if test_health():
            print("✅ Server is healthy!")
            test_full_flow()
        else:
            print("❌ Server health check failed")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   $ python main.py")
        print("\n   Or:")
        print("   $ uvicorn main:app --reload")
