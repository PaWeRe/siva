# Copyright Sierra
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class PatientData:
    """Patient information collected during intake."""

    full_name: Optional[str] = None
    birthday: Optional[str] = None
    prescriptions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    reason_for_visit: Optional[str] = None
    symptoms: Dict[str, Any] = field(default_factory=dict)
    routing: Optional[Dict[str, Any]] = None


@dataclass
class SessionState:
    """Session state for patient intake."""

    session_id: str
    mode: str = "patient_intake"
    phase: str = "basic_intake"  # basic_intake -> detailed_symptoms -> routing
    messages: List[Dict[str, Any]] = field(default_factory=list)
    data: PatientData = field(default_factory=PatientData)
    escalation_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    completed: bool = False


@dataclass
class PatientIntakeDB:
    """Database for patient intake domain."""

    sessions: Dict[str, SessionState] = field(default_factory=dict)

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def create_session(self, session_id: str) -> SessionState:
        """Create a new session."""
        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def update_session(self, session_id: str, **kwargs) -> SessionState:
        """Update session data."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_activity = datetime.now()
        return session

    def save_conversation(self, session_id: str, conversation_data: Dict[str, Any]):
        """Save completed conversation."""
        session = self.get_session(session_id)
        if session:
            session.completed = True
            session.data = conversation_data.get("data", session.data)
            session.escalation_data = conversation_data.get("escalation_data", {})
            session.messages = conversation_data.get("messages", session.messages)
