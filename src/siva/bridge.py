"""
Bridge module to connect your existing SIVA API with the new tau2-bench structure.
This allows for gradual migration without breaking the current system.
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Add the parent directory to the path to import your existing modules
sys.path.append(str(Path(__file__).parent.parent))

from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from core.data_manager import DataManager
from core.processor import UnifiedProcessor
from openai import OpenAI

from .domains.patient_intake.environment import PatientIntakeEnvironment
from .domains.patient_intake.tools import PatientIntakeTools
from .domains.patient_intake.data_model import PatientIntakeDB


class SIVABridge:
    """
    Bridge class that connects your existing SIVA components with the new tau2-bench structure.
    This allows for gradual migration while keeping your current API functional.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_judge: LLMJudge,
        data_manager: DataManager,
        openai_client: OpenAI,
        current_mode: str = "patient_intake",
    ):
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.data_manager = data_manager
        self.openai_client = openai_client
        self.current_mode = current_mode

        # Initialize tau2-bench components
        self.patient_intake_db = PatientIntakeDB()
        self.patient_intake_tools = PatientIntakeTools()

        # Create environment with your existing components
        self.environment = PatientIntakeEnvironment(
            domain_name="patient_intake",
            policy="Patient intake policy placeholder",
            tools=self.patient_intake_tools,
            user_tools=None,  # We'll add this later
            vector_store=vector_store,
            llm_judge=llm_judge,
            data_manager=data_manager,
        )

    def create_legacy_processor(self, session: Dict[str, Any]) -> UnifiedProcessor:
        """
        Create a legacy processor that works with your existing API.
        This maintains backward compatibility while we migrate.
        """
        return UnifiedProcessor(
            session=session,
            vector_store=self.vector_store,
            llm_judge=self.llm_judge,
            openai_client=self.openai_client,
            retrieval_threshold=3,  # Default value
            current_mode=self.current_mode,
        )

    def process_message_legacy(
        self, session_id: str, message: str
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Process a message using your existing processor logic.
        This is the current implementation that your API uses.
        """
        # Get or create session
        session = self._get_or_create_session(session_id)

        # Use your existing processor
        processor = self.create_legacy_processor(session)

        # Process the message
        reply, end_call, escalation_info = processor.next_prompt(message)

        # Update session
        session.update(
            {
                "messages": processor.get_history(),
                "data": processor.get_data(),
                "escalation_data": processor.get_escalation_data(),
            }
        )

        return reply, end_call, escalation_info

    def process_message_tau2(
        self, session_id: str, message: str
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Process a message using the new tau2-bench structure.
        This is the future implementation we're migrating toward.
        """
        # For now, this is a placeholder that calls the legacy method
        # In future commits, this will be replaced with actual tau2-bench logic
        return self.process_message_legacy(session_id, message)

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get or create a session for the given session ID.
        This maintains compatibility with your existing session management.
        """
        # For now, we'll use a simple in-memory session store
        # In the future, this will use the tau2-bench session management
        if not hasattr(self, "_sessions"):
            self._sessions = {}

        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "mode": self.current_mode,
                "phase": "basic_intake",
                "messages": [],
                "data": {},
                "escalation_data": {},
            }

        return self._sessions[session_id]

    def save_conversation(self, session_id: str, conversation_data: Dict[str, Any]):
        """
        Save a completed conversation.
        This bridges your existing data manager with the new structure.
        """
        # Save using your existing data manager
        self.data_manager.save_conversation(session_id, conversation_data)

        # Also save to the new tau2-bench database
        self.patient_intake_db.save_conversation(session_id, conversation_data)

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data from the bridge.
        """
        return self._get_or_create_session(session_id)


# Global bridge instance (will be initialized in main.py)
siva_bridge: Optional[SIVABridge] = None


def initialize_bridge(
    vector_store: VectorStore,
    llm_judge: LLMJudge,
    data_manager: DataManager,
    openai_client: OpenAI,
    current_mode: str = "patient_intake",
) -> SIVABridge:
    """
    Initialize the SIVA bridge with your existing components.
    """
    global siva_bridge
    siva_bridge = SIVABridge(
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
        openai_client=openai_client,
        current_mode=current_mode,
    )
    return siva_bridge


def get_bridge() -> SIVABridge:
    """
    Get the global bridge instance.
    """
    if siva_bridge is None:
        raise RuntimeError(
            "SIVA bridge not initialized. Call initialize_bridge() first."
        )
    return siva_bridge
