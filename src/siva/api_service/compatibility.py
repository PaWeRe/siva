"""
Compatibility layer for seamless integration between old and new API structures.
This ensures that existing clients continue to work while we migrate to the new architecture.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from siva.bridge import get_bridge, SIVABridge
from siva.api_service.chat_service import ChatService, get_chat_service


class CompatibilityLayer:
    """Compatibility layer that bridges old and new API structures."""

    def __init__(self, bridge: SIVABridge):
        self.bridge = bridge
        self.chat_service = ChatService(bridge)

    async def process_legacy_chat(
        self, session_id: str, message: str
    ) -> Dict[str, Any]:
        """
        Process chat using legacy format for backward compatibility.

        Args:
            session_id: Session identifier
            message: User message

        Returns:
            Legacy format response
        """
        # Use legacy processor to maintain exact same behavior
        reply, end_call, escalation_info = await self.chat_service.process_message(
            session_id, message, use_legacy=True
        )

        # Format response in legacy format
        response = {
            "reply": reply,
            "end_call": end_call,
            "escalation_info": escalation_info,
            "session_id": session_id,
        }

        # Save conversation if ended (legacy behavior)
        if end_call:
            session_data = await self.chat_service.get_session_data(session_id)
            if session_data:
                conversation_data = {
                    "messages": session_data.get("messages", []),
                    "data": session_data.get("data", {}),
                    "escalation_data": session_data.get("escalation_data", {}),
                }
                await self.chat_service.save_conversation(session_id, conversation_data)

        return response

    async def get_legacy_session_data(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session data in legacy format."""
        return await self.chat_service.get_session_data(session_id)


def get_compatibility_layer(
    bridge: SIVABridge = Depends(get_bridge),
) -> CompatibilityLayer:
    """Dependency to get compatibility layer instance."""
    return CompatibilityLayer(bridge)


# Create compatibility router
compatibility_router = APIRouter(prefix="/compatibility", tags=["compatibility"])


@compatibility_router.post("/chat")
async def legacy_chat_compatibility(
    session_id: str,
    message: str,
    compatibility_layer: CompatibilityLayer = Depends(get_compatibility_layer),
):
    """
    Legacy chat endpoint compatibility layer.
    This ensures existing clients continue to work during migration.
    """
    try:
        response = await compatibility_layer.process_legacy_chat(session_id, message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legacy chat error: {str(e)}")


@compatibility_router.get("/session/{session_id}")
async def legacy_session_compatibility(
    session_id: str,
    compatibility_layer: CompatibilityLayer = Depends(get_compatibility_layer),
):
    """Legacy session endpoint compatibility layer."""
    try:
        session_data = await compatibility_layer.get_legacy_session_data(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"session_id": session_id, "data": session_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legacy session error: {str(e)}")


@compatibility_router.get("/migration-info")
async def migration_info():
    """Get migration information for clients."""
    return {
        "migration_phase": 5,
        "phase_name": "API Layer Migration",
        "status": "in_progress",
        "recommendations": {
            "clients": "Continue using existing endpoints - they will be maintained during migration",
            "new_features": "Use /api/v2 endpoints for new tau2-bench features",
            "timeline": "Full migration expected in Phase 9",
        },
        "endpoint_mapping": {
            "legacy": {"chat": "/chat", "session": "/session/{session_id}"},
            "new": {
                "chat": "/api/v2/chat",
                "chat_simulate": "/api/v2/chat/simulate",
                "session": "/api/v2/session/{session_id}",
            },
            "compatibility": {
                "chat": "/api/compatibility/chat",
                "session": "/api/compatibility/session/{session_id}",
            },
        },
    }
