#!/usr/bin/env python3
"""
SIVA CLI for running simulations and managing the system.
"""

import argparse
import sys
from pathlib import Path

from siva.registry import registry
from siva.run import run_domain
from siva.data_model.simulation import RunConfig
from siva.learning.integration import LearningIntegration


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SIVA CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run simulations")
    run_parser.add_argument("--domain", required=True, help="Domain to run")
    run_parser.add_argument("--agent", required=True, help="Agent to use")
    run_parser.add_argument("--user", required=True, help="User simulator to use")
    run_parser.add_argument(
        "--num-tasks", type=int, default=1, help="Number of tasks to run"
    )
    run_parser.add_argument(
        "--max-steps", type=int, default=50, help="Maximum steps per simulation"
    )
    run_parser.add_argument(
        "--max-errors", type=int, default=10, help="Maximum errors per simulation"
    )
    run_parser.add_argument("--seed", type=int, help="Random seed")

    # View command
    view_parser = subparsers.add_parser("view", help="View simulation results")

    # Learning command
    learning_parser = subparsers.add_parser(
        "learning", help="View learning system status"
    )
    learning_parser.add_argument("--export", help="Export learning data to file")

    args = parser.parse_args()

    if args.command == "run":
        # Run simulations
        config = RunConfig(
            domain=args.domain,
            agent=args.agent,
            user=args.user,
            num_tasks=args.num_tasks,
            max_steps=args.max_steps,
            max_errors=args.max_errors,
            seed=args.seed,
            agent_llm="gpt-4.1",
            user_llm="gpt-4.1",
            num_trials=1,
        )
        run_domain(config)
    elif args.command == "view":
        # View simulation results
        from siva.scripts.view_simulations import main as view_main

        view_main()
    elif args.command == "learning":
        # View learning system status
        learning_integration = LearningIntegration()
        summary = learning_integration.get_learning_summary()

        print("🧠 SIVA Learning System Status")
        print("=" * 50)
        print(f"Total Simulations: {summary['total_simulations']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.2%}")
        print(f"Recent Success Rate: {summary['recent_success_rate']:.2%}")
        print(f"Learning Records: {summary['total_learning_records']}")

        if summary["improvement_suggestions"]:
            print("\n📈 Improvement Suggestions:")
            for suggestion in summary["improvement_suggestions"]:
                print(f"  • {suggestion}")

        if args.export:
            export_path = learning_integration.export_learning_data(args.export)
            print(f"\n📊 Learning data exported to: {export_path}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
