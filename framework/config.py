"""
Configuration system for SIVA Framework.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

# Import components after they're defined


@dataclass
class VoiceConfig:
    """Voice interface configuration."""

    personality: str = "helpful_assistant"
    stt_model: str = "whisper-1"
    tts_model: str = "sonic-2"
    voice_id: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 300


@dataclass
class RetrievalConfig:
    """Dual-purpose vector store configuration."""

    similarity_threshold: float = 0.75
    min_cases_for_confidence: int = 3
    max_retrieved_cases: int = 5
    embedding_model: str = "text-embedding-3-small"


@dataclass
class DomainConfig:
    """Domain-specific knowledge configuration."""

    knowledge_source: str = "none"
    api_key_env_var: Optional[str] = None
    validation_enabled: bool = True
    confidence_threshold: float = 0.7


@dataclass
class LearningConfig:
    """Learning pipeline configuration."""

    escalation_threshold: float = 0.6
    auto_extract_insights: bool = True
    validation_required: bool = True
    outcome_tracking: bool = True


@dataclass
class SIVAConfig:
    """Complete SIVA framework configuration."""

    voice: VoiceConfig
    retrieval: RetrievalConfig
    domain: DomainConfig
    learning: LearningConfig

    def __post_init__(self):
        """Validate and set up configuration."""
        if self.domain.api_key_env_var and not os.getenv(self.domain.api_key_env_var):
            print(f"Warning: {self.domain.api_key_env_var} not found in environment")


class SIVAFramework:
    """Main framework class that orchestrates all components."""

    def __init__(self, config: SIVAConfig):
        self.config = config
        # Import here to avoid circular imports
        from .voice_interface import VoiceInterface
        from .dual_purpose_vector_store import DualPurposeVectorStore
        from .domain_knowledge_adapter import DomainKnowledgeAdapter
        from .learning_pipeline import SelfImprovingPipeline

        self.voice_interface = VoiceInterface(config.voice)
        self.vector_store = DualPurposeVectorStore(config.retrieval)
        self.domain_knowledge = DomainKnowledgeAdapter(config.domain)
        self.learning_pipeline = SelfImprovingPipeline(config.learning)

    def process_interaction(self, voice_input: bytes) -> Dict[str, Any]:
        """Process a complete voice interaction."""
        # 1. Voice processing
        text_input = self.voice_interface.process_voice_input(voice_input)

        # 2. Intent classification and data extraction
        extracted_data = self.voice_interface.extract_intent_and_data(text_input)

        # 3. Dual evidence retrieval
        experience_evidence = self.vector_store.get_similar_cases(extracted_data)
        domain_evidence = self.domain_knowledge.get_domain_evidence(extracted_data)

        # 4. Confidence assessment
        # TODO: confidence should be based on a mixture of domain and experience
        confidence = self.vector_store.assess_confidence(experience_evidence)

        # 5. Decision making
        if confidence >= self.config.learning.escalation_threshold:
            decision = self._make_decision(experience_evidence, domain_evidence)
            should_escalate = False
        else:
            decision = None
            should_escalate = True

        # 6. Generate response
        response_text = self._generate_response(
            decision, should_escalate, domain_evidence
        )
        voice_response = self.voice_interface.generate_voice_response(response_text)

        return {
            "text_input": text_input,
            "extracted_data": extracted_data,
            "experience_evidence": experience_evidence,
            "domain_evidence": domain_evidence,
            "confidence": confidence,
            "decision": decision,
            "should_escalate": should_escalate,
            "response_text": response_text,
            "voice_response": voice_response,
        }

    def handle_human_feedback(
        self, interaction_id: str, human_decision: Any, human_reasoning: str
    ) -> Dict[str, Any]:
        """Process human feedback and update knowledge base."""
        # Extract insights from human correction
        insights = self.learning_pipeline.extract_knowledge(
            human_decision, human_reasoning
        )

        # Validate insights against domain knowledge
        validated_insights = self.domain_knowledge.validate_insights(insights)

        # Update knowledge base
        self.learning_pipeline.update_knowledge_base(validated_insights)

        # Update vector store with new example
        self.vector_store.add_case(validated_insights)

        return {
            "insights_extracted": insights,
            "validated_insights": validated_insights,
            "knowledge_updated": True,
        }

    def _make_decision(self, experience_evidence: list, domain_evidence: dict) -> Any:
        """Make decision based on combined evidence."""
        # This would be implemented by specific applications
        raise NotImplementedError("Subclasses must implement _make_decision")

    def _generate_response(
        self, decision: Any, should_escalate: bool, domain_evidence: dict
    ) -> str:
        """Generate appropriate response text."""
        if should_escalate:
            return "I'd like to have a human expert review this case to ensure you get the best care."
        else:
            return f"Based on the available evidence, I recommend: {decision}"


# Pre-configured setups for common use cases
def create_patient_intake_config() -> SIVAConfig:
    """Configuration for patient intake automation."""
    return SIVAConfig(
        voice=VoiceConfig(
            personality="caring_healthcare_assistant",
            voice_id="5c43e078-5ba4-4e1f-9639-8d85a403f76a",
        ),
        retrieval=RetrievalConfig(
            similarity_threshold=0.75, min_cases_for_confidence=3
        ),
        domain=DomainConfig(
            knowledge_source="openevidence_api", api_key_env_var="OPENEVIDENCE_API_KEY"
        ),
        learning=LearningConfig(escalation_threshold=0.6),
    )


def create_clinical_pearls_config() -> SIVAConfig:
    """Configuration for clinical pearl collection."""
    return SIVAConfig(
        voice=VoiceConfig(personality="clinical_decision_support", temperature=0.2),
        retrieval=RetrievalConfig(similarity_threshold=0.8, min_cases_for_confidence=5),
        domain=DomainConfig(
            knowledge_source="medical_literature",
            api_key_env_var="OPENEVIDENCE_API_KEY",
            validation_enabled=True,
        ),
        learning=LearningConfig(
            escalation_threshold=0.7,
            auto_extract_insights=True,
            validation_required=True,
        ),
    )
