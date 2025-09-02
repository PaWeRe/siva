"""
Main API Router for SIVA - Combines old and new endpoints for seamless migration.
This provides a unified API interface while we migrate from old to new structure.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from siva.api_service.dashboard_api import router as dashboard_router


# Create main router
main_router = APIRouter()

# Include dashboard API
main_router.include_router(dashboard_router, prefix="/dashboard")


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
            "dashboard": {
                "simulations": "/api/dashboard/simulations/recent",
                "run_simulation": "/api/dashboard/simulations/run",
                "learning_summary": "/api/dashboard/learning/summary",
                "domains": "/api/dashboard/domains",
                "health": "/api/dashboard/health",
            }
        },
        "message": "Clean tau2-bench architecture - no legacy dependencies",
    }


@main_router.get("/status")
async def status():
    """Get current system status."""
    return {
        "status": "active",
        "architecture": "tau2-bench",
        "components": {
            "dashboard_api": "active",
            "learning_system": "active",
            "simulation_framework": "active",
        },
        "message": "Clean, modern architecture built on tau2-bench",
    }
