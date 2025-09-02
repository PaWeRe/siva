#!/usr/bin/env python3
"""
SIVA tau2-bench Backend Server

This server exposes tau2-bench functionality via HTTP endpoints,
allowing the Next.js dashboard to interact with simulations.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import threading
from pathlib import Path
import json
import uuid
from datetime import datetime

# Import tau2-bench components
from siva.run import run_domain
from siva.data_model.simulation import RunConfig, Results
from siva.scripts.view_simulations import get_available_simulations
from siva.learning.integration import LearningIntegration
from siva.registry import registry

# Create FastAPI app
app = FastAPI(
    title="SIVA tau2-bench Backend",
    description="Backend server for SIVA using tau2-bench simulation framework",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize learning integration
learning_integration = LearningIntegration()

# Store running simulations
running_simulations: Dict[str, Dict[str, Any]] = {}


# Pydantic models
class SimulationRequest(BaseModel):
    domain: str
    agent: str
    user: str
    num_tasks: int = 1
    max_steps: int = 50
    max_errors: int = 10
    seed: Optional[int] = None
    agent_llm: str = "gpt-4.1"
    user_llm: str = "gpt-4.1"
    num_trials: int = 1


class SimulationStatus(BaseModel):
    id: str
    status: str
    progress: float
    message: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SIVA tau2-bench Backend",
        "version": "2.0.0",
        "description": "Backend server for SIVA using tau2-bench simulation framework",
        "architecture": "tau2-bench compatible",
        "endpoints": {
            "simulations": {
                "run": "/api/simulations/run",
                "status": "/api/simulations/status/{simulation_id}",
                "recent": "/api/simulations/recent",
                "list": "/api/simulations/list",
            },
            "domains": {
                "list": "/api/domains",
                "info": "/api/domains/{domain_name}",
                "docs": "/api/domains/{domain_name}/docs",
            },
            "learning": {
                "summary": "/api/learning/summary",
                "export": "/api/learning/export",
            },
            "health": "/api/health",
        },
        "dashboard_url": "http://localhost:3000",
    }


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SIVA tau2-bench Backend",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


# Domain information
@app.get("/api/domains")
async def list_domains():
    """List available domains."""
    try:
        info = registry.get_info()
        return {
            "domains": info.domains,
            "agents": info.agents,
            "users": info.users,
            "task_sets": info.task_sets,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching domain info: {str(e)}"
        )


@app.get("/api/domains/{domain_name}")
async def get_domain_info(domain_name: str):
    """Get information about a specific domain."""
    try:
        info = registry.get_info()
        if domain_name not in info.domains:
            raise HTTPException(
                status_code=404, detail=f"Domain '{domain_name}' not found"
            )

        return {
            "domain": domain_name,
            "available_agents": info.agents,
            "available_users": info.users,
            "task_sets": [ts for ts in info.task_sets if domain_name in ts],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching domain info: {str(e)}"
        )


# Simulation management
@app.post("/api/simulations/run")
async def run_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """Run a new simulation in the background."""
    try:
        # Generate unique simulation ID
        simulation_id = str(uuid.uuid4())

        # Create run configuration
        config = RunConfig(
            domain=request.domain,
            agent=request.agent,
            user=request.user,
            num_tasks=request.num_tasks,
            max_steps=request.max_steps,
            max_errors=request.max_errors,
            seed=request.seed,
            agent_llm=request.agent_llm,
            user_llm=request.user_llm,
            num_trials=request.num_trials,
        )

        # Store simulation info
        running_simulations[simulation_id] = {
            "id": simulation_id,
            "status": "running",
            "progress": 0.0,
            "message": "Simulation started",
            "config": config.dict(),
            "start_time": datetime.now().isoformat(),
            "results": None,
            "error": None,
        }

        # Run simulation in background
        background_tasks.add_task(run_simulation_background, simulation_id, config)

        return {
            "simulation_id": simulation_id,
            "message": "Simulation started",
            "status": "running",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting simulation: {str(e)}"
        )


async def run_simulation_background(simulation_id: str, config: RunConfig):
    """Run simulation in background thread."""
    try:
        # Update status
        running_simulations[simulation_id]["status"] = "running"
        running_simulations[simulation_id]["progress"] = 25.0
        running_simulations[simulation_id]["message"] = "Running simulation..."

        # Run the simulation
        results = run_domain(config)

        # Update status with results
        running_simulations[simulation_id]["status"] = "completed"
        running_simulations[simulation_id]["progress"] = 100.0
        running_simulations[simulation_id][
            "message"
        ] = "Simulation completed successfully"
        running_simulations[simulation_id]["results"] = {
            "total_tasks": len(results.simulations),
            "successful_tasks": sum(
                1
                for r in results.simulations
                if r.reward_info and r.reward_info.reward > 0.5
            ),
            "total_cost": sum(
                (r.agent_cost or 0) + (r.user_cost or 0) for r in results.simulations
            ),
            "simulation_runs": [
                {
                    "id": str(r.id) if hasattr(r, "id") else str(hash(r)),
                    "task_id": r.task_id,
                    "duration": r.duration,
                    "termination_reason": r.termination_reason,
                    "agent_cost": r.agent_cost or 0.0,
                    "user_cost": r.user_cost or 0.0,
                    "reward": r.reward_info.reward if r.reward_info else 0.0,
                }
                for r in results.simulations
            ],
        }

        # Process for learning
        try:
            for sim_run in results.simulations:
                learning_integration.process_simulation_result(sim_run)
        except Exception as e:
            print(f"Learning integration failed: {e}")

    except Exception as e:
        running_simulations[simulation_id]["status"] = "failed"
        running_simulations[simulation_id]["error"] = str(e)
        running_simulations[simulation_id]["message"] = f"Simulation failed: {str(e)}"


@app.get("/api/simulations/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get status of a running or completed simulation."""
    if simulation_id not in running_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return SimulationStatus(**running_simulations[simulation_id])


