# Adapted from tau2-bench: https://github.com/sierra-research/tau2-bench
# Original file: src/tau2/agent/base.py

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, List, Dict, Any


# For now, we'll create simple placeholder classes
# These will be replaced with proper tau2-bench imports in future phases
class Message:
    """Placeholder for tau2 Message class."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class UserMessage(Message):
    """Placeholder for tau2 UserMessage class."""

    def __init__(self, content: str):
        super().__init__("user", content)
        self.is_tool_call = lambda: False


class AssistantMessage(Message):
    """Placeholder for tau2 AssistantMessage class."""

    def __init__(self, content: str, tool_calls: Optional[List[Dict]] = None):
        super().__init__("assistant", content)
        self.tool_calls = tool_calls or []


class ToolMessage(Message):
    """Placeholder for tau2 ToolMessage class."""

    def __init__(self, content: str, requestor: str = "assistant"):
        super().__init__("tool", content)
        self.requestor = requestor


class MultiToolMessage(Message):
    """Placeholder for tau2 MultiToolMessage class."""

    def __init__(self, content: str):
        super().__init__("multitool", content)


class Tool:
    """Placeholder for tau2 Tool class."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


# Define TypeVar for the agent state type
AgentState = TypeVar("AgentState")
ValidAgentInputMessage = UserMessage | ToolMessage | MultiToolMessage


def is_valid_agent_history_message(message: Message) -> bool:
    """Check if the message is a valid agent history message."""
    return (
        isinstance(message, AssistantMessage)
        or (isinstance(message, UserMessage) and not message.is_tool_call())
        or (isinstance(message, ToolMessage) and message.requestor == "assistant")
    )


class BaseAgent(ABC, Generic[AgentState]):
    """
    Base agent class that defines the common interface for all agents.
    """

    @abstractmethod
    def generate_next_message(
        self, message: ValidAgentInputMessage, state: AgentState
    ) -> tuple[AssistantMessage, AgentState]:
        """
        Generate the next message from a user/tool message(s) and an agent state.
        Args:
            message: The user message or tool message(s).
            state: The agent state.

        Returns:
            A tuple of an assistant message and an agent state.
        """
        raise NotImplementedError

    @abstractmethod
    def get_init_state(
        self,
        message_history: Optional[list[Message]] = None,
    ) -> AgentState:
        """
        Get the initial state of the agent.
        This is required to be able to rerun an agent from any point in the conversation.
        Args:
            message_history: The message history.

        Returns:
            The initial state of the agent.
        """
        raise NotImplementedError

    @classmethod
    def is_stop(cls, message: AssistantMessage) -> bool:
        """Check if the message is a stop message.
        By default the agent does not stop.
        """
        return False

    def set_seed(self, seed: int):
        """
        Set the seed for the agent. [Optional]
        """
        print(
            f"Warning: Setting seed for agent is not implemented for class {self.__class__.__name__}"
        )


class LocalAgent(BaseAgent[AgentState]):
    """
    Local agent implementation
    Agent developers should implement the following methods:
    - generate_next_message: Generate the next message: Can be a user message or a tool call.
    - get_init_state: Get the initial state of the agent. [Optional] This is required to be able to rerun an agent from any point in the conversation.

    """

    def __init__(self, tools: list[Tool], domain_policy: str):
        super().__init__()
        self.tools = tools
        self.domain_policy = domain_policy
