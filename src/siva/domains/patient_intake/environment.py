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
from core.processor import UnifiedProcessor
from openai import OpenAI


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

from .tools import PatientIntakeTools


class PatientIntakeEnvironment(Environment):
    """Patient intake environment for healthcare domain."""

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: PatientIntakeTools,
        user_tools: Any,
        vector_store: Optional[VectorStore] = None,
        llm_judge: Optional[LLMJudge] = None,
        data_manager: Optional[DataManager] = None,
        openai_client: Optional[OpenAI] = None,
    ):
        super().__init__(domain_name, policy, tools, user_tools)
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.data_manager = data_manager
        self.openai_client = openai_client
        self.session_data: Dict[str, Any] = {}

        # Initialize tools with session data
        if tools and hasattr(tools, "session_data"):
            tools.session_data = self.session_data

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

        # Update tools session data
        if self.tools and hasattr(self.tools, "session_data"):
            self.tools.session_data = self.session_data

    def get_response(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls in the patient intake environment."""
        if not self.tools:
            return {"content": "No tools available", "success": False}

        # Parse the tool call
        function_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        # Handle different tool calls
        if function_name == "verify_fullname":
            return self.tools.verify_fullname(arguments.get("names", []))
        elif function_name == "verify_birthday":
            return self.tools.verify_birthday(arguments.get("birthday", ""))
        elif function_name == "list_prescriptions":
            return self.tools.list_prescriptions(arguments.get("prescriptions", []))
        elif function_name == "list_allergies":
            return self.tools.list_allergies(arguments.get("allergies", []))
        elif function_name == "list_conditions":
            return self.tools.list_conditions(arguments.get("conditions", []))
        elif function_name == "list_visit_reasons":
            return self.tools.list_visit_reasons(arguments.get("visit_reasons", []))
        elif function_name == "collect_detailed_symptoms":
            return self.tools.collect_detailed_symptoms(arguments.get("symptoms", []))
        elif function_name == "determine_routing":
            return self.tools.determine_routing(
                arguments.get("route", ""), arguments.get("reasoning", "")
            )
        else:
            return {"content": f"Unknown tool call: {function_name}", "success": False}

    def process_message(self, message: str) -> tuple[str, bool, Dict[str, Any]]:
        """
        Process a message using the environment.
        This integrates with your existing processor logic.
        """
        # Create a legacy processor for compatibility
        if self.openai_client and self.vector_store and self.llm_judge:
            processor = UnifiedProcessor(
                session=self.session_data,
                vector_store=self.vector_store,
                llm_judge=self.llm_judge,
                openai_client=self.openai_client,
                retrieval_threshold=3,
                current_mode="patient_intake",
            )

            # Process the message
            reply, end_call, escalation_info = processor.next_prompt(message)

            # Update session data
            self.session_data.update(
                {
                    "messages": processor.get_history(),
                    "data": processor.get_data(),
                    "escalation_data": processor.get_escalation_data(),
                }
            )

            return reply, end_call, escalation_info
        else:
            # Fallback response if components aren't available
            return "I'm sorry, but I'm not fully initialized yet.", False, {}

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

    def get_function_schemas(self) -> list[Dict[str, Any]]:
        """Get function schemas for OpenAI function calling."""
        if self.tools and hasattr(self.tools, "get_function_schemas"):
            return self.tools.get_function_schemas()
        return []


def get_environment(
    db: Optional[Any] = None,
    user_db: Optional[Any] = None,
    solo_mode: bool = False,
    vector_store: Optional[VectorStore] = None,
    llm_judge: Optional[LLMJudge] = None,
    data_manager: Optional[DataManager] = None,
    openai_client: Optional[OpenAI] = None,
) -> PatientIntakeEnvironment:
    """Get the patient intake environment."""
    # Create tools
    tools = PatientIntakeTools()
    user_tools = None

    # Load policy
    policy_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "data",
        "siva",
        "domains",
        "patient_intake",
        "main_policy.md",
    )
    try:
        with open(policy_path, "r") as f:
            policy = f.read()
    except FileNotFoundError:
        policy = "Patient intake policy placeholder"

    return PatientIntakeEnvironment(
        domain_name="patient_intake",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
        openai_client=openai_client,
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
