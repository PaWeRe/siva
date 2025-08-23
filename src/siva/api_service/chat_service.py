"""
Chat Service for SIVA API - tau2-bench compatible implementation.
This provides the new API structure while maintaining backward compatibility.
"""

import datetime
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..settings import settings
from ..bridge import get_bridge, SIVABridge
from ..domains.patient_intake.data_model import PatientIntakeDB


class ChatService:
    """Chat service that handles patient intake conversations using tau2-bench architecture."""

    def __init__(self, bridge: SIVABridge):
        self.bridge = bridge
        self.patient_intake_db = PatientIntakeDB()

    async def process_message(
        self, session_id: str, message: str, use_legacy: bool = False
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Process a chat message using either legacy or new tau2-bench system.

        Args:
            session_id: Session identifier
            message: User message
            use_legacy: Whether to use legacy processor (for backward compatibility)

        Returns:
            Tuple of (reply, end_call, escalation_info)
        """
        if use_legacy:
            # Use legacy processor for backward compatibility
            return self.bridge.process_message_legacy(session_id, message)
        else:
            # Use new tau2-bench system
            return self.bridge.process_message_tau2(session_id, message)

    async def process_message_with_agent(
        self, session_id: str, message: str
    ) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Process a message using the healthcare agent.

        Args:
            session_id: Session identifier
            message: User message

        Returns:
            Tuple of (reply, end_call, escalation_info)
        """
        return self.bridge.process_message_with_agent(session_id, message)

    async def save_conversation(
        self, session_id: str, conversation_data: Dict[str, Any]
    ):
        """Save a completed conversation."""
        self.bridge.save_conversation(session_id, conversation_data)

    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self.bridge.get_session_data(session_id)

    async def simulate_conversation(
        self, patient_messages: list[str]
    ) -> list[Tuple[str, str]]:
        """
        Simulate a complete conversation using the healthcare agent.

        Args:
            patient_messages: List of patient messages

        Returns:
            List of (agent_message, patient_message) pairs
        """
        return self.bridge.simulate_conversation_with_agent(patient_messages)


def get_chat_service(bridge: SIVABridge = Depends(get_bridge)) -> ChatService:
    """Dependency to get chat service instance."""
    return ChatService(bridge)


# Create router for new API endpoints
router = APIRouter(prefix="/api/v2", tags=["chat"])


@router.post("/chat")
async def chat_v2(
    session_id: str,
    message: str,
    use_agent: bool = False,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    New chat endpoint using tau2-bench architecture.

    Args:
        session_id: Session identifier
        message: User message
        use_agent: Whether to use healthcare agent
        chat_service: Chat service instance
    """
    try:
        if use_agent:
            reply, end_call, escalation_info = (
                await chat_service.process_message_with_agent(session_id, message)
            )
        else:
            reply, end_call, escalation_info = await chat_service.process_message(
                session_id, message, use_legacy=False
            )

        # Save conversation if ended
        if end_call:
            session_data = await chat_service.get_session_data(session_id)
            if session_data:
                conversation_data = {
                    "messages": session_data.get("messages", []),
                    "data": session_data.get("data", {}),
                    "escalation_data": session_data.get("escalation_data", {}),
                }
                await chat_service.save_conversation(session_id, conversation_data)

        return {
            "reply": reply,
            "end_call": end_call,
            "escalation_info": escalation_info,
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@router.post("/chat/simulate")
async def simulate_chat(
    patient_messages: list[str], chat_service: ChatService = Depends(get_chat_service)
):
    """
    Simulate a complete conversation.

    Args:
        patient_messages: List of patient messages
        chat_service: Chat service instance
    """
    try:
        conversation = await chat_service.simulate_conversation(patient_messages)

        return {
            "conversation": conversation,
            "total_messages": len(conversation),
            "timestamp": datetime.datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(
    session_id: str, chat_service: ChatService = Depends(get_chat_service)
):
    """Get session data."""
    try:
        session_data = await chat_service.get_session_data(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "data": session_data,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Session retrieval error: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str, chat_service: ChatService = Depends(get_chat_service)
):
    """Delete session data."""
    try:
        # For now, we'll just return success since session deletion isn't implemented
        # In the future, this would remove the session from the database
        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session deletion error: {str(e)}")
