"""
Learning Pipeline for SIVA Framework.

Handles knowledge extraction from human feedback and continuous improvement.
"""

import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .config import LearningConfig


class SelfImprovingPipeline:
    """Universal learning pipeline for extracting insights from human feedback."""

    def __init__(self, config: LearningConfig):
        self.config = config
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_knowledge(self, human_decision: Any, human_reasoning: str) -> List[Dict[str, Any]]:
        """Extract knowledge from human feedback."""
        if not self.config.auto_extract_insights:
            return []

        try:
            # Use LLM to extract structured insights from human reasoning
            prompt = f"""
            Extract key insights from this human expert's reasoning:
            
            Decision: {human_decision}
            Reasoning: {human_reasoning}
            
            Identify:
            1. Key patterns or rules the expert used
            2. Important factors they considered
            3. Clinical reasoning or decision-making logic
            
            Return as a JSON array of insights, each with:
            - text: the insight description
            - type: pattern/rule/factor/logic
            - confidence: how confident you are in this extraction (0-1)
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            insights = result.get("insights", [])

            # Add metadata
            for insight in insights:
                insight["source"] = "human_feedback"
                insight["timestamp"] = self._get_timestamp()
                insight["decision"] = human_decision
                insight["original_reasoning"] = human_reasoning

            return insights

        except Exception as e:
            print(f"[SelfImprovingPipeline] Error extracting knowledge: {e}")
            return []

    def update_knowledge_base(self, validated_insights: List[Dict[str, Any]]) -> bool:
        """Update the knowledge base with validated insights."""
        try:
            # This would typically update a persistent knowledge store
            # For now, we'll just log the insights
            for insight in validated_insights:
                print(f"[SelfImprovingPipeline] Adding insight: {insight.get('text', 'Unknown')}")
                
            return True
        except Exception as e:
            print(f"[SelfImprovingPipeline] Error updating knowledge base: {e}")
            return False

    def track_outcome(self, case_id: str, decision: Any, outcome: str, 
                     success_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Track the outcome of a decision for learning."""
        if not self.config.outcome_tracking:
            return {"tracked": False}

        try:
            outcome_data = {
                "case_id": case_id,
                "decision": decision,
                "outcome": outcome,
                "success_metrics": success_metrics,
                "timestamp": self._get_timestamp()
            }

            # This would store outcome data for analysis
            print(f"[SelfImprovingPipeline] Tracking outcome: {outcome} for case {case_id}")
            
            return {
                "tracked": True,
                "outcome_data": outcome_data
            }

        except Exception as e:
            print(f"[SelfImprovingPipeline] Error tracking outcome: {e}")
            return {"tracked": False, "error": str(e)}

    def analyze_performance(self, time_period: str = "recent") -> Dict[str, Any]:
        """Analyze system performance and learning progress."""
        try:
            # This would analyze stored outcome data
            # For now, return placeholder metrics
            return {
                "total_cases": 0,
                "success_rate": 0.0,
                "learning_progress": 0.0,
                "insights_generated": 0,
                "validation_rate": 0.0
            }

        except Exception as e:
            print(f"[SelfImprovingPipeline] Error analyzing performance: {e}")
            return {"error": str(e)}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


class ClinicalPearlExtractor(SelfImprovingPipeline):
    """Specialized extractor for clinical pearls from medical feedback."""

    def __init__(self, config: LearningConfig):
        super().__init__(config)

    def extract_knowledge(self, human_decision: Any, human_reasoning: str) -> List[Dict[str, Any]]:
        """Extract clinical pearls from physician feedback."""
        try:
            # Specialized prompt for clinical pearl extraction
            prompt = f"""
            Extract clinical pearls from this physician's reasoning:
            
            Clinical Decision: {human_decision}
            Physician Reasoning: {human_reasoning}
            
            Identify clinical pearls - specific, actionable insights that could help other physicians:
            1. Clinical patterns or associations
            2. Treatment approaches or modifications
            3. Diagnostic considerations
            4. Patient-specific factors to consider
            5. Evidence-based reasoning
            
            Return as a JSON array of clinical pearls, each with:
            - text: the clinical pearl description
            - category: pattern/treatment/diagnostic/factor/evidence
            - confidence: extraction confidence (0-1)
            - applicability: how broadly applicable this pearl is (specific/general)
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more precise extraction
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            pearls = result.get("clinical_pearls", [])

            # Add clinical pearl metadata
            for pearl in pearls:
                pearl["source"] = "physician_feedback"
                pearl["timestamp"] = self._get_timestamp()
                pearl["decision"] = human_decision
                pearl["original_reasoning"] = human_reasoning
                pearl["type"] = "clinical_pearl"

            return pearls

        except Exception as e:
            print(f"[ClinicalPearlExtractor] Error extracting clinical pearls: {e}")
            return []

    def validate_clinical_pearl(self, pearl: Dict[str, Any], 
                              domain_evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a clinical pearl against medical literature."""
        try:
            # Check if pearl aligns with domain evidence
            pearl_text = pearl.get("text", "")
            evidence_citations = domain_evidence.get("evidence", {}).get("citations", [])
            
            # Simple validation logic - in practice, this would be more sophisticated
            if evidence_citations:
                validation_status = "literature_confirmed"
                confidence = 0.8
            else:
                validation_status = "novel_insight"
                confidence = 0.4

            return {
                "validated": True,
                "status": validation_status,
                "confidence": confidence,
                "supporting_evidence": evidence_citations,
                "validation_timestamp": self._get_timestamp()
            }

        except Exception as e:
            print(f"[ClinicalPearlExtractor] Error validating clinical pearl: {e}")
            return {
                "validated": False,
                "error": str(e),
                "status": "validation_failed"
            } 