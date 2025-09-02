"""
Comprehensive testing framework for SIVA learning system.
Tests learning progression, accuracy improvement, and system readiness.
"""

import asyncio
import json
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import requests
import logging
from dataclasses import dataclass, asdict

from .patient_scenarios import (
    get_all_scenarios,
    get_scenarios_by_route,
    RouteType,
    PatientScenario,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single patient simulation test."""

    scenario_name: str
    expected_route: str
    predicted_route: str
    confidence: float
    correct: bool
    conversation_length: int
    processing_time: float
    timestamp: str
    session_id: str
    escalated: bool
    similar_cases_found: int


@dataclass
class LearningMetrics:
    """Metrics tracking learning progression."""

    timestamp: str
    total_conversations: int
    vector_store_size: int
    accuracy_rate: float
    escalation_rate: float
    avg_confidence: float
    route_accuracy: Dict[str, float]
    processing_efficiency: float
    system_readiness_score: float


class SIVALearningTester:
    """Main testing framework for SIVA learning system."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[TestResult] = []
        self.learning_metrics: List[LearningMetrics] = []
        self.session = requests.Session()

    def create_session_id(self) -> str:
        """Generate unique session ID for testing."""
        return f"test_session_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    async def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send a chat message to SIVA system."""
        try:
            response = self.session.post(
                f"{self.base_url}/chat",
                json={"session_id": session_id, "message": message},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {}

    async def simulate_patient_conversation(
        self, scenario: PatientScenario, verbose: bool = False
    ) -> Optional[TestResult]:
        """Simulate a complete patient conversation."""
        session_id = self.create_session_id()
        start_time = time.time()

        if verbose:
            print(f"\n🔄 Testing: {scenario.name} (Expected: {scenario.route.value})")

        responses = []
        for i, message in enumerate(scenario.conversation_flow):
            if verbose:
                print(f"  👤 User: {message}")

            response = await self.send_chat_message(session_id, message)

            if response:
                if verbose:
                    ai_response = response.get("response", "")
                    print(
                        f"  🤖 SIVA: {ai_response[:80]}{'...' if len(ai_response) > 80 else ''}"
                    )

                responses.append(response)

                # Check if conversation ended
                if response.get("end_call", False):
                    break

            # Small delay between messages
            await asyncio.sleep(0.2)

        processing_time = time.time() - start_time

        if not responses:
            logger.warning(f"No responses received for {scenario.name}")
            return None

        # Extract final result
        last_response = responses[-1]
        escalation_info = last_response.get("escalation_info", {})
        predicted_route = escalation_info.get("agent_prediction", "unknown")

        # Calculate metrics
        escalated = last_response.get("end_call", False)
        correct = predicted_route == scenario.route.value
        confidence = escalation_info.get("confidence", 0.0)

        # Get similar cases count (approximate from current system state)
        similar_cases = await self.get_similar_cases_count(session_id)

        result = TestResult(
            scenario_name=scenario.name,
            expected_route=scenario.route.value,
            predicted_route=predicted_route,
            confidence=confidence,
            correct=correct,
            conversation_length=len(responses),
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            escalated=escalated,
            similar_cases_found=similar_cases,
        )

        if verbose:
            status = "✅ Correct" if correct else "❌ Incorrect"
            print(
                f"  {status} - Predicted: {predicted_route}, Confidence: {confidence:.2f}"
            )

        return result

    async def get_similar_cases_count(self, session_id: str) -> int:
        """Get count of similar cases for current conversation."""
        try:
            response = self.session.get(f"{self.base_url}/vector_store/stats")
            if response.status_code == 200:
                data = response.json()
                return data.get("total_conversations", 0)
        except:
            pass
        return 0

    async def get_current_metrics(self) -> LearningMetrics:
        """Get current system metrics."""
        try:
            # Fetch dashboard metrics
            dashboard_response = self.session.get(f"{self.base_url}/dashboard/metrics")
            dashboard_data = dashboard_response.json()

            # Fetch vector store stats
            vector_response = self.session.get(f"{self.base_url}/vector_store/stats")
            vector_data = vector_response.json()

            # Calculate metrics from test results
            recent_results = [
                r
                for r in self.test_results
                if r.timestamp > (datetime.now() - timedelta(hours=1)).isoformat()
            ]

            accuracy_rate = sum(1 for r in recent_results if r.correct) / max(
                len(recent_results), 1
            )
            escalation_rate = sum(1 for r in recent_results if r.escalated) / max(
                len(recent_results), 1
            )
            avg_confidence = sum(r.confidence for r in recent_results) / max(
                len(recent_results), 1
            )

            # Route-specific accuracy
            route_accuracy = {}
            for route in RouteType:
                route_results = [
                    r for r in recent_results if r.expected_route == route.value
                ]
                if route_results:
                    route_accuracy[route.value] = sum(
                        1 for r in route_results if r.correct
                    ) / len(route_results)
                else:
                    route_accuracy[route.value] = 0.0

            # Processing efficiency (conversations per minute)
            if recent_results:
                time_span = max(
                    1,
                    (
                        datetime.now()
                        - datetime.fromisoformat(recent_results[0].timestamp)
                    ).total_seconds()
                    / 60,
                )
                processing_efficiency = len(recent_results) / time_span
            else:
                processing_efficiency = 0.0

            # System readiness score (composite metric)
            vector_size = vector_data.get("total_conversations", 0)
            readiness_score = min(
                100,
                (
                    accuracy_rate * 40  # 40% weight on accuracy
                    + min(vector_size / 50, 1)
                    * 30  # 30% weight on data size (50 conversations = ready)
                    + (1 - escalation_rate) * 20  # 20% weight on autonomy
                    + avg_confidence * 10  # 10% weight on confidence
                ),
            )

            return LearningMetrics(
                timestamp=datetime.now().isoformat(),
                total_conversations=dashboard_data.get("total_conversations", 0),
                vector_store_size=vector_size,
                accuracy_rate=accuracy_rate,
                escalation_rate=escalation_rate,
                avg_confidence=avg_confidence,
                route_accuracy=route_accuracy,
                processing_efficiency=processing_efficiency,
                system_readiness_score=readiness_score,
            )

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return LearningMetrics(
                timestamp=datetime.now().isoformat(),
                total_conversations=0,
                vector_store_size=0,
                accuracy_rate=0.0,
                escalation_rate=1.0,
                avg_confidence=0.0,
                route_accuracy={},
                processing_efficiency=0.0,
                system_readiness_score=0.0,
            )

    async def run_learning_progression_test(
        self, rounds: int = 3, scenarios_per_round: int = 5, verbose: bool = True
    ) -> Dict[str, Any]:
        """Run a comprehensive learning progression test."""

        print(f"\n🧪 Starting Learning Progression Test")
        print(f"📊 {rounds} rounds, {scenarios_per_round} scenarios per round")
        print("=" * 60)

        all_scenarios = get_all_scenarios()
        test_summary = {
            "start_time": datetime.now().isoformat(),
            "rounds": rounds,
            "scenarios_per_round": scenarios_per_round,
            "round_results": [],
            "learning_progression": [],
        }

        for round_num in range(1, rounds + 1):
            print(f"\n🔄 Round {round_num}/{rounds}")
            print("-" * 40)

            # Get initial metrics
            initial_metrics = await self.get_current_metrics()
            self.learning_metrics.append(initial_metrics)

            # Select diverse scenarios for this round
            round_scenarios = self._select_diverse_scenarios(
                all_scenarios, scenarios_per_round
            )
            round_results = []

            for scenario in round_scenarios:
                result = await self.simulate_patient_conversation(scenario, verbose)
                if result:
                    self.test_results.append(result)
                    round_results.append(result)

                # Brief pause between scenarios
                await asyncio.sleep(1)

            # Get final metrics for this round
            final_metrics = await self.get_current_metrics()
            self.learning_metrics.append(final_metrics)

            # Calculate round statistics
            round_accuracy = sum(1 for r in round_results if r.correct) / max(
                len(round_results), 1
            )
            round_summary = {
                "round": round_num,
                "accuracy": round_accuracy,
                "scenarios_tested": len(round_results),
                "vector_size_growth": final_metrics.vector_store_size
                - initial_metrics.vector_store_size,
                "readiness_improvement": final_metrics.system_readiness_score
                - initial_metrics.system_readiness_score,
                "results": [asdict(r) for r in round_results],
            }

            test_summary["round_results"].append(round_summary)
            test_summary["learning_progression"].append(asdict(final_metrics))

            print(f"\n📈 Round {round_num} Summary:")
            print(f"   Accuracy: {round_accuracy:.1%}")
            print(
                f"   Vector Store Growth: +{round_summary['vector_size_growth']} conversations"
            )
            print(
                f"   System Readiness: {final_metrics.system_readiness_score:.1f}/100"
            )

            # Pause between rounds to allow system to process
            if round_num < rounds:
                print(f"\n⏳ Waiting before next round...")
                await asyncio.sleep(3)

        test_summary["end_time"] = datetime.now().isoformat()
        return test_summary

    def _select_diverse_scenarios(
        self, all_scenarios: List[PatientScenario], count: int
    ) -> List[PatientScenario]:
        """Select a diverse set of scenarios ensuring good route coverage."""
        import random

        # Group scenarios by route
        by_route = {}
        for scenario in all_scenarios:
            route = scenario.route.value
            if route not in by_route:
                by_route[route] = []
            by_route[route].append(scenario)

        # Select scenarios ensuring route diversity
        selected = []
        routes = list(by_route.keys())

        for i in range(count):
            route = routes[i % len(routes)]
            if by_route[route]:
                scenario = random.choice(by_route[route])
                selected.append(scenario)
                by_route[route].remove(scenario)  # Avoid duplicates

        return selected

    async def run_accuracy_validation_test(
        self, verbose: bool = True
    ) -> Dict[str, Any]:
        """Run focused accuracy validation test with known scenarios."""

        print(f"\n🎯 Accuracy Validation Test")
        print("=" * 40)

        # Test specific scenarios that should be learned
        validation_scenarios = [
            # Emergency cases that should be clearly recognized
            ("Acute Myocardial Infarction", RouteType.EMERGENCY),
            ("Stroke Symptoms", RouteType.EMERGENCY),
            # Routine cases that should not be escalated
            ("Annual Physical Exam", RouteType.ROUTINE),
            ("Common Cold", RouteType.SELF_CARE),
        ]

        results = []
        for scenario_name, expected_route in validation_scenarios:
            try:
                scenario = [s for s in get_all_scenarios() if s.name == scenario_name][
                    0
                ]
                result = await self.simulate_patient_conversation(scenario, verbose)
                if result:
                    results.append(result)
            except IndexError:
                logger.warning(f"Scenario '{scenario_name}' not found")

        # Calculate validation metrics
        accuracy = sum(1 for r in results if r.correct) / max(len(results), 1)

        return {
            "validation_accuracy": accuracy,
            "total_tested": len(results),
            "correct_predictions": sum(1 for r in results if r.correct),
            "results": [asdict(r) for r in results],
            "timestamp": datetime.now().isoformat(),
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        if not self.test_results:
            return {"error": "No test results available"}

        # Overall statistics
        total_tests = len(self.test_results)
        correct_predictions = sum(1 for r in self.test_results if r.correct)
        overall_accuracy = correct_predictions / total_tests

        # Route-specific analysis
        route_analysis = {}
        for route in RouteType:
            route_results = [
                r for r in self.test_results if r.expected_route == route.value
            ]
            if route_results:
                route_analysis[route.value] = {
                    "total": len(route_results),
                    "correct": sum(1 for r in route_results if r.correct),
                    "accuracy": sum(1 for r in route_results if r.correct)
                    / len(route_results),
                    "avg_confidence": sum(r.confidence for r in route_results)
                    / len(route_results),
                    "avg_processing_time": sum(r.processing_time for r in route_results)
                    / len(route_results),
                }

        # Learning progression analysis
        learning_progression = []
        if len(self.learning_metrics) >= 2:
            for i in range(1, len(self.learning_metrics)):
                prev = self.learning_metrics[i - 1]
                curr = self.learning_metrics[i]
                learning_progression.append(
                    {
                        "timestamp": curr.timestamp,
                        "accuracy_change": curr.accuracy_rate - prev.accuracy_rate,
                        "vector_size_change": curr.vector_store_size
                        - prev.vector_store_size,
                        "readiness_change": curr.system_readiness_score
                        - prev.system_readiness_score,
                    }
                )

        return {
            "summary": {
                "total_tests": total_tests,
                "correct_predictions": correct_predictions,
                "overall_accuracy": overall_accuracy,
                "avg_confidence": sum(r.confidence for r in self.test_results)
                / total_tests,
                "avg_processing_time": sum(r.processing_time for r in self.test_results)
                / total_tests,
            },
            "route_analysis": route_analysis,
            "learning_progression": learning_progression,
            "final_metrics": (
                asdict(self.learning_metrics[-1]) if self.learning_metrics else None
            ),
            "test_timestamp": datetime.now().isoformat(),
        }

    def save_results(self, filename: str = None):
        """Save test results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tests/results/siva_learning_test_{timestamp}.json"

        # Create directory if it doesn't exist
        import os

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        data = {
            "test_results": [asdict(r) for r in self.test_results],
            "learning_metrics": [asdict(m) for m in self.learning_metrics],
            "report": self.generate_report(),
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"📄 Test results saved to: {filename}")
        return filename


# Convenience functions for running tests
async def run_quick_learning_test(
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Run a quick learning test with minimal scenarios."""
    tester = SIVALearningTester(base_url)
    return await tester.run_learning_progression_test(
        rounds=2, scenarios_per_round=3, verbose=True
    )


async def run_comprehensive_learning_test(
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Run a comprehensive learning test with full scenario coverage."""
    tester = SIVALearningTester(base_url)
    return await tester.run_learning_progression_test(
        rounds=5, scenarios_per_round=8, verbose=True
    )


async def run_accuracy_validation(
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Run focused accuracy validation test."""
    tester = SIVALearningTester(base_url)
    return await tester.run_accuracy_validation_test(verbose=True)
