"""
Dashboard API endpoints for the Next.js frontend.

This module provides REST API endpoints that integrate with the existing
tau2-bench simulation framework and learning system.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from siva.learning.integration import LearningIntegration
from siva.scripts.view_simulations import get_available_simulations
from siva.data_model.simulation import Results
from siva.run import run_domain
from siva.data_model.simulation import RunConfig

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize learning integration
learning_integration = LearningIntegration()


class SimulationRunRequest(BaseModel):
    domain: str
    agent: str
    user: str
    num_tasks: int = 1
    max_steps: int = 50
    max_errors: int = 10
    seed: Optional[int] = None


class SimulationResult(BaseModel):
    id: str
    task_id: str
    duration: float
    termination_reason: str
    agent_cost: float
    user_cost: float
    reward: float
    action_checks: List[Dict[str, Any]]


@router.get("/simulations/recent")
async def get_recent_simulations(limit: int = 10) -> Dict[str, Any]:
    """Get recent simulation results for the dashboard."""
    try:
        # Get available simulation files
        sim_files = get_available_simulations()

        if not sim_files:
            return {"simulations": [], "total": 0}

        # Load the most recent simulation file
        latest_file = sim_files[-1]
        results = Results.load(latest_file)

        # Convert to dashboard format
        simulations = []
        for sim in results.simulations[:limit]:
            # Extract action checks if available
            action_checks = []
            if sim.reward_info and hasattr(sim.reward_info, "action_checks"):
                for check in sim.reward_info.action_checks:
                    action_checks.append(
                        {
                            "name": check.name if hasattr(check, "name") else "unknown",
                            "reward": check.reward if hasattr(check, "reward") else 0.0,
                        }
                    )

            simulations.append(
                SimulationResult(
                    id=str(sim.id) if hasattr(sim, "id") else str(hash(sim)),
                    task_id=sim.task_id,
                    duration=sim.duration,
                    termination_reason=sim.termination_reason,
                    agent_cost=sim.agent_cost or 0.0,
                    user_cost=sim.user_cost or 0.0,
                    reward=sim.reward_info.reward if sim.reward_info else 0.0,
                    action_checks=action_checks,
                )
            )

        return {"simulations": simulations, "total": len(simulations)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching simulations: {str(e)}"
        )


@router.post("/simulations/run")
async def run_simulation(request: SimulationRunRequest) -> Dict[str, Any]:
    """Run a new simulation from the dashboard."""
    try:
        # Create run configuration
        config = RunConfig(
            domain=request.domain,
            agent=request.agent,
            user=request.user,
            num_tasks=request.num_tasks,
            max_steps=request.max_steps,
            max_errors=request.max_errors,
            seed=request.seed,
            agent_llm="gpt-4.1",
            user_llm="gpt-4.1",
            num_trials=1,
        )

        # Run the simulation
        results = run_domain(config)

        return {
            "success": True,
            "message": f"Simulation completed successfully",
            "results": {
                "total_tasks": len(results.simulation_runs),
                "successful_tasks": sum(
                    1
                    for r in results.simulation_runs
                    if r.reward_info and r.reward_info.reward > 0.5
                ),
                "total_cost": sum(
                    (r.agent_cost or 0) + (r.user_cost or 0)
                    for r in results.simulation_runs
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running simulation: {str(e)}"
        )


@router.get("/learning/summary")
async def get_learning_summary() -> Dict[str, Any]:
    """Get learning system summary for the dashboard."""
    try:
        summary = learning_integration.get_learning_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching learning summary: {str(e)}"
        )


@router.get("/learning/export")
async def export_learning_data(
    filename: str = "learning_export.json",
) -> Dict[str, Any]:
    """Export learning data for analysis."""
    try:
        export_path = learning_integration.export_learning_data(filename)
        return {
            "success": True,
            "export_path": export_path,
            "message": f"Learning data exported to {export_path}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting learning data: {str(e)}"
        )


@router.get("/domains")
async def get_available_domains() -> Dict[str, Any]:
    """Get available domains for simulation."""
    try:
        from siva.registry import registry

        info = registry.get_info()
        return {"domains": info.domains, "agents": info.agents, "users": info.users}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching domain info: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for the dashboard."""
    return {"status": "healthy", "service": "SIVA Dashboard API", "version": "1.0.0"}
