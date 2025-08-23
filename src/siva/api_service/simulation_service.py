# Copyright Sierra
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from siva.config import API_PORT
from siva.data_model.simulation import Results, RunConfig
from siva.registry import RegistryInfo
from siva.run import get_options, load_tasks, run_domain

from .data_model import GetTasksRequest, GetTasksResponse

# Create router instead of FastAPI app
router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"app_health": "OK"}


@router.post("/get_options")
async def get_options_api() -> RegistryInfo:
    """Get available options for simulation."""
    try:
        return get_options()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_tasks")
async def get_tasks_api(
    request: GetTasksRequest,
) -> GetTasksResponse:
    """Get tasks for a specific domain."""
    try:
        tasks = load_tasks(request.domain)
        return GetTasksResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run_domain")
async def run_domain_api(
    request: RunConfig,
) -> Results:
    """Run a domain simulation."""
    try:
        results = run_domain(request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
