# Copyright Sierra

from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Import your existing components (we'll keep them for now)
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from core.data_manager import DataManager
from core.processor import UnifiedProcessor
from openai import OpenAI

from siva.agent.llm_agent import WorkflowPhase, ValidationStatus, PatientData
from siva.data_model.message import Message, UserMessage, AssistantMessage, ToolMessage
from siva.data_model.tasks import Task
from siva.environment.tool import Tool, as_tool
from siva.environment.environment import EnvironmentInfo
from .utils import PATIENT_INTAKE_TASK_SET_PATH


class Environment:
    """Placeholder for tau2 Environment class."""

    def __init__(self, domain_name: str, policy: str, tools: Any, user_tools: Any):
        self.domain_name = domain_name
        self.policy = policy
        self.tools = tools
        self.user_tools = user_tools


def load_file(path: str) -> Any:
    """Load file content, parsing JSON if it's a JSON file."""
    try:
        with open(path, "r") as f:
            if str(path).endswith(".json"):
                import json

                return json.load(f)
            else:
                return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"


from .tools import PatientIntakeTools


class PatientIntakeEnvironment(Environment):
    """Patient intake environment for healthcare domain with tau2-bench workflow."""

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
        solo_mode: bool = False,
    ):
        super().__init__(domain_name, policy, tools, user_tools)
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.data_manager = data_manager
        self.openai_client = openai_client
        self.solo_mode = solo_mode

        # Initialize workflow state
        self.current_phase = WorkflowPhase.GREETING
        self.patient_data = PatientData()
        self.session_data: Dict[str, Any] = {
            "mode": "patient_intake",
            "phase": self.current_phase.value,
            "messages": [],
            "data": {},
            "escalation_data": {},
            "conversation_start_time": datetime.now().isoformat(),
            "last_activity_time": datetime.now().isoformat(),
        }

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
            "phase": self.current_phase.value,
            "messages": message_history,
            "data": initialization_data or {},
            "escalation_data": {},
            "session_id": (
                initialization_data.get("session_id", "default")
                if initialization_data
                else "default"
            ),
            "conversation_start_time": datetime.now().isoformat(),
            "last_activity_time": datetime.now().isoformat(),
        }

        # Initialize patient data from initialization data
        if initialization_data:
            self.patient_data.full_name = initialization_data.get("full_name")
            self.patient_data.birthday = initialization_data.get("birthday")
            self.patient_data.prescriptions = initialization_data.get(
                "prescriptions", []
            )
            self.patient_data.allergies = initialization_data.get("allergies", [])
            self.patient_data.medical_conditions = initialization_data.get(
                "medical_conditions", []
            )
            self.patient_data.visit_reasons = initialization_data.get(
                "visit_reasons", []
            )
            self.patient_data.detailed_symptoms = initialization_data.get(
                "detailed_symptoms", []
            )

        # Initialize with system message if not present
        if not message_history:
            self.session_data["messages"] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]

        # Update tools session data
        if self.tools and hasattr(self.tools, "session_data"):
            self.tools.session_data = self.session_data

    def get_response(self, tool_call) -> "ToolMessage":
        """Get response for a tool call."""
        from siva.data_model.message import ToolMessage

        # Handle both ToolCall objects and dictionaries
        if hasattr(tool_call, "name"):
            function_name = tool_call.name
            arguments = tool_call.arguments
            tool_call_id = tool_call.id
            requestor = tool_call.requestor
        else:
            function_name = tool_call.get("name", "")
            arguments = tool_call.get("arguments", {})
            tool_call_id = tool_call.get("id", "")
            requestor = tool_call.get("requestor", "assistant")

        # First try to find the tool in the domain tools
        if hasattr(self.tools, function_name):
            method = getattr(self.tools, function_name)
            try:
                result = method(**arguments)

                # Update patient data based on tool call
                self._update_patient_data(function_name, arguments, result)

                # Convert result to string content
                if isinstance(result, dict):
                    content = json.dumps(result, indent=2)
                else:
                    content = str(result)

                return ToolMessage(
                    id=tool_call_id,
                    role="tool",
                    content=content,
                    requestor=requestor,
                    error=False,
                )
            except Exception as e:
                return ToolMessage(
                    id=tool_call_id,
                    role="tool",
                    content=f"Error calling {function_name}: {str(e)}",
                    requestor=requestor,
                    error=True,
                )

        # If not found in domain tools, handle workflow tools
        elif function_name == "escalate_conversation":
            reason = arguments.get("reason", "Unknown reason")
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=json.dumps(
                    {
                        "success": True,
                        "escalation_reason": reason,
                        "message": "Conversation escalated",
                    },
                    indent=2,
                ),
                requestor=requestor,
                error=False,
            )
        elif function_name == "terminate_conversation":
            reason = arguments.get("reason", "Unknown reason")
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=json.dumps(
                    {
                        "success": True,
                        "termination_reason": reason,
                        "message": "Conversation terminated",
                    },
                    indent=2,
                ),
                requestor=requestor,
                error=False,
            )
        elif function_name == "complete_phase":
            phase = arguments.get("phase", "unknown")
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=json.dumps(
                    {
                        "success": True,
                        "phase": phase,
                        "message": f"Phase {phase} completed",
                    },
                    indent=2,
                ),
                requestor=requestor,
                error=False,
            )
        elif function_name == "validate_birthday":
            birthday = arguments.get("birthday", "")
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=json.dumps(
                    {"valid": True, "message": "Birthday validated"}, indent=2
                ),
                requestor=requestor,
                error=False,
            )
        elif function_name == "validate_name":
            full_name = arguments.get("full_name", "")
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=json.dumps(
                    {"valid": True, "message": "Name validated"}, indent=2
                ),
                requestor=requestor,
                error=False,
            )
        else:
            return ToolMessage(
                id=tool_call_id,
                role="tool",
                content=f"Unknown tool call: {function_name}",
                requestor=requestor,
                error=True,
            )

    def _update_patient_data(
        self, function_name: str, arguments: Dict[str, Any], result: Dict[str, Any]
    ):
        """Update patient data based on tool call results."""
        if result.get("success", False):
            if function_name == "verify_fullname":
                self.patient_data.full_name = arguments.get("names", [{}])[0].get(
                    "full_name", ""
                )
                self.patient_data.name_validation = ValidationStatus.VALID
            elif function_name == "verify_birthday":
                self.patient_data.birthday = arguments.get("birthday", "")
                self.patient_data.birthday_validation = ValidationStatus.VALID
            elif function_name == "list_prescriptions":
                self.patient_data.prescriptions = arguments.get("prescriptions", [])
                self.patient_data.prescriptions_validation = ValidationStatus.VALID
            elif function_name == "list_allergies":
                self.patient_data.allergies = arguments.get("allergies", [])
                self.patient_data.allergies_validation = ValidationStatus.VALID
            elif function_name == "list_conditions":
                self.patient_data.medical_conditions = arguments.get("conditions", [])
                self.patient_data.conditions_validation = ValidationStatus.VALID
            elif function_name == "list_visit_reasons":
                self.patient_data.visit_reasons = arguments.get("visit_reasons", [])
                self.patient_data.visit_reasons_validation = ValidationStatus.VALID
            elif function_name == "collect_detailed_symptoms":
                self.patient_data.detailed_symptoms = arguments.get("symptoms", [])
                self.patient_data.symptoms_validation = ValidationStatus.VALID
            elif function_name == "determine_routing":
                self.patient_data.routing_decision = {
                    "route": arguments.get("route", ""),
                    "reasoning": arguments.get("reasoning", ""),
                }
                self.patient_data.routing_validation = ValidationStatus.VALID

        # Update session data
        self.session_data["data"] = self.patient_data.dict()
        self.session_data["last_activity_time"] = datetime.now().isoformat()

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

    def sync_tools(self):
        """Sync tools with current state."""
        if self.tools and hasattr(self.tools, "session_data"):
            self.tools.session_data = self.session_data

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "current_phase": self.current_phase.value,
            "patient_data": self.patient_data.dict(),
            "session_data": self.session_data,
            "validation_status": {
                "name": self.patient_data.name_validation.value,
                "birthday": self.patient_data.birthday_validation.value,
                "prescriptions": self.patient_data.prescriptions_validation.value,
                "allergies": self.patient_data.allergies_validation.value,
                "conditions": self.patient_data.conditions_validation.value,
                "visit_reasons": self.patient_data.visit_reasons_validation.value,
                "symptoms": self.patient_data.symptoms_validation.value,
                "routing": self.patient_data.routing_validation.value,
            },
        }

    def advance_phase(self):
        """Advance to the next workflow phase."""
        if self.current_phase == WorkflowPhase.GREETING:
            self.current_phase = WorkflowPhase.BASIC_INTAKE
        elif self.current_phase == WorkflowPhase.BASIC_INTAKE:
            if self._is_basic_intake_complete():
                self.current_phase = WorkflowPhase.DETAILED_SYMPTOMS
        elif self.current_phase == WorkflowPhase.DETAILED_SYMPTOMS:
            if self._is_detailed_symptoms_complete():
                self.current_phase = WorkflowPhase.ROUTING
        elif self.current_phase == WorkflowPhase.ROUTING:
            if self._is_routing_complete():
                self.current_phase = WorkflowPhase.TERMINATION

        # Update session data
        self.session_data["phase"] = self.current_phase.value

    def _is_basic_intake_complete(self) -> bool:
        """Check if basic intake phase is complete."""
        required_fields = [
            self.patient_data.name_validation,
            self.patient_data.birthday_validation,
            self.patient_data.prescriptions_validation,
            self.patient_data.allergies_validation,
            self.patient_data.conditions_validation,
            self.patient_data.visit_reasons_validation,
        ]
        return all(status == ValidationStatus.VALID for status in required_fields)

    def _is_detailed_symptoms_complete(self) -> bool:
        """Check if detailed symptoms phase is complete."""
        return self.patient_data.symptoms_validation == ValidationStatus.VALID

    def _is_routing_complete(self) -> bool:
        """Check if routing phase is complete."""
        return self.patient_data.routing_validation == ValidationStatus.VALID

    def get_info(self, include_tool_info: bool = False) -> EnvironmentInfo:
        """Get environment information."""
        return EnvironmentInfo(
            domain_name=self.domain_name,
            policy=self.policy,
            tools=(
                self.tools.get_function_schemas()
                if hasattr(self.tools, "get_function_schemas")
                else []
            ),
            user_tools=(
                self.user_tools.get_function_schemas()
                if self.user_tools and hasattr(self.user_tools, "get_function_schemas")
                else []
            ),
        )

    def get_tools(self) -> list[Tool]:
        """Get environment tools."""
        return self.tools.get_tools() if hasattr(self.tools, "get_tools") else []

    def get_user_tools(self) -> list[Tool]:
        """Get user tools."""
        return (
            self.user_tools.get_tools()
            if self.user_tools and hasattr(self.user_tools, "get_tools")
            else []
        )

    def get_policy(self) -> str:
        """Get domain policy."""
        return self.policy

    def get_db_hash(self) -> str:
        """Get database hash for evaluation."""
        return "patient_intake_db_hash"

    def get_user_db_hash(self) -> str:
        """Get user database hash for evaluation."""
        return "patient_intake_user_db_hash"


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
        "main_policy_solo.md" if solo_mode else "main_policy.md",
    )
    policy = load_file(policy_path)

    # Create tools
    tools = PatientIntakeTools()

    # Create user tools (placeholder for now)
    user_tools = None

    return PatientIntakeEnvironment(
        domain_name="patient_intake",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
        openai_client=openai_client,
        solo_mode=solo_mode,
    )


