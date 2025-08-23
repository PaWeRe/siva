"""
Main API Router for SIVA - Combines old and new endpoints for seamless migration.
This provides a unified API interface while we migrate from old to new structure.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from siva.api_service.chat_service import router as chat_router
from siva.api_service.simulation_service import router as simulation_router
from siva.api_service.compatibility import compatibility_router


# Create main router
main_router = APIRouter()

# Include new API endpoints
main_router.include_router(chat_router, prefix="/v2")
main_router.include_router(simulation_router, prefix="/v2")

# Include compatibility layer
main_router.include_router(compatibility_router)


@main_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "tau2-bench",
        "message": "SIVA API is running with new tau2-bench architecture",
    }


@main_router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SIVA API",
        "version": "2.0.0",
        "description": "Self-Learning Voice Agent for Healthcare Intake",
        "architecture": "tau2-bench compatible",
        "endpoints": {
            "v2": {
                "chat": "/api/v2/chat",
                "chat_simulate": "/api/v2/chat/simulate",
                "session": "/api/v2/session/{session_id}",
                "simulation": "/api/v2/simulation",
            },
            "compatibility": {
                "chat": "/api/compatibility/chat",
                "session": "/api/compatibility/session/{session_id}",
                "migration_info": "/api/compatibility/migration-info",
            },
            "legacy": {"chat": "/chat", "embedding_viz": "/api/embedding-viz"},
        },
        "websockets": {"tts": "/ws/tts", "stt": "/ws/stt"},
    }


@main_router.get("/migration-status")
async def migration_status():
    """Get current migration status."""
    return {
        "phase": 5,
        "phase_name": "API Layer Migration",
        "completed_phases": [
            "Phase 1: Foundation with bridge pattern",
            "Phase 2: Core logic migration to tau2-bench tools and environment",
            "Phase 3: Agent integration with healthcare agent and user simulator",
            "Phase 4: Configuration migration",
        ],
        "current_status": {
            "old_api": "Active and functional",
            "new_api": "Active and functional",
            "compatibility_layer": "Active and functional",
            "migration_progress": "50%",
            "backward_compatibility": "Maintained",
        },
        "next_phases": [
            "Phase 6: Core Logic Migration",
            "Phase 7: Schema Migration",
            "Phase 8: Testing and Validation",
            "Phase 9: Cleanup and Removal",
        ],
    }