@app.get("/api/simulations/recent")
async def get_recent_simulations(limit: int = 10):
    """Get recent simulation results."""
    try:
        # Get available simulation files
        sim_files = get_available_simulations()

        if not sim_files:
            return {"simulations": [], "total": 0}

        # Load the most recent simulation file
        latest_file = sim_files[-1]
        results = Results.load(latest_file)

        # Convert to API format
        simulations = []
        for sim in results.simulations[:limit]:
            simulations.append(
                {
                    "id": str(sim.id) if hasattr(sim, "id") else str(hash(sim)),
                    "task_id": sim.task_id,
                    "duration": sim.duration,
                    "termination_reason": sim.termination_reason,
                    "agent_cost": sim.agent_cost or 0.0,
                    "user_cost": sim.user_cost or 0.0,
                    "reward": sim.reward_info.reward if sim.reward_info else 0.0,
                    "action_checks": [
                        {
                            "name": check.name if hasattr(check, "name") else "unknown",
                            "reward": check.reward if hasattr(check, "reward") else 0.0,
                        }
                        for check in (
                            sim.reward_info.action_checks
                            if sim.reward_info
                            and hasattr(sim.reward_info, "action_checks")
                            else []
                        )
                    ],
                }
            )

        return {"simulations": simulations, "total": len(simulations)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching simulations: {str(e)}"
        )


@app.get("/api/simulations/list")
async def list_simulation_files():
    """List available simulation result files."""
    try:
        sim_files = get_available_simulations()
        return {"files": [str(f.name) for f in sim_files], "total": len(sim_files)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing simulation files: {str(e)}"
        )


# Learning system
@app.get("/api/learning/summary")
async def get_learning_summary():
    """Get learning system summary."""
    try:
        summary = learning_integration.get_learning_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching learning summary: {str(e)}"
        )


@app.get("/api/learning/export")
async def export_learning_data(filename: str = "learning_export.json"):
    """Export learning data."""
    try:
        export_path = learning_integration.export_learning_data(filename)
        return {
            "success": True,
            "export_path": str(export_path),
            "message": f"Learning data exported to {export_path}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting learning data: {str(e)}"
        )


if __name__ == "__main__":
    print("🚀 Starting SIVA tau2-bench Backend Server...")
    print("📱 Dashboard will be available at: http://localhost:3000")
    print("🔌 Backend API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("")
    print("Press Ctrl+C to stop the server")

    uvicorn.run("main_tau2:app", host="0.0.0.0", port=8000, reload=True)
