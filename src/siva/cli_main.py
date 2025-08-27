#!/usr/bin/env python3
"""
SIVA CLI for running patient intake simulations.
Based on tau2-bench structure.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from siva.cli import add_run_args
from siva.data_model.simulation import RunConfig
from siva.run import run_domain


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SIVA - Self-Learning Voice Agent for Healthcare Intake",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run simulations")
    add_run_args(run_parser)

    # Parse arguments
    args = parser.parse_args()

    if args.command == "run":
        # Create run config
        config = RunConfig(
            domain=args.domain,
            num_trials=args.num_trials,
            agent=args.agent,
            llm_agent=args.agent_llm,
            llm_agent_args=args.agent_llm_args,
            user=args.user,
            llm_user=args.user_llm,
            llm_user_args=args.user_llm_args,
            task_set_name=args.task_set_name,
            task_ids=args.task_ids,
            num_tasks=args.num_tasks,
            max_steps=args.max_steps,
            max_errors=args.max_errors,
            max_concurrency=args.max_concurrency,
            seed=args.seed,
        )

        # Run the simulation
        results = run_domain(config)

        # Print results
        print(f"Simulation completed!")
        print(f"Total tasks: {len(results.simulations)}")
        print(f"Results saved to data/siva/simulations/")

        # Save results
        results_path = Path("data/siva/simulations")
        results_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_path / f"patient_intake_{timestamp}_results.json"

        with open(results_file, "w") as f:
            f.write(results.model_dump_json(indent=2))

        print(f"Results saved to: {results_file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
