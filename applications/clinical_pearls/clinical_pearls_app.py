"""
Clinical Pearls Application using SIVA Framework.

Extends the framework for clinical pearl collection and medical decision support.
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
from framework.learning_pipeline import ClinicalPearlExtractor


class ClinicalPearlsApp(SIVAFramework):
    """Clinical pearls application using SIVA framework."""

    def __init__(self):
        # Create clinical pearls specific configuration
        config = SIVAConfig(
            voice=VoiceConfig(personality="clinical_decision_support", temperature=0.2),
            retrieval=RetrievalConfig(
                similarity_threshold=0.8, min_cases_for_confidence=5
            ),
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

        super().__init__(config)

        # Override components with clinical pearls specific ones
        self.domain_knowledge = OpenEvidenceAdapter(config.domain)
        self.learning_pipeline = ClinicalPearlExtractor(config.learning)

    def _make_decision(
        self, experience_evidence: list, domain_evidence: dict
    ) -> Dict[str, Any]:
        """Make clinical decision based on combined evidence."""
        # Extract clinical patterns from experience evidence
        clinical_patterns = self._extract_clinical_patterns(experience_evidence)

        # Get clinical recommendation based on patterns and literature
        recommendation = self._generate_clinical_recommendation(
            clinical_patterns, domain_evidence
        )

        # Generate evidence-based reasoning
        reasoning = self._generate_clinical_reasoning(
            clinical_patterns, recommendation, domain_evidence
        )

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "clinical_patterns": clinical_patterns,
            "evidence_level": self._determine_evidence_level(domain_evidence),
            "confidence": self._calculate_decision_confidence(
                experience_evidence, domain_evidence
            ),
        }

    def _extract_clinical_patterns(
        self, experience_evidence: list
    ) -> List[Dict[str, Any]]:
        """Extract clinical patterns from experience evidence."""
        patterns = []
        for case, score in experience_evidence:
            case_data = case.get("case_data", {})
            if "clinical_pearls" in case_data:
                patterns.extend(case_data["clinical_pearls"])
        return patterns

    def _generate_clinical_recommendation(
        self, clinical_patterns: List[Dict[str, Any]], domain_evidence: dict
    ) -> str:
        """Generate clinical recommendation based on patterns and evidence."""
        # This would be more sophisticated in practice
        if clinical_patterns:
            # Use the most relevant clinical pearl
            best_pattern = max(clinical_patterns, key=lambda p: p.get("confidence", 0))
            return best_pattern.get("text", "Consider clinical assessment")
        else:
            return "Standard clinical assessment recommended"

    def _generate_clinical_reasoning(
        self,
        clinical_patterns: List[Dict[str, Any]],
        recommendation: str,
        domain_evidence: dict,
    ) -> str:
        """Generate evidence-based clinical reasoning."""
        evidence_text = ""
        if domain_evidence.get("enabled", False):
            citations = domain_evidence.get("evidence", {}).get("citations", [])
            if citations:
                evidence_text = f" This approach is supported by {len(citations)} peer-reviewed sources."

        pattern_text = ""
        if clinical_patterns:
            pattern_text = (
                f" Clinical experience suggests: {clinical_patterns[0].get('text', '')}"
            )

        return f"{recommendation}.{pattern_text}{evidence_text}"

    def _determine_evidence_level(self, domain_evidence: dict) -> str:
        """Determine the level of evidence supporting the recommendation."""
        if not domain_evidence.get("enabled", False):
            return "expert_opinion"

        citations = domain_evidence.get("evidence", {}).get("citations", [])
        if len(citations) >= 5:
            return "strong_evidence"
        elif len(citations) >= 2:
            return "moderate_evidence"
        else:
            return "limited_evidence"

    def _calculate_decision_confidence(
        self, experience_evidence: list, domain_evidence: dict
    ) -> float:
        """Calculate confidence in the clinical decision."""
        # Higher weight on domain evidence for clinical decisions
        experience_confidence = (
            len(experience_evidence) / self.config.retrieval.min_cases_for_confidence
        )
        domain_confidence = self.domain_knowledge.get_confidence_score(domain_evidence)

        # Weighted average favoring literature evidence
        return (experience_confidence * 0.3) + (domain_confidence * 0.7)

    def _generate_response(
        self, decision: Dict[str, Any], should_escalate: bool, domain_evidence: dict
    ) -> str:
        """Generate physician-appropriate response."""
        if should_escalate:
            return (
                "I'd recommend consulting with a colleague or specialist "
                "to ensure the best clinical approach for this case."
            )

        recommendation = decision.get("recommendation", "")
        reasoning = decision.get("reasoning", "")
        evidence_level = decision.get("evidence_level", "")

        return f"Clinical recommendation: {recommendation}. {reasoning} (Evidence level: {evidence_level})"

    def extract_clinical_pearl(
        self, physician_decision: str, physician_reasoning: str
    ) -> Dict[str, Any]:
        """Extract clinical pearl from physician feedback."""
        # Use the specialized clinical pearl extractor
        pearls = self.learning_pipeline.extract_knowledge(
            physician_decision, physician_reasoning
        )

        if pearls:
            # Validate the first pearl against domain evidence
            pearl = pearls[0]
            validation = self.learning_pipeline.validate_clinical_pearl(pearl, {})

            return {"pearl": pearl, "validation": validation, "extracted": True}

        return {"extracted": False, "pearls": pearls}

    def handle_physician_feedback(
        self, session_id: str, physician_decision: str, physician_reasoning: str
    ) -> Dict[str, Any]:
        """Handle feedback from physicians and extract clinical pearls."""
        # Extract clinical pearl
        pearl_result = self.extract_clinical_pearl(
            physician_decision, physician_reasoning
        )

        # Update knowledge base
        if pearl_result.get("extracted", False):
            pearl = pearl_result["pearl"]
            self.vector_store.add_case(pearl, outcome=physician_decision)

        return {
            "clinical_pearl_extracted": pearl_result.get("extracted", False),
            "pearl_data": pearl_result,
            "knowledge_updated": True,
        }
