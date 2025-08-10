"""
SIVA Framework - Voice-Driven Self-Improving Systems

A generalizable framework for building voice-driven AI systems that learn from human feedback.
"""

from .voice_interface import VoiceInterface
from .dual_purpose_vector_store import DualPurposeVectorStore
from .domain_knowledge_adapter import DomainKnowledgeAdapter
from .learning_pipeline import SelfImprovingPipeline
from .config import (
    SIVAConfig,
    SIVAFramework,
    VoiceConfig,
    RetrievalConfig,
    DomainConfig,
    LearningConfig,
)

__version__ = "1.0.0"
__all__ = [
    "VoiceInterface",
    "DualPurposeVectorStore",
    "DomainKnowledgeAdapter",
    "SelfImprovingPipeline",
    "SIVAConfig",
    "SIVAFramework",
    "VoiceConfig",
    "RetrievalConfig",
    "DomainConfig",
    "LearningConfig",
]
