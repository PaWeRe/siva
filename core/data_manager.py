"""Data manager for persistent storage and management of SIVA system data."""

import json
import os
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class DataManager:
    """Manages persistent storage of conversations, evaluations, and system metrics."""

    def __init__(self, data_dir: str = "siva_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Data files
        self.conversations_file = self.data_dir / "conversations.jsonl"
        self.evaluations_file = self.data_dir / "evaluations.jsonl"
        self.system_metrics_file = self.data_dir / "system_metrics.json"
        self.sessions_file = self.data_dir / "sessions.json"

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize data files if they don't exist."""
        for file_path in [self.conversations_file, self.evaluations_file]:
            if not file_path.exists():
                file_path.touch()

        if not self.system_metrics_file.exists():
            self._save_json(
                self.system_metrics_file,
                {
                    "created_at": datetime.datetime.now().isoformat(),
                    "total_conversations": 0,
                    "total_escalations": 0,
                    "accuracy_history": [],
                },
            )

        if not self.sessions_file.exists():
            self._save_json(self.sessions_file, {})

    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _append_jsonl(self, file_path: Path, data: Dict):
        """Append data to JSONL file."""
        with open(file_path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def _read_jsonl(self, file_path: Path) -> List[Dict]:
        """Read all data from JSONL file."""
        data = []
        try:
            with open(file_path, "r") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except FileNotFoundError:
            pass
        return data

    def save_conversation(self, session_id: str, conversation_data: Dict):
        """Save a completed conversation."""
        record = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "conversation_data": conversation_data,
        }
        self._append_jsonl(self.conversations_file, record)
        self._update_metrics("conversation_saved")

    def save_evaluation(self, session_id: str, evaluation_data: Dict):
        """Save an evaluation from human feedback."""
        record = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "evaluation_data": evaluation_data,
        }
        self._append_jsonl(self.evaluations_file, record)
        self._update_metrics("evaluation_saved", evaluation_data)

    def get_all_conversations(self) -> List[Dict]:
        """Get all saved conversations."""
        return self._read_jsonl(self.conversations_file)

    def get_all_evaluations(self) -> List[Dict]:
        """Get all saved evaluations."""
        return self._read_jsonl(self.evaluations_file)

    def get_system_metrics(self) -> Dict:
        """Get current system metrics."""
        return self._load_json(self.system_metrics_file)

    def save_sessions(self, sessions: Dict[str, Dict]):
        """Save current sessions to disk."""
        self._save_json(self.sessions_file, sessions)

    def load_sessions(self) -> Dict[str, Dict]:
        """Load sessions from disk."""
        return self._load_json(self.sessions_file)

    def _update_metrics(self, event_type: str, data: Optional[Dict] = None):
        """Update system metrics based on events."""
        metrics = self.get_system_metrics()

        if event_type == "conversation_saved":
            metrics["total_conversations"] = metrics.get("total_conversations", 0) + 1

        elif event_type == "evaluation_saved":
            metrics["total_escalations"] = metrics.get("total_escalations", 0) + 1

            # Track accuracy over time
            if data and "evaluation_data" in data:
                eval_data = data["evaluation_data"]
                is_correct = eval_data.get("prediction_correct", False)

                accuracy_history = metrics.get("accuracy_history", [])
                accuracy_history.append(
                    {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "is_correct": is_correct,
                        "agent_prediction": eval_data.get("agent_prediction"),
                        "human_label": eval_data.get("human_label"),
                    }
                )
                metrics["accuracy_history"] = accuracy_history

        metrics["last_updated"] = datetime.datetime.now().isoformat()
        self._save_json(self.system_metrics_file, metrics)

    def compute_learning_curve(self) -> Dict[str, List]:
        """Compute learning curve from historical data."""
        evaluations = self.get_all_evaluations()

        timestamps = []
        accuracy_scores = []
        cumulative_correct = 0

        for i, eval_record in enumerate(evaluations):
            eval_data = eval_record.get("evaluation_data", {})
            is_correct = eval_data.get("prediction_correct", False)

            if is_correct:
                cumulative_correct += 1

            accuracy = (cumulative_correct / (i + 1)) * 100 if i >= 0 else 0
            timestamps.append(eval_record.get("timestamp", ""))
            accuracy_scores.append(accuracy)

        return {
            "timestamps": timestamps,
            "accuracy": accuracy_scores,
            "total_evaluations": len(evaluations),
        }

    def get_escalation_metrics(self) -> Dict[str, Any]:
        """Compute escalation precision and related metrics."""
        evaluations = self.get_all_evaluations()

        if not evaluations:
            return {
                "total_escalations": 0,
                "necessary_escalations": 0,
                "unnecessary_escalations": 0,
                "escalation_precision": 0.0,
                "escalation_rate": 0.0,
            }

        necessary = sum(
            1
            for eval_record in evaluations
            if not eval_record.get("evaluation_data", {}).get(
                "prediction_correct", True
            )
        )

        unnecessary = len(evaluations) - necessary
        precision = necessary / len(evaluations) if evaluations else 0

        conversations = self.get_all_conversations()
        total_conversations = len(conversations)
        escalation_rate = len(evaluations) / max(1, total_conversations)

        return {
            "total_escalations": len(evaluations),
            "necessary_escalations": necessary,
            "unnecessary_escalations": unnecessary,
            "escalation_precision": precision,
            "escalation_rate": escalation_rate,
        }

    def export_all_data(self) -> Dict[str, Any]:
        """Export all system data for backup or analysis."""
        return {
            "conversations": self.get_all_conversations(),
            "evaluations": self.get_all_evaluations(),
            "system_metrics": self.get_system_metrics(),
            "sessions": self.load_sessions(),
            "escalation_metrics": self.get_escalation_metrics(),
            "learning_curve": self.compute_learning_curve(),
            "export_timestamp": datetime.datetime.now().isoformat(),
        }

    def reset_all_data(self):
        """Reset all stored data (for demo purposes)."""
        # Remove all data files
        for file_path in [
            self.conversations_file,
            self.evaluations_file,
            self.system_metrics_file,
            self.sessions_file,
        ]:
            if file_path.exists():
                file_path.unlink()

        # Reinitialize
        self._initialize_files()
        print("[DataManager] All data reset")

    def get_data_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored data."""
        conversations = self.get_all_conversations()
        evaluations = self.get_all_evaluations()
        metrics = self.get_system_metrics()

        # Route distribution from evaluations
        route_counts = {}
        for eval_record in evaluations:
            eval_data = eval_record.get("evaluation_data", {})
            route = eval_data.get("human_label", "unknown")
            route_counts[route] = route_counts.get(route, 0) + 1

        # Recent activity (last 10 evaluations)
        recent_activity = []
        for eval_record in evaluations[-10:]:
            eval_data = eval_record.get("evaluation_data", {})
            outcome = (
                "necessary"
                if not eval_data.get("prediction_correct", True)
                else "unnecessary"
            )

            recent_activity.append(
                {
                    "type": "Escalation",
                    "route": eval_data.get("human_label", "unknown"),
                    "description": f"Agent predicted {eval_data.get('agent_prediction', 'unknown')}",
                    "outcome": outcome,
                    "timestamp": eval_record.get("timestamp", ""),
                }
            )

        return {
            "total_conversations": len(conversations),
            "total_evaluations": len(evaluations),
            "route_distribution": route_counts,
            "recent_activity": recent_activity,
            "data_size_mb": self._calculate_data_size(),
            "oldest_record": evaluations[0].get("timestamp", "") if evaluations else "",
            "newest_record": (
                evaluations[-1].get("timestamp", "") if evaluations else ""
            ),
        }

    def _calculate_data_size(self) -> float:
        """Calculate total data size in MB."""
        total_size = 0
        for file_path in [
            self.conversations_file,
            self.evaluations_file,
            self.system_metrics_file,
            self.sessions_file,
        ]:
            if file_path.exists():
                total_size += file_path.stat().st_size

        return round(total_size / (1024 * 1024), 2)
