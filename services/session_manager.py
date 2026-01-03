"""
Session Manager - Handles JSON session file operations
"""
import json
import os
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import shutil

from config import settings
from models import (
    Session, SessionStatus, CurrentPhase, StudentSnapshot,
    LearningPreferences, SessionMeta, Message
)


class SessionManager:
    """Manages session JSON files"""
    
    def __init__(self):
        self.sessions_dir = Path(settings.SESSIONS_DIR)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get path to session JSON file"""
        return self.sessions_dir / f"session_{session_id}.json"
    
    def _serialize_session(self, session: Session) -> dict:
        """Convert session to JSON-serializable dict"""
        return json.loads(session.model_dump_json())
    
    def _deserialize_session(self, data: dict) -> Session:
        """Convert dict back to Session model"""
        return Session.model_validate(data)
    
    def create_session(
        self,
        student_id: str,
        student_name: str,
        class_grade: int,
        board: str,
        subject: str,
        chapter: str,
        topic: str,
        interests: List[str] = None,
        learning_style: str = "examples",
        pace: str = "medium"
    ) -> Session:
        """Create a new session"""
        
        # Create student snapshot
        student = StudentSnapshot(
            student_id=student_id,
            name=student_name,
            class_grade=class_grade,
            board=board,
            preferences=LearningPreferences(
                learning_style=learning_style,
                pace=pace,
                encouragement_level="high"
            ),
            interests=interests or [],
            known_weaknesses=[]
        )
        
        # Create session metadata
        meta = SessionMeta(
            subject=subject,
            class_grade=class_grade,
            board=board,
            chapter=chapter,
            chapter_number=1,  # Default
            topic_requested=topic or chapter,
            session_type="learning",
            estimated_duration_minutes=30
        )
        
        # Create session
        session = Session(
            student_id=student_id,
            student=student,
            meta=meta,
            current_phase=CurrentPhase.TOPIC_SELECTION
        )
        
        # Save to file
        self.save_session(session)
        
        return session
    
    def save_session(self, session: Session) -> bool:
        """Save session to JSON file (atomic write)"""
        try:
            session.update_timestamp()
            
            file_path = self._get_session_path(session.session_id)
            temp_path = file_path.with_suffix('.tmp')
            
            # Write to temp file first
            with open(temp_path, 'w') as f:
                json.dump(self._serialize_session(session), f, indent=2, default=str)
            
            # Atomic rename
            shutil.move(str(temp_path), str(file_path))
            
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session from JSON file"""
        try:
            file_path = self._get_session_path(session_id)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return self._deserialize_session(data)
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return self._get_session_path(session_id).exists()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file"""
        try:
            file_path = self._get_session_path(session_id)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def list_sessions(self, student_id: Optional[str] = None) -> List[dict]:
        """List all sessions, optionally filtered by student"""
        sessions = []
        
        for file_path in self.sessions_dir.glob("session_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if student_id is None or data.get('student_id') == student_id:
                    sessions.append({
                        'session_id': data.get('session_id'),
                        'student_id': data.get('student_id'),
                        'subject': data.get('meta', {}).get('subject'),
                        'chapter': data.get('meta', {}).get('chapter'),
                        'status': data.get('status'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'current_phase': data.get('current_phase')
                    })
            except Exception as e:
                print(f"Error reading session file {file_path}: {e}")
        
        return sorted(sessions, key=lambda x: x.get('updated_at', ''), reverse=True)
    
    def add_message(self, session: Session, role: str, content: str) -> Session:
        """Add a message to conversation context"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        session.conversation.recent_messages.append(message)
        session.conversation.total_messages += 1
        
        # Keep only last 10 messages for context
        if len(session.conversation.recent_messages) > 10:
            session.conversation.recent_messages = session.conversation.recent_messages[-10:]
        
        return session
    
    def update_phase(self, session: Session, phase: CurrentPhase) -> Session:
        """Update session phase"""
        session.current_phase = phase
        session.update_timestamp()
        return session
    
    def update_stats(
        self,
        session: Session,
        questions_attempted: int = 0,
        questions_correct: int = 0,
        hints_used: int = 0,
        xp_earned: int = 0
    ) -> Session:
        """Update session statistics"""
        session.stats.questions_attempted += questions_attempted
        session.stats.questions_correct += questions_correct
        session.stats.hints_used += hints_used
        session.stats.xp_earned += xp_earned
        
        # Recalculate accuracy
        if session.stats.questions_attempted > 0:
            session.stats.accuracy_rate = (
                session.stats.questions_correct / session.stats.questions_attempted
            )
        
        return session


# Singleton instance
session_manager = SessionManager()
