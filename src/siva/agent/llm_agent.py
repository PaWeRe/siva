# Adapted from tau2-bench: https://github.com/sierra-research/tau2-bench
# Original file: src/tau2/agent/llm_agent.py

from copy import deepcopy
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import json
import re
from datetime import datetime

from loguru import logger
from pydantic import BaseModel, Field

from siva.agent.base import (
    LocalAgent,
    ValidAgentInputMessage,
    is_valid_agent_history_message,
)
from siva.data_model.message import (
    APICompatibleMessage,
    AssistantMessage,
    Message,
    MultiToolMessage,
    SystemMessage,
    UserMessage,
)
from siva.data_model.tasks import Action, Task
from siva.environment.tool import Tool, as_tool
from siva.utils.llm_utils import generate


class WorkflowPhase(Enum):
    """Enumeration of workflow phases for patient intake."""

    GREETING = "greeting"
    BASIC_INTAKE = "basic_intake"
    DETAILED_SYMPTOMS = "detailed_symptoms"
    ROUTING = "routing"
    ESCALATION = "escalation"
    TERMINATION = "termination"


class ValidationStatus(Enum):
    """Enumeration of validation statuses."""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_CLARIFICATION = "requires_clarification"


class PatientData(BaseModel):
    """Structured patient data with validation."""

    full_name: Optional[str] = Field(None, description="Patient's full name")
    birthday: Optional[str] = Field(None, description="Birthday in YYYY-MM-DD format")
    prescriptions: List[Dict[str, str]] = Field(
        default_factory=list, description="Current prescriptions"
    )
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    medical_conditions: List[str] = Field(
        default_factory=list, description="Medical conditions"
    )
    visit_reasons: List[str] = Field(
        default_factory=list, description="Reasons for visit"
    )
    detailed_symptoms: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed symptom information"
    )
    routing_decision: Optional[Dict[str, Any]] = Field(
        None, description="Care routing decision"
    )

    # Validation status for each field
    name_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    birthday_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    prescriptions_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    allergies_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    conditions_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    visit_reasons_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    symptoms_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)
    routing_validation: ValidationStatus = Field(default=ValidationStatus.PENDING)


class LLMAgentState(BaseModel):
    """Simplified state of the agent."""

    system_messages: list[SystemMessage]
    messages: list[APICompatibleMessage]
    current_phase: Optional[WorkflowPhase] = Field(default=None)
    patient_data: Optional[PatientData] = Field(default=None)
    phase_completion_status: Optional[Dict[str, bool]] = Field(default=None)
    conversation_start_time: Optional[datetime] = Field(default=None)
    last_activity_time: Optional[datetime] = Field(default=None)
    escalation_reason: Optional[str] = Field(default=None)
    termination_reason: Optional[str] = Field(default=None)

    def __post_init__(self):
        if self.conversation_start_time is None:
            self.conversation_start_time = datetime.now()
        if self.last_activity_time is None:
            self.last_activity_time = datetime.now()


AGENT_INSTRUCTION = """
You are a patient intake agent for Tsidi Health Services. Your job is to collect patient information systematically.

CONVERSATION FLOW:
1. Start with a proper greeting: "Hello! Welcome to Tsidi Health Services. My name is John, and I'll be helping you get checked in for your appointment today."
2. Collect information in this order: name, birthday, prescriptions, allergies, medical conditions, visit reason
3. Use tool calls to store each piece of information as you collect it
4. Complete the intake by calling determine_routing when you have all information

TOOL USAGE GUIDELINES:
- When a user provides their name, call verify_fullname with:
  {"names": [{"full_name": "John Smith"}]}
- When a user provides their birthday, call verify_birthday with:
  {"birthday": "1990-11-04"}
- When a user provides prescriptions, call list_prescriptions with:
  {"prescriptions": ["Lisinopril 10mg daily"]}
- When a user provides allergies, call list_allergies with:
  {"allergies": ["Penicillin"]}
- When a user provides medical conditions, call list_conditions with:
  {"conditions": ["Hypertension"]}
- When a user provides visit reasons, call list_visit_reasons with:
  {"visit_reasons": ["Annual checkup"]}
- When you have collected all information, call determine_routing with:
  {"route": "Routine", "reasoning": "Patient presents for routine checkup"}

CRITICAL: You must collect ALL required information before stopping. Do not stop after collecting just the name. Continue asking for birthday, prescriptions, allergies, conditions, and visit reason until you have everything. Only call determine_routing when you have collected all information.

CONVERSATION TERMINATION: After calling determine_routing successfully, conclude the conversation with a clear termination message containing one of these keywords: "goodbye", "complete", "finished", "done", "have a great day". Example: "Thank you, John. Your check-in is complete. Have a great day!"

IMPORTANT: Do not start with a generic greeting. Begin with the proper Tsidi Health Services greeting immediately.
""".strip()

