"""
Learning System Integration for SIVA.

This module connects the tau2-bench simulation framework with the learning system
to enable continuous agent improvement through simulation results analysis.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from siva.data_model.simulation import SimulationRun
from siva.data_model.message import Message
from siva.utils.llm_utils import get_cost


class LearningIntegration:
    """
    Integrates simulation results with the learning system for continuous improvement.

    This class bridges the gap between tau2-bench simulations and the existing
    SIVA learning components (VectorStore, LLMJudge, DataManager).
    """

    def __init__(self, data_dir: str = "siva_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Learning system data files
        self.simulation_learning_file = self.data_dir / "simulation_learning.jsonl"
        self.agent_improvement_file = self.data_dir / "agent_improvement.json"

        # Initialize files
        self._initialize_files()

    def _initialize_files(self):
        """Initialize learning system data files."""
        if not self.simulation_learning_file.exists():
            self.simulation_learning_file.touch()

        if not self.agent_improvement_file.exists():
            self._save_json(
                self.agent_improvement_file,
                {
                    "created_at": datetime.now().isoformat(),
                    "total_simulations": 0,
                    "successful_simulations": 0,
                    "failed_simulations": 0,
                    "improvement_suggestions": [],
                    "performance_trends": [],
                },
            )

    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _append_jsonl(self, file_path: Path, data: Dict):
        """Append data to JSONL file."""
        with open(file_path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def process_simulation_result(
        self, simulation_run: SimulationRun
    ) -> Dict[str, Any]:
        """
        Process a simulation result and extract learning insights.

        Args:
            simulation_run: The completed simulation run

        Returns:
            Dictionary containing learning insights and recommendations
        """
        # Extract key metrics
        # Handle case where reward_info might not be available yet (e.g., when called from orchestrator)
        if simulation_run.reward_info:
            success = simulation_run.reward_info.reward > 0.5
            reward = simulation_run.reward_info.reward
        else:
            # Fallback: determine success based on other metrics
            success = True  # Assume success if no reward_info (will be updated later)
            reward = 0.0
        duration = simulation_run.duration
        agent_cost = simulation_run.agent_cost or 0.0
        user_cost = simulation_run.user_cost or 0.0
        total_cost = agent_cost + user_cost

        # Analyze conversation flow
        conversation_analysis = self._analyze_conversation_flow(simulation_run.messages)

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            simulation_run, conversation_analysis
        )

        # Create learning record
        learning_record = {
            "simulation_id": simulation_run.id,
            "task_id": simulation_run.task_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "metrics": {
                "duration": duration,
                "agent_cost": agent_cost,
                "user_cost": user_cost,
                "total_cost": total_cost,
                "reward": reward,
            },
            "conversation_analysis": conversation_analysis,
            "improvement_suggestions": improvement_suggestions,
        }

        # Save to learning system
        self._append_jsonl(self.simulation_learning_file, learning_record)

        # Update agent improvement metrics
        self._update_improvement_metrics(simulation_run, success)

        return learning_record

    def _analyze_conversation_flow(self, messages: List[Message]) -> Dict[str, Any]:
        """Analyze the conversation flow for learning insights."""
        analysis = {
            "total_turns": len(messages),
            "user_messages": 0,
            "agent_messages": 0,
            "tool_calls": 0,
            "tool_responses": 0,
            "conversation_patterns": [],
            "efficiency_metrics": {},
        }

        for msg in messages:
            if msg.role == "user":
                analysis["user_messages"] += 1
            elif msg.role == "assistant":
                analysis["agent_messages"] += 1
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    analysis["tool_calls"] += len(msg.tool_calls)
            elif msg.role == "tool":
                analysis["tool_responses"] += 1

        # Calculate efficiency metrics
        if analysis["total_turns"] > 0:
            analysis["efficiency_metrics"] = {
                "turns_per_tool_call": analysis["total_turns"]
                / max(analysis["tool_calls"], 1),
                "user_agent_ratio": analysis["user_messages"]
                / max(analysis["agent_messages"], 1),
                "tool_utilization_rate": analysis["tool_calls"]
                / max(analysis["total_turns"], 1),
            }

        return analysis

    def _generate_improvement_suggestions(
        self, simulation_run: SimulationRun, conversation_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement suggestions based on simulation results."""
        suggestions = []

        # Check for common failure patterns
        if simulation_run.reward_info and simulation_run.reward_info.reward < 0.5:
            suggestions.append(
                "Consider reviewing agent instructions for this task type"
            )

            # Analyze action checks for specific failures
            if hasattr(simulation_run.reward_info, "action_checks"):
                failed_actions = [
                    check
                    for check in simulation_run.reward_info.action_checks
                    if check.get("reward", 1.0) < 0.5
                ]
                if failed_actions:
                    suggestions.append(
                        f"Focus on improving {len(failed_actions)} failed action(s)"
                    )

        # Check conversation efficiency
        if conversation_analysis["total_turns"] > 20:
            suggestions.append(
                "Consider optimizing conversation flow to reduce turn count"
            )

        # Check tool utilization
        tool_utilization = conversation_analysis["efficiency_metrics"].get(
            "tool_utilization_rate", 0
        )
        if tool_utilization < 0.3:
            suggestions.append("Agent may benefit from more proactive tool usage")

        # Check cost efficiency
        if simulation_run.agent_cost and simulation_run.agent_cost > 0.05:
            suggestions.append(
                "Consider optimizing agent prompts to reduce token usage"
            )

        return suggestions

    def _update_improvement_metrics(self, simulation_run: SimulationRun, success: bool):
        """Update agent improvement metrics."""
        current_metrics = self._load_json(self.agent_improvement_file)

        current_metrics["total_simulations"] += 1
        if success:
            current_metrics["successful_simulations"] += 1
        else:
            current_metrics["failed_simulations"] += 1

        # Calculate success rate
        success_rate = (
            current_metrics["successful_simulations"]
            / current_metrics["total_simulations"]
        )

        # Add performance trend
        current_metrics["performance_trends"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "success_rate": success_rate,
                "simulation_id": simulation_run.id,
            }
        )

        # Keep only last 100 trends
        if len(current_metrics["performance_trends"]) > 100:
            current_metrics["performance_trends"] = current_metrics[
                "performance_trends"
            ][-100:]

        self._save_json(self.agent_improvement_file, current_metrics)

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning system performance."""
        # Load learning records
        learning_records = []
        try:
            with open(self.simulation_learning_file, "r") as f:
                for line in f:
                    if line.strip():
                        learning_records.append(json.loads(line))
        except FileNotFoundError:
            pass

        # Load improvement metrics
        improvement_metrics = self._load_json(self.agent_improvement_file)

        # Calculate recent performance (last 10 simulations)
        recent_simulations = learning_records[-10:] if learning_records else []
        recent_success_rate = (
            sum(1 for r in recent_simulations if r.get("success", False))
            / len(recent_simulations)
            if recent_simulations
            else 0
        )

        return {
            "total_simulations": improvement_metrics.get("total_simulations", 0),
            "overall_success_rate": improvement_metrics.get("successful_simulations", 0)
            / max(improvement_metrics.get("total_simulations", 1), 1),
            "recent_success_rate": recent_success_rate,
            "total_learning_records": len(learning_records),
            "improvement_suggestions": improvement_metrics.get(
                "improvement_suggestions", []
            ),
            "performance_trends": improvement_metrics.get("performance_trends", []),
        }

    def export_learning_data(self, output_file: str = "learning_export.json"):
        """Export learning data for external analysis."""
        learning_records = []
        try:
            with open(self.simulation_learning_file, "r") as f:
                for line in f:
                    if line.strip():
                        learning_records.append(json.loads(line))
        except FileNotFoundError:
            pass

        improvement_metrics = self._load_json(self.agent_improvement_file)

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "learning_records": learning_records,
            "improvement_metrics": improvement_metrics,
            "summary": self.get_learning_summary(),
        }

        export_path = self.data_dir / output_file
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return str(export_path)