def get_environment_manual_policy(
    db: Optional[Any] = None,
    user_db: Optional[Any] = None,
    solo_mode: bool = False,
    vector_store: Optional[VectorStore] = None,
    llm_judge: Optional[LLMJudge] = None,
    data_manager: Optional[DataManager] = None,
    openai_client: Optional[OpenAI] = None,
) -> PatientIntakeEnvironment:
    """Get the patient intake environment with manual policy."""
    return get_environment(
        db=db,
        user_db=user_db,
        solo_mode=solo_mode,
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
        openai_client=openai_client,
    )


def get_environment_workflow_policy(
    db: Optional[Any] = None,
    user_db: Optional[Any] = None,
    solo_mode: bool = False,
    vector_store: Optional[VectorStore] = None,
    llm_judge: Optional[LLMJudge] = None,
    data_manager: Optional[DataManager] = None,
    openai_client: Optional[OpenAI] = None,
) -> PatientIntakeEnvironment:
    """Get the patient intake environment with workflow policy."""
    return get_environment(
        db=db,
        user_db=user_db,
        solo_mode=solo_mode,
        vector_store=vector_store,
        llm_judge=llm_judge,
        data_manager=data_manager,
        openai_client=openai_client,
    )


def load_tasks(path: str) -> list[Task]:
    """Load tasks from a data file, could be json, yaml or toml file."""
    tasks = load_file(path)
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    return [Task(**task) for task in tasks]


def get_tasks_full() -> list[Task]:
    return load_tasks(PATIENT_INTAKE_TASK_SET_PATH)


def get_tasks_small() -> list[Task]:
    return load_tasks(PATIENT_INTAKE_TASK_SET_PATH)


def get_tasks() -> list[Task]:
    return load_tasks(PATIENT_INTAKE_TASK_SET_PATH)


if __name__ == "__main__":
    env = get_environment()
    # print(env.get_tools())
    for tool in env.get_user_tools():
        print(tool.name)