SYSTEM_PROMPT = """
<instructions>
{agent_instruction}
</instructions>
<policy>
{domain_policy}
</policy>
""".strip()


class LLMAgent(LocalAgent[LLMAgentState]):
    """
    Enhanced LLM agent with workflow management and validation.
    """

    def __init__(
        self,
        tools: List[Tool],
        domain_policy: str,
        llm: Optional[str] = None,
        llm_args: Optional[dict] = None,
        max_conversation_duration: int = 1800,  # 30 minutes
        max_inactivity_duration: int = 300,  # 5 minutes
    ):
        """
        Initialize the LLMAgent.
        """
        super().__init__(tools=tools, domain_policy=domain_policy)
        self.llm = llm
        self.llm_args = deepcopy(llm_args) if llm_args is not None else {}
        self.max_conversation_duration = max_conversation_duration
        self.max_inactivity_duration = max_inactivity_duration

        # Simplified state - no complex workflow phases
        self.collected_info = {
            "name": False,
            "birthday": False,
            "prescriptions": False,
            "allergies": False,
            "conditions": False,
            "visit_reason": False,
        }

    def _add_workflow_tools(self):
        """Add workflow management tools."""

        def validate_birthday(birthday: str) -> Dict[str, Any]:
            """Validate birthday format and reasonableness."""
            try:
                # Check format
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", birthday):
                    return {"valid": False, "error": "Invalid format. Use YYYY-MM-DD"}

                # Parse date
                date_obj = datetime.strptime(birthday, "%Y-%m-%d")
                current_year = datetime.now().year

                # Check reasonableness (age between 0 and 120)
                if date_obj.year < current_year - 120 or date_obj.year > current_year:
                    return {"valid": False, "error": "Birthday seems unreasonable"}

                return {"valid": True, "message": "Birthday validated"}
            except ValueError:
                return {"valid": False, "error": "Invalid date format"}

        def validate_name(full_name: str) -> Dict[str, Any]:
            """Validate full name."""
            if not full_name or len(full_name.strip()) < 2:
                return {"valid": False, "error": "Name too short"}

            # Check for at least first and last name
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                return {"valid": False, "error": "Please provide first and last name"}

            return {"valid": True, "message": "Name validated"}

        def complete_phase(phase: str) -> Dict[str, Any]:
            """Mark a phase as complete."""
            return {
                "success": True,
                "phase": phase,
                "message": f"Phase {phase} completed",
            }

        def escalate_conversation(reason: str) -> Dict[str, Any]:
            """Escalate the conversation to human agent."""
            return {
                "success": True,
                "escalation_reason": reason,
                "message": "Conversation escalated",
            }

        def terminate_conversation(reason: str) -> Dict[str, Any]:
            """Terminate the conversation."""
            return {
                "success": True,
                "termination_reason": reason,
                "message": "Conversation terminated",
            }

        # Add tools to the list
        self.tools.extend(
            [
                as_tool(validate_birthday),
                as_tool(validate_name),
                as_tool(complete_phase),
                as_tool(escalate_conversation),
                as_tool(terminate_conversation),
            ]
        )

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            domain_policy=self.domain_policy,
            agent_instruction=AGENT_INSTRUCTION,
        )

    def _get_current_phase_description(self) -> str:
        """Get description of current phase."""
        phase_descriptions = {
            WorkflowPhase.GREETING: "Greet the patient and introduce yourself",
            WorkflowPhase.BASIC_INTAKE: "Collect basic patient information (name, birthday, prescriptions, allergies, conditions, visit reasons)",
            WorkflowPhase.DETAILED_SYMPTOMS: "Collect detailed symptom information",
            WorkflowPhase.ROUTING: "Determine appropriate care routing based on collected information",
            WorkflowPhase.ESCALATION: "Escalate to human agent if needed",
            WorkflowPhase.TERMINATION: "End the conversation appropriately",
        }
        return phase_descriptions.get(self.current_phase, "Unknown phase")

    def _get_workflow_status(self) -> str:
        """Get current workflow status."""
        status_lines = [f"Current Phase: {self.current_phase.value}"]

        # Add validation status
        data = self.patient_data
        status_lines.extend(
            [
                f"Name: {data.name_validation.value}",
                f"Birthday: {data.birthday_validation.value}",
                f"Prescriptions: {data.prescriptions_validation.value}",
                f"Allergies: {data.allergies_validation.value}",
                f"Conditions: {data.conditions_validation.value}",
                f"Visit Reasons: {data.visit_reasons_validation.value}",
                f"Symptoms: {data.symptoms_validation.value}",
                f"Routing: {data.routing_validation.value}",
            ]
        )

        return "\n".join(status_lines)

    def get_init_state(
        self, message_history: Optional[list[Message]] = None
    ) -> LLMAgentState:
        """Get the initial state of the agent."""
        if message_history is None:
            message_history = []
        assert all(
            is_valid_agent_history_message(m) for m in message_history
        ), "Message history must contain only AssistantMessage, UserMessage, or ToolMessage to Agent."

        return LLMAgentState(
            system_messages=[SystemMessage(role="system", content=self.system_prompt)],
            messages=message_history,
        )

    def generate_next_message(
        self, message: ValidAgentInputMessage, state: LLMAgentState
    ) -> tuple[AssistantMessage, LLMAgentState]:
        """
        Respond to a user or tool message with enhanced workflow management.
        """
        # Update activity time
        state.last_activity_time = datetime.now()

        # Check for timeout conditions
        if self._should_timeout(state):
            state.termination_reason = "Conversation timeout"
            state.current_phase = WorkflowPhase.TERMINATION
            return (
                AssistantMessage(
                    content="I apologize, but our conversation has timed out. Please contact us again if you need assistance."
                ),
                state,
            )

        # Add message to state
        if isinstance(message, MultiToolMessage):
            state.messages.extend(message.tool_messages)
        else:
            state.messages.append(message)

        # Generate response
        messages = state.system_messages + state.messages
        assistant_message = generate(
            model=self.llm,
            tools=self.tools,
            messages=messages,
            **self.llm_args,
        )

        # Process the response and update state
        state = self._process_response(assistant_message, state)
        state.messages.append(assistant_message)

        return assistant_message, state

    def _process_response(
        self, message: AssistantMessage, state: LLMAgentState
    ) -> LLMAgentState:
        """Process the assistant response and update workflow state."""
        if not message.is_tool_call():
            return state

        for tool_call in message.tool_calls:
            state = self._handle_tool_call(tool_call, state)

        return state

    def _handle_tool_call(self, tool_call: Any, state: LLMAgentState) -> LLMAgentState:
        """Handle individual tool calls and update state accordingly."""
        tool_name = tool_call.name
        arguments = tool_call.arguments if hasattr(tool_call, "arguments") else {}

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        # Simplified: no complex state management
        # The environment handles tool calls directly
        return state

    def _advance_phase(self, state: LLMAgentState) -> LLMAgentState:
        """Advance to the next phase if current phase is complete."""
        if state.current_phase == WorkflowPhase.GREETING:
            state.current_phase = WorkflowPhase.BASIC_INTAKE

        elif state.current_phase == WorkflowPhase.BASIC_INTAKE:
            if self._is_basic_intake_complete(state):
                state.current_phase = WorkflowPhase.DETAILED_SYMPTOMS

        elif state.current_phase == WorkflowPhase.DETAILED_SYMPTOMS:
            if self._is_detailed_symptoms_complete(state):
                state.current_phase = WorkflowPhase.ROUTING

        elif state.current_phase == WorkflowPhase.ROUTING:
            if self._is_routing_complete(state):
                state.current_phase = WorkflowPhase.TERMINATION

        return state

    def _is_basic_intake_complete(self, state: LLMAgentState) -> bool:
        """Check if basic intake phase is complete."""
        data = state.patient_data
        required_fields = [
            data.name_validation,
            data.birthday_validation,
            data.prescriptions_validation,
            data.allergies_validation,
            data.conditions_validation,
            data.visit_reasons_validation,
        ]
        return all(status == ValidationStatus.VALID for status in required_fields)

    def _is_detailed_symptoms_complete(self, state: LLMAgentState) -> bool:
        """Check if detailed symptoms phase is complete."""
        return state.patient_data.symptoms_validation == ValidationStatus.VALID

    def _is_routing_complete(self, state: LLMAgentState) -> bool:
        """Check if routing phase is complete."""
        return state.patient_data.routing_validation == ValidationStatus.VALID

    def _should_timeout(self, state: LLMAgentState) -> bool:
        """Check if conversation should timeout."""
        if not state.conversation_start_time or not state.last_activity_time:
            return False

        conversation_duration = (
            datetime.now() - state.conversation_start_time
        ).total_seconds()
        inactivity_duration = (
            datetime.now() - state.last_activity_time
        ).total_seconds()

        return (
            conversation_duration > self.max_conversation_duration
            or inactivity_duration > self.max_inactivity_duration
        )

    def is_stop(self, message: AssistantMessage) -> bool:
        """Check if the message indicates the conversation should stop."""
        # Check for termination keywords in content
        if message.content:
            termination_keywords = [
                "goodbye",
                "end call",
                "terminate",
                "complete",
                "finished",
                "done",
                "bye",
                "see you",
                "have a good day",
            ]
            content_lower = message.content.lower()
            if any(keyword in content_lower for keyword in termination_keywords):
                return True

        # Check for termination tool calls
        if message.is_tool_call():
            for tool_call in message.tool_calls:
                if tool_call.name == "terminate_conversation":
                    return True

        return False

    def set_seed(self, seed: int):
        """Set the seed for the LLM."""
        if self.llm is None:
            raise ValueError("LLM is not set")
        cur_seed = self.llm_args.get("seed", None)
        if cur_seed is not None:
            logger.warning(f"Seed is already set to {cur_seed}, resetting it to {seed}")
        self.llm_args["seed"] = seed


