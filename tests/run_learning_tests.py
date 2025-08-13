#!/usr/bin/env python3
"""
CLI runner for SIVA learning system tests.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tests.simulations.learning_test_framework import (
    SIVALearningTester,
    run_quick_learning_test,
    run_comprehensive_learning_test,
    run_accuracy_validation,
)
from tests.simulations.patient_scenarios import get_all_scenarios, RouteType


def print_banner():
    """Print test banner."""
    print("=" * 70)
    print("🧠 SIVA Learning System Test Suite")
    print("   Testing AI Learning Progression & Accuracy")
    print("=" * 70)


async def test_server_connection(base_url: str) -> bool:
    """Test if SIVA server is running."""
    import requests

    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ SIVA server is running at {base_url}")
        return True
    except:
        print(f"❌ SIVA server is not running at {base_url}")
        print(
            "   Please start the server with: uv run uvicorn main:app --host 0.0.0.0 --port 8000"
        )
        return False


async def run_scenario_demo(base_url: str):
    """Run a demo of available scenarios."""
    print("\n📋 Available Test Scenarios")
    print("-" * 40)

    scenarios = get_all_scenarios()
    by_route = {}
    for scenario in scenarios:
        route = scenario.route.value
        if route not in by_route:
            by_route[route] = []
        by_route[route].append(scenario)

    for route, route_scenarios in by_route.items():
        print(f"\n🔹 {route.upper()} ({len(route_scenarios)} scenarios):")
        for scenario in route_scenarios[:3]:  # Show first 3
            print(f"   • {scenario.name}")
            print(f"     {scenario.description}")
        if len(route_scenarios) > 3:
            print(f"   ... and {len(route_scenarios) - 3} more")


async def run_single_scenario_test(base_url: str, scenario_name: str):
    """Run a test with a single specific scenario."""
    from tests.simulations.patient_scenarios import get_scenario_by_name

    try:
        scenario = get_scenario_by_name(scenario_name)
        print(f"\n🧪 Testing Single Scenario: {scenario.name}")
        print(f"📝 Description: {scenario.description}")
        print(f"🎯 Expected Route: {scenario.route.value}")
        print("-" * 50)

        tester = SIVALearningTester(base_url)
        result = await tester.simulate_patient_conversation(scenario, verbose=True)

        if result:
            print(f"\n📊 Test Result:")
            print(f"   ✅ Correct: {result.correct}")
            print(f"   🎯 Predicted: {result.predicted_route}")
            print(f"   🎚️ Confidence: {result.confidence:.2f}")
            print(f"   ⏱️ Processing Time: {result.processing_time:.2f}s")
            print(f"   💬 Conversation Length: {result.conversation_length} messages")
        else:
            print("❌ Test failed - no result obtained")

    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nAvailable scenarios:")
        for scenario in get_all_scenarios():
            print(f"   • {scenario.name}")


async def main():
    parser = argparse.ArgumentParser(description="SIVA Learning System Test Suite")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="SIVA server URL"
    )
    parser.add_argument(
        "--test-type",
        choices=["quick", "comprehensive", "accuracy", "demo", "scenario"],
        default="quick",
        help="Type of test to run",
    )
    parser.add_argument(
        "--scenario", help="Specific scenario name for single scenario test"
    )
    parser.add_argument(
        "--save-results", action="store_true", help="Save test results to file"
    )

    args = parser.parse_args()

    print_banner()

    # Check server connection
    if not await test_server_connection(args.url):
        return 1

    try:
        if args.test_type == "demo":
            await run_scenario_demo(args.url)

        elif args.test_type == "scenario":
            if not args.scenario:
                print("❌ --scenario name required for single scenario test")
                return 1
            await run_single_scenario_test(args.url, args.scenario)

        elif args.test_type == "quick":
            print("\n🚀 Running Quick Learning Test")
            print("   2 rounds, 3 scenarios per round")
            result = await run_quick_learning_test(args.url)

            print(f"\n📈 Quick Test Summary:")
            print(f"   Rounds completed: {len(result['round_results'])}")
            print(
                f"   Total scenarios: {sum(r['scenarios_tested'] for r in result['round_results'])}"
            )

            if args.save_results:
                tester = SIVALearningTester(args.url)
                filename = tester.save_results()
                print(f"📄 Results saved to: {filename}")

        elif args.test_type == "comprehensive":
            print("\n🎯 Running Comprehensive Learning Test")
            print("   5 rounds, 8 scenarios per round")
            result = await run_comprehensive_learning_test(args.url)

            print(f"\n📈 Comprehensive Test Summary:")
            print(f"   Rounds completed: {len(result['round_results'])}")
            print(
                f"   Total scenarios: {sum(r['scenarios_tested'] for r in result['round_results'])}"
            )

            if args.save_results:
                tester = SIVALearningTester(args.url)
                filename = tester.save_results()
                print(f"📄 Results saved to: {filename}")

        elif args.test_type == "accuracy":
            print("\n🎯 Running Accuracy Validation Test")
            result = await run_accuracy_validation(args.url)

            print(f"\n📊 Accuracy Validation Summary:")
            print(f"   Validation Accuracy: {result['validation_accuracy']:.1%}")
            print(f"   Scenarios Tested: {result['total_tested']}")
            print(f"   Correct Predictions: {result['correct_predictions']}")

        print(f"\n🎉 Test completed successfully!")
        print(f"   View dashboard at: {args.url}/frontend/dashboard.html")

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
