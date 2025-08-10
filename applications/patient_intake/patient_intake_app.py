"""
Patient Intake Application using SIVA Framework.

Extends the framework for healthcare patient intake and routing.
"""

from typing import Dict, Any, List
from framework import (
    SIVAFramework,
    SIVAConfig,
    VoiceConfig,
    RetrievalConfig,
    DomainConfig,
    LearningConfig,
)
from framework.domain_knowledge_adapter import OpenEvidenceAdapter


class PatientIntakeApp(SIVAFramework):
    """Patient intake application using SIVA framework."""

    def __init__(self):
        # Create patient intake specific configuration
        config = SIVAConfig(
            voice=VoiceConfig(
                personality="caring_healthcare_assistant",
                voice_id="5c43e078-5ba4-4e1f-9639-8d85a403f76a",
            ),
            retrieval=RetrievalConfig(
                similarity_threshold=0.75, min_cases_for_confidence=3
            ),
            domain=DomainConfig(
                knowledge_source="openevidence_api",
                api_key_env_var="OPENEVIDENCE_API_KEY",
            ),
            learning=LearningConfig(escalation_threshold=0.6),
        )

        super().__init__(config)

        # Override domain knowledge adapter with OpenEvidence specific one
        self.domain_knowledge = OpenEvidenceAdapter(config.domain)

    def _make_decision(
        self, experience_evidence: list, domain_evidence: dict
    ) -> Dict[str, Any]:
        """Make patient routing decision based on combined evidence."""
        # Extract symptoms from experience evidence
        symptoms = self._extract_symptoms_from_evidence(experience_evidence)

        # Get routing recommendation based on symptoms
        route = self._determine_care_route(symptoms, domain_evidence)

        # Generate reasoning
        reasoning = self._generate_routing_reasoning(symptoms, route, domain_evidence)

        return {
            "route": route,
            "reasoning": reasoning,
            "symptoms": symptoms,
            "confidence": self._calculate_decision_confidence(
                experience_evidence, domain_evidence
            ),
        }

    def _extract_symptoms_from_evidence(self, experience_evidence: list) -> List[str]:
        """Extract symptoms from experience evidence."""
        symptoms = []
        for case, score in experience_evidence:
            case_data = case.get("case_data", {})
            if "symptoms" in case_data:
                symptoms.extend(case_data["symptoms"])
        return list(set(symptoms))  # Remove duplicates

    def _determine_care_route(self, symptoms: List[str], domain_evidence: dict) -> str:
        """Determine appropriate care route based on symptoms."""
        # Simple routing logic - in practice, this would be more sophisticated
        emergency_keywords = [
            "chest pain",
            "difficulty breathing",
            "stroke",
            "heart attack",
        ]
        urgent_keywords = ["high fever", "severe pain", "bleeding", "broken bone"]

        symptoms_text = " ".join(symptoms).lower()

        if any(keyword in symptoms_text for keyword in emergency_keywords):
            return "emergency"
        elif any(keyword in symptoms_text for keyword in urgent_keywords):
            return "urgent"
        else:
            return "routine"

    def _generate_routing_reasoning(
        self, symptoms: List[str], route: str, domain_evidence: dict
    ) -> str:
        """Generate reasoning for routing decision."""
        evidence_text = ""
        if domain_evidence.get("enabled", False):
            citations = domain_evidence.get("evidence", {}).get("citations", [])
            if citations:
                evidence_text = f" This recommendation is supported by {len(citations)} medical sources."

        return f"Based on symptoms {', '.join(symptoms)}, I recommend {route} care.{evidence_text}"

    def _calculate_decision_confidence(
        self, experience_evidence: list, domain_evidence: dict
    ) -> float:
        """Calculate confidence in the routing decision."""
        # Combine experience and domain evidence confidence
        experience_confidence = (
            len(experience_evidence) / self.config.retrieval.min_cases_for_confidence
        )
        domain_confidence = self.domain_knowledge.get_confidence_score(domain_evidence)

        # Weighted average
        return (experience_confidence * 0.7) + (domain_confidence * 0.3)

    def _generate_response(
        self, decision: Dict[str, Any], should_escalate: bool, domain_evidence: dict
    ) -> str:
        """Generate patient-appropriate response."""
        if should_escalate:
            return (
                "I'd like to have a healthcare professional review your symptoms "
                "to ensure you get the most appropriate care. Let me connect you with one of our specialists."
            )

        route = decision.get("route", "routine")
        reasoning = decision.get("reasoning", "")

        return f"Based on your symptoms, I recommend {route} care. {reasoning}"

    def handle_patient_feedback(
        self, session_id: str, human_route: str, human_reasoning: str
    ) -> Dict[str, Any]:
        """Handle feedback from healthcare professionals on routing decisions."""
        return self.handle_human_feedback(session_id, human_route, human_reasoning)