AGENT_GT_INSTRUCTION = """
You are testing that our user simulator is working correctly.
User simulator will have an issue for you to solve.
You must behave according to the <policy> provided below.
To make following the policy easier, we give you the list of resolution steps you are expected to take.
These steps involve either taking an action or asking the user to take an action.

In each turn you can either:
- Send a message to the user.
- Make a tool call.
You cannot do both at the same time.

Try to be helpful and always follow the policy. Always make sure you generate valid JSON only.
""".strip()

SYSTEM_PROMPT_GT = """
<instructions>
{agent_instruction}
</instructions>
<policy>
{domain_policy}
</policy>
<resolution_steps>
{resolution_steps}
</resolution_steps>
""".strip()


class LLMGTAgent(LocalAgent[LLMAgentState]):
    """
    An GroundTruth agent that can be used to solve a task.
    This agent will receive the expected actions.
    """

    def __init__(
        self,
        tools: List[Tool],
        domain_policy: str,
        task: Task,
        llm: Optional[str] = None,
        llm_args: Optional[dict] = None,
        provide_function_args: bool = True,
    ):
        """
        Initialize the LLMAgent.
        If provide_function_args is True, the resolution steps will include the function arguments.
        """
        super().__init__(tools=tools, domain_policy=domain_policy)
        assert self.check_valid_task(
            task
        ), f"Task {task.id} is not valid. Cannot run GT agent."
        self.task = task
        self.llm = llm
        self.llm_args = deepcopy(llm_args) if llm_args is not None else {}
        self.provide_function_args = provide_function_args

    @classmethod
    def check_valid_task(cls, task: Task) -> bool:
        """
        Check if the task is valid.
        Only the tasks that require at least one action are valid.
        """
        if task.evaluation_criteria is None:
            return False
        expected_actions = task.evaluation_criteria.actions or []
        if len(expected_actions) == 0:
            return False
        return True

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_GT.format(
            agent_instruction=AGENT_GT_INSTRUCTION,
            domain_policy=self.domain_policy,
            resolution_steps=self.make_agent_instructions_from_actions(),
        )

    def get_init_state(
        self, message_history: Optional[list[Message]] = None
    ) -> LLMAgentState:
        """Get the initial state of the agent.

        Args:
            message_history: The message history of the conversation.

        Returns:
            The initial state of the agent.
        """
        if message_history is None:
            message_history = []
        assert all(
            is_valid_agent_history_message(m) for m in message_history
        ), "Message history must contain only AssistantMessage, UserMessage, or ToolMessage to Agent."
        return LLMAgentState(
            system_messages=[SystemMessage(role="system", content=self.system_prompt)],
            messages=message_history,
        )

    def generate_next_message(
        self, message: ValidAgentInputMessage, state: LLMAgentState
    ) -> tuple[AssistantMessage, LLMAgentState]:
        """
        Respond to a user or tool message.
        """
        if isinstance(message, MultiToolMessage):
            state.messages.extend(message.tool_messages)
        else:
            state.messages.append(message)
        messages = state.system_messages + state.messages
        assistant_message = generate(
            model=self.llm,
            tools=self.tools,
            messages=messages,
            **self.llm_args,
        )
        state.messages.append(assistant_message)
        return assistant_message, state

    def set_seed(self, seed: int):
        """Set the seed for the LLM."""
        if self.llm is None:
            raise ValueError("LLM is not set")
        cur_seed = self.llm_args.get("seed", None)
        if cur_seed is not None:
            logger.warning(f"Seed is already set to {cur_seed}, resetting it to {seed}")
        self.llm_args["seed"] = seed

    def make_agent_instructions_from_actions(self) -> str:
        """
        Make agent instructions from a list of actions
        """
        lines = []
        for i, action in enumerate(self.task.evaluation_criteria.actions):
            lines.append(
                f"[Step {i + 1}] {self.make_agent_instructions_from_action(action=action, include_function_args=self.provide_function_args)}"
            )
        return "\n".join(lines)

    @classmethod
    def make_agent_instructions_from_action(
        cls, action: Action, include_function_args: bool = False
    ) -> str:
        """
        Make agent instructions from an action.
        If the action is a user action, returns instructions for the agent to give to the user.
        If the action is an agent action, returns instructions for the agent to perform the action.
        """
        if action.requestor == "user":
            if include_function_args:
                return f"Instruct the user to perform the following action: {action.get_func_format()}."
            else:
                return f"User action: {action.name}."
        elif action.requestor == "assistant":
            if include_function_args:
                return f"Perform the following action: {action.get_func_format()}."
            else:
                return f"Assistant action: {action.name}."
        else:
            raise ValueError(f"Unknown action requestor: {action.requestor}")


