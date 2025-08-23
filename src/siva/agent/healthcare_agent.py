# Copyright Sierra
"""
Healthcare Agent for SIVA patient intake system.
Integrates existing processor logic with tau2-bench agent interface.
"""

import sys
import os
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

# Add the parent directory to the path to import your existing modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.processor import UnifiedProcessor
from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from openai import OpenAI

# Import from siva package structure instead of tau2
from .base import (
    LocalAgent,
    ValidAgentInputMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    Tool,
)


class HealthcareAgentState:
    """State for the healthcare agent."""

    def __init__(self, session_data: Dict[str, Any]):
        self.session_data = session_data
        self.messages = session_data.get("messages", [])
        self.data = session_data.get("data", {})
        self.escalation_data = session_data.get("escalation_data", {})
        self.phase = session_data.get("phase", "basic_intake")
        self.mode = session_data.get("mode", "patient_intake")


class HealthcareAgent(LocalAgent[HealthcareAgentState]):
    """
    Healthcare agent for patient intake that integrates with existing SIVA processor.
    """

    def __init__(
        self,
        tools: List[Tool],
        domain_policy: str,
        vector_store: Optional[VectorStore] = None,
        llm_judge: Optional[LLMJudge] = None,
        openai_client: Optional[OpenAI] = None,
        retrieval_threshold: int = 3,
    ):
        super().__init__(tools=tools, domain_policy=domain_policy)
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.openai_client = openai_client
        self.retrieval_threshold = retrieval_threshold

        # Create a processor instance for handling the logic
        self.processor = None  # Will be initialized when needed

    def _create_processor(self, session_data: Dict[str, Any]) -> UnifiedProcessor:
        """Create a processor instance for the given session."""
        return UnifiedProcessor(
            session=session_data,
            vector_store=self.vector_store,
            llm_judge=self.llm_judge,
            openai_client=self.openai_client,
            retrieval_threshold=self.retrieval_threshold,
            current_mode="patient_intake",
        )

    def get_init_state(
        self, message_history: Optional[List[UserMessage]] = None
    ) -> HealthcareAgentState:
        """Get the initial state of the agent."""
        if message_history is None:
            message_history = []

        # Convert tau2-bench messages to our format
        messages = []
        for msg in message_history:
            if isinstance(msg, UserMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AssistantMessage):
                messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                messages.append({"role": "tool", "content": msg.content})

        # Create initial session data
        session_data = {
            "mode": "patient_intake",
            "phase": "basic_intake",
            "messages": messages,
            "data": {},
            "escalation_data": {},
        }

        # Initialize with system message if no messages
        if not messages:
            session_data["messages"] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]

        return HealthcareAgentState(session_data)

    def generate_next_message(
        self, message: ValidAgentInputMessage, state: HealthcareAgentState
    ) -> Tuple[AssistantMessage, HealthcareAgentState]:
        """Generate the next message from a user/tool message and agent state."""

        # Update state with new message
        if isinstance(message, UserMessage):
            state.session_data["messages"].append(
                {"role": "user", "content": message.content}
            )
        elif isinstance(message, ToolMessage):
            state.session_data["messages"].append(
                {"role": "tool", "content": message.content}
            )

        # Create processor for this session
        self.processor = self._create_processor(state.session_data)

        # Process the message using existing logic
        reply, end_call, escalation_info = self.processor.next_prompt(
            message.content if isinstance(message, UserMessage) else None
        )

        # Update state with processor results
        state.session_data.update(
            {
                "messages": self.processor.get_history(),
                "data": self.processor.get_data(),
                "escalation_data": self.processor.get_escalation_data(),
            }
        )

        # Create assistant message
        assistant_message = AssistantMessage(content=reply)

        # Check if this is a stop message
        if end_call:
            # Mark as stop message (we'll implement this in the base class)
            pass

        return assistant_message, state

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

    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data."""
        if self.processor:
            return {
                "messages": self.processor.get_history(),
                "data": self.processor.get_data(),
                "escalation_data": self.processor.get_escalation_data(),
            }
        return {}

    def is_stop(self, message: AssistantMessage) -> bool:
        """Check if the message indicates the conversation should stop."""
        # Check if routing decision has been made
        if self.processor:
            return self.processor.has_routing_decision()
        return False


def create_healthcare_agent(
    vector_store: Optional[VectorStore] = None,
    llm_judge: Optional[LLMJudge] = None,
    openai_client: Optional[OpenAI] = None,
    retrieval_threshold: int = 3,
) -> HealthcareAgent:
    """Create a healthcare agent with the given components."""

    # Create placeholder tools (these will be replaced with actual tools in future phases)
    tools = [
        Tool("verify_fullname", "Collect the user's full name"),
        Tool("verify_birthday", "Verify the user's birthday"),
        Tool("list_prescriptions", "Collect the user's current prescriptions"),
        Tool("list_allergies", "Collect the user's allergies"),
        Tool("list_conditions", "Collect the user's medical conditions"),
        Tool("list_visit_reasons", "Collect the user's reasons for visiting"),
        Tool("collect_detailed_symptoms", "Collect detailed symptom information"),
        Tool("determine_routing", "Determine appropriate care routing"),
    ]

    # Load policy
    policy_path = os.path.join(
        os.path.dirname(__file__),
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

    return HealthcareAgent(
        tools=tools,
        domain_policy=policy,
        vector_store=vector_store,
        llm_judge=llm_judge,
        openai_client=openai_client,
        retrieval_threshold=retrieval_threshold,
    )
