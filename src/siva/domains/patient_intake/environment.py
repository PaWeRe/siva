# Copyright Sierra
from functools import partial
from typing import Optional, Dict, Any

# Import your existing components (we'll keep them for now)
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from core.data_manager import DataManager


# For now, we'll create simple placeholder classes
# These will be replaced with proper tau2-bench imports in future phases
class Task:
    """Placeholder for tau2 Task class."""

    pass


class Environment:
    """Placeholder for tau2 Environment class."""

    def __init__(self, domain_name: str, policy: str, tools: Any, user_tools: Any):
        self.domain_name = domain_name
        self.policy = policy
        self.tools = tools
        self.user_tools = user_tools


def load_file(path: str) -> str:
    """Placeholder for tau2 load_file function."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"


# Import your existing components (we'll keep them for now)
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from core.data_manager import DataManager


class PatientIntakeEnvironment(Environment):
    """Patient intake environment for healthcare domain."""

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: Any,  # We'll define proper tools later
        user_tools: Any,  # We'll define proper user tools later
        vector_store: Optional[VectorStore] = None,
        llm_judge: Optional[LLMJudge] = None,
        data_manager: Optional[DataManager] = None,
    ):
        super().__init__(domain_name, policy, tools, user_tools)
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.data_manager = data_manager
        self.session_data: Dict[str, Any] = {}

    def set_state(
        self,
        initialization_data: Dict[str, Any],
        initialization_actions: list,
        message_history: list,
    ):
        """Set the initial state for a patient intake session."""
        self.session_data = {
            "mode": "patient_intake",
            "phase": "basic_intake",
            "messages": message_history,
            "data": initialization_data or {},
            "escalation_data": {},
            "session_id": initialization_data.get("session_id", "default"),
        }

        # Initialize with system message if not present
        if not message_history:
            self.session_data["messages"] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]

    def get_response(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls in the patient intake environment."""
        # For now, return a simple response
        # This will be expanded to handle your existing function calls
        return {
            "content": f"Tool call {tool_call.get('name', 'unknown')} processed",
            "success": True,
        }

    def _get_system_prompt(self) -> str:
        """Get system prompt for patient intake."""
        return (
            "You are John, an agent for Tsidi Health Services. "
            "Your job is to collect basic information from the user before their doctor visit. "
            "Address the user by their first name, be polite and professional. "
            "You're not a medical professional, so you shouldn't provide any advice. Keep your responses short. "
            "IMPORTANT: Start by greeting the user warmly and introducing yourself. "
            "Collect basic information: full name, birthday, prescriptions, allergies, medical conditions, and reason for visit. "
            "Ask for clarification if a user response is ambiguous. "
            "NEVER assume or hallucinate information. Only store what the user actually provides. "
            "Use function calls to store each piece of information as you collect it. "
            "Once ALL basic information is collected, tell the user you need to ask some detailed questions about their symptoms."
        )


def get_environment(
    db: Optional[Any] = None,
    user_db: Optional[Any] = None,
    solo_mode: bool = False,
    vector_store: Optional[VectorStore] = None,
    llm_judge: Optional[LLMJudge] = None,
    data_manager: Optional[DataManager] = None,
) -> PatientIntakeEnvironment:
    """Get the patient intake environment."""
    # For now, we'll use placeholder tools
    # These will be properly defined in the next phase
    tools = None
    user_tools = None

    # Load policy (we'll create this in the next phase)
    policy = "Patient intake policy placeholder"

    return PatientIntakeEnvironment(
        domain_name="patient_intake",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
    )


get_environment_manual_policy = partial(get_environment, policy_type="manual")
get_environment_workflow_policy = partial(get_environment, policy_type="workflow")


def load_tasks(path: str) -> list[Task]:
    """Load tasks from a data file, could be json, yaml or toml file."""
    tasks = load_file(path)
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    return [Task.model_validate(task) for task in tasks]


def get_tasks_full() -> list[Task]:
    return load_tasks(TELECOM_TASK_SET_PATH_FULL)


def get_tasks_small() -> list[Task]:
    return load_tasks(TELECOM_TASK_SET_PATH_SMALL)


def get_tasks() -> list[Task]:
    return load_tasks(TELECOM_TASK_SET_PATH)


if __name__ == "__main__":
    env = get_environment()
    # print(env.get_tools())
    for tool in env.get_user_tools():
        print(tool.name)