AGENT_SOLO_INSTRUCTION = """
You are a customer service agent that helps the user according to the <policy> provided below.
You will be provided with a ticket that contains the user's request.
You will need to plan and call the appropriate tools to solve the ticket.

You cannot communicate with the user, only make tool calls.
Stop when you consider that you have solved the ticket.
To do so, send a message containing a single tool call to the `{stop_function_name}` tool. Do not include any other tool calls in this last message.

Always follow the policy. Always make sure you generate valid JSON only.
""".strip()

SYSTEM_PROMPT_SOLO = """
<instructions>
{agent_instruction}
</instructions>
<policy>
{domain_policy}
</policy>
<ticket>
{ticket}
</ticket>
""".strip()


class LLMSoloAgent(LocalAgent[LLMAgentState]):
    """
    An LLM agent that can be used to solve a task without any interaction with the customer.
    The task need to specify a ticket format.
    """

    STOP_FUNCTION_NAME = "done"
    TRANSFER_TOOL_NAME = "transfer_to_human_agents"
    STOP_TOKEN = "###STOP###"

    def __init__(
        self,
        tools: List[Tool],
        domain_policy: str,
        task: Task,
        llm: Optional[str] = None,
        llm_args: Optional[dict] = None,
    ):
        """
        Initialize the LLMAgent.
        """
        super().__init__(tools=tools, domain_policy=domain_policy)
        assert self.check_valid_task(
            task
        ), f"Task {task.id} is not valid. Cannot run GT agent."
        self.task = task
        self.llm = llm
        self.llm_args = llm_args if llm_args is not None else {}
        self.add_stop_tool()
        self.validate_tools()

    def add_stop_tool(self) -> None:
        """Add the stop tool to the tools."""

        def done() -> str:
            """Call this function when you are done with the task."""
            return self.STOP_TOKEN

        self.tools.append(as_tool(done))

    def validate_tools(self) -> None:
        """Check if the tools are valid."""
        tool_names = {tool.name for tool in self.tools}
        if self.TRANSFER_TOOL_NAME not in tool_names:
            logger.warning(
                f"Tool {self.TRANSFER_TOOL_NAME} not found in tools. This tool is required for the agent to transfer the user to a human agent."
            )
        if self.STOP_FUNCTION_NAME not in tool_names:
            raise ValueError(f"Tool {self.STOP_FUNCTION_NAME} not found in tools.")

    @classmethod
    def check_valid_task(cls, task: Task) -> bool:
        """
        Check if the task is valid.
        Task should contain a ticket and evaluation criteria.
        If the task contains an initial state, the message history should only contain tool calls and responses.
        """
        if task.initial_state is not None:
            message_history = task.initial_state.message_history or []
            for message in message_history:
                if isinstance(message, UserMessage):
                    return False
                if isinstance(message, AssistantMessage) and not message.is_tool_call():
                    return False
            return True
        if task.ticket is None:
            return False
        if task.evaluation_criteria is None:
            return False
        expected_actions = task.evaluation_criteria.actions or []
        if len(expected_actions) == 0:
            return False
        return True

    @property
    def system_prompt(self) -> str:
        agent_instruction = AGENT_SOLO_INSTRUCTION.format(
            stop_function_name=self.STOP_FUNCTION_NAME,
            stop_token=self.STOP_TOKEN,
        )
        return SYSTEM_PROMPT_SOLO.format(
            agent_instruction=agent_instruction,
            domain_policy=self.domain_policy,
            ticket=self.task.ticket,
        )

    def _check_if_stop_toolcall(self, message: AssistantMessage) -> AssistantMessage:
        """Check if the message is a stop message.
        If the message contains a tool call with the name STOP_FUNCTION_NAME, then the message is a stop message.
        """
        is_stop = False
        for tool_call in message.tool_calls:
            if tool_call.name == self.STOP_FUNCTION_NAME:
                is_stop = True
                break
        if is_stop:
            message.content = self.STOP_TOKEN
            message.tool_calls = None
        return message

    @classmethod
    def is_stop(cls, message: AssistantMessage) -> bool:
        """Check if the message is a stop message."""
        if message.content is None:
            return False
        return cls.STOP_TOKEN in message.content

    def get_init_state(
        self, message_history: Optional[list[Message]] = None
    ) -> LLMAgentState:
        """Get the initial state of the agent.

        Args:
            message_history: The message history of the conversation.

        Returns:
            The initial state of the agent.
        """
        if message_history is None:
            message_history = []
        assert all(
            is_valid_agent_history_message(m) for m in message_history
        ), "Message history must contain only AssistantMessage, UserMessage, or ToolMessage to Agent."
        return LLMAgentState(
            system_messages=[SystemMessage(role="system", content=self.system_prompt)],
            messages=message_history,
        )

    def generate_next_message(
        self, message: Optional[ValidAgentInputMessage], state: LLMAgentState
    ) -> tuple[AssistantMessage, LLMAgentState]:
        """
        Respond to a user or tool message.
        """
        if isinstance(message, UserMessage):
            raise ValueError("LLMSoloAgent does not support user messages.")
        if isinstance(message, MultiToolMessage):
            state.messages.extend(message.tool_messages)
        elif message is None:
            assert len(state.messages) == 0, "Message history should be empty"
        else:
            state.messages.append(message)
        messages = state.system_messages + state.messages
        assistant_message = generate(
            model=self.llm,
            tools=self.tools,
            messages=messages,
            tool_choice="required",
            **self.llm_args,
        )
        if not assistant_message.is_tool_call():
            raise ValueError("LLMSoloAgent only supports tool calls.")
        message = self._check_if_stop_toolcall(assistant_message)
        state.messages.append(assistant_message)
        return assistant_message, state

    def set_seed(self, seed: int):
        """Set the seed for the LLM."""
        if self.llm is None:
            raise ValueError("LLM is not set")
        cur_seed = self.llm_args.get("seed", None)
        if cur_seed is not None:
            logger.warning(f"Seed is already set to {cur_seed}, resetting it to {seed}")
        self.llm_args["seed"] = seed
