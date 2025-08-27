import json
import random
from argparse import ArgumentParser

from siva.data_model.tasks import Task
from siva.domains.patient_intake.tasks.patient_intake_manager import (
    create_patient_intake_tasks,
)
from siva.utils import DATA_DIR


def create_tasks(save_tasks: bool = True) -> list[Task]:
    """Create patient intake tasks."""
    tasks = create_patient_intake_tasks(save_tasks=False)
    print(f"Number of patient intake tasks: {len(tasks)}")

    if save_tasks:
        file_path = DATA_DIR / "siva" / "domains" / "patient_intake" / "tasks.json"
        with open(file_path, "w") as f:
            json.dump([t.model_dump() for t in tasks], f, indent=2)
        print(f"Saved {len(tasks)} tasks to {file_path}")

    return tasks


def main():
    parser = ArgumentParser()
    parser.add_argument("-s", "--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    create_tasks()


if __name__ == "__main__":
    main()
