from abc import ABC, abstractmethod
from typing import Any

from siva.data_model.message import Message
from siva.data_model.simulation import RewardInfo
from siva.data_model.tasks import Task


class EvaluatorBase(ABC):
    """
    Base class for all Evaluators.
    Evaluators are responsible for evaluating a simulation.
    """

    @classmethod
    @abstractmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Message],
        **kwargs: Any,
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation.
        """
        pass
