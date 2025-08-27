from datetime import date, datetime

from siva.utils.utils import DATA_DIR

PATIENT_INTAKE_DATA_DIR = DATA_DIR / "siva" / "domains" / "patient_intake"
PATIENT_INTAKE_DB_PATH = PATIENT_INTAKE_DATA_DIR / "db.toml"
PATIENT_INTAKE_USER_DB_PATH = PATIENT_INTAKE_DATA_DIR / "user_db.toml"
PATIENT_INTAKE_MAIN_POLICY_PATH = PATIENT_INTAKE_DATA_DIR / "main_policy.md"
PATIENT_INTAKE_MAIN_POLICY_SOLO_PATH = PATIENT_INTAKE_DATA_DIR / "main_policy_solo.md"
PATIENT_INTAKE_TASK_SET_PATH = PATIENT_INTAKE_DATA_DIR / "tasks.json"


def get_now() -> datetime:
    # assume now is 2025-02-25 12:08:00
    return datetime(2025, 2, 25, 12, 8, 0)


def get_today() -> date:
    # assume today is 2025-02-25
    return date(2025, 2, 25)
