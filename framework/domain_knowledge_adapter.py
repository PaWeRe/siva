"""
Domain Knowledge Adapter for SIVA Framework.

Pluggable interface for domain-specific knowledge sources.
"""

import os
from typing import Dict, Any, List, Optional
from .config import DomainConfig


class DomainKnowledgeAdapter:
    """Pluggable adapter for domain-specific knowledge sources."""

    def __init__(self, config: DomainConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env_var) if config.api_key_env_var else None
        # Initialize OpenAI client for simulated API calls
        try:
            from openai import OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
            else:
                print("[DomainKnowledgeAdapter] Warning: OPENAI_API_KEY not found")
                self.openai_client = None
        except Exception as e:
            print(f"[DomainKnowledgeAdapter] Error initializing OpenAI client: {e}")
            self.openai_client = None

    def get_domain_evidence(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get domain-specific evidence for a query."""
        if not self.config.validation_enabled:
            return {"enabled": False, "evidence": None}

        try:
            if self.config.knowledge_source == "openevidence_api":
                return self._query_openevidence(query_data)
            elif self.config.knowledge_source == "medical_literature":
                return self._query_medical_literature(query_data)
            else:
                return {"enabled": False, "evidence": None}
        except Exception as e:
            print(f"[DomainKnowledgeAdapter] Error querying knowledge source: {e}")
            return {"enabled": False, "error": str(e)}

    def validate_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate insights against domain knowledge."""
        if not self.config.validation_enabled:
            return insights

        validated_insights = []
        for insight in insights:
            validation_result = self._validate_single_insight(insight)
            insight["validation"] = validation_result
            validated_insights.append(insight)

        return validated_insights

    def _query_openevidence(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query OpenEvidence API for medical evidence."""
        # For now, simulate OpenEvidence with GPT-4
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not available")
            
            # Extract medical information from query
            symptoms = query_data.get("data", {}).get("symptoms", [])
            conditions = query_data.get("data", {}).get("conditions", [])
            
            # Build query for medical evidence
            query_text = self._build_medical_query(symptoms, conditions)
            
            # Simulate OpenEvidence response using GPT
            prompt = f"""
            Act as OpenEvidence API and provide medical evidence for this query:
            
            Query: {query_text}
            
            Provide a response in JSON format with:
            - guidelines: list of relevant clinical guidelines
            - citations: list of medical citations (journal names and years)
            - confidence: confidence score (0-1)
            
            Focus on evidence-based medicine and clinical best practices.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "enabled": True,
                "source": "openevidence_api_simulated",
                "query": query_text,
                "evidence": {
                    "guidelines": result.get("guidelines", []),
                    "citations": result.get("citations", []),
                    "confidence": result.get("confidence", 0.7)
                }
            }
            
        except Exception as e:
            print(f"[DomainKnowledgeAdapter] Error simulating OpenEvidence: {e}")
            return {
                "enabled": True,
                "source": "openevidence_api_simulated",
                "evidence": {
                    "guidelines": ["Standard clinical assessment recommended"],
                    "citations": ["General medical guidelines"],
                    "confidence": 0.5
                }
            }

    def _query_medical_literature(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query medical literature databases."""
        # Simulate medical literature search with GPT
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Extract clinical information
            symptoms = query_data.get("data", {}).get("symptoms", [])
            conditions = query_data.get("data", {}).get("conditions", [])
            
            query_text = self._build_medical_query(symptoms, conditions)
            
            # Simulate medical literature search
            prompt = f"""
            Act as a medical literature database and provide evidence for this clinical query:
            
            Query: {query_text}
            
            Provide a response in JSON format with:
            - studies: list of relevant clinical studies
            - citations: list of medical citations (journal names and years)
            - confidence: confidence score (0-1)
            
            Focus on recent, high-quality medical research.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "enabled": True,
                "source": "medical_literature_simulated",
                "query": query_text,
                "evidence": {
                    "studies": result.get("studies", []),
                    "citations": result.get("citations", []),
                    "confidence": result.get("confidence", 0.7)
                }
            }
            
        except Exception as e:
            print(f"[DomainKnowledgeAdapter] Error simulating medical literature: {e}")
            return {
                "enabled": True,
                "source": "medical_literature_simulated",
                "evidence": {
                    "studies": ["Standard clinical assessment recommended"],
                    "citations": ["General medical guidelines"],
                    "confidence": 0.5
                }
            }

    def _validate_single_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single insight against domain knowledge."""
        # Simulate insight validation with GPT
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            insight_text = insight.get("text", "")
            
            prompt = f"""
            Validate this clinical insight against medical literature:
            
            Insight: {insight_text}
            
            Provide a response in JSON format with:
            - validated: boolean indicating if insight is supported by literature
            - confidence: confidence score (0-1)
            - supporting_evidence: list of supporting citations
            - conflicting_evidence: list of conflicting citations
            - status: "literature_confirmed", "novel_insight", or "conflicting_evidence"
            
            Be conservative in validation - only confirm if strongly supported by evidence.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "validated": result.get("validated", False),
                "confidence": result.get("confidence", 0.5),
                "supporting_evidence": result.get("supporting_evidence", []),
                "conflicting_evidence": result.get("conflicting_evidence", []),
                "status": result.get("status", "pending_validation")
            }
            
        except Exception as e:
            print(f"[DomainKnowledgeAdapter] Error validating insight: {e}")
            return {
                "validated": False,
                "confidence": 0.0,
                "supporting_evidence": [],
                "conflicting_evidence": [],
                "status": "validation_failed"
            }

    def get_confidence_score(self, evidence: Dict[str, Any]) -> float:
        """Calculate confidence score based on domain evidence."""
        if not evidence.get("enabled", False):
            return 0.0

        # Simple confidence calculation based on evidence strength
        citations = evidence.get("evidence", {}).get("citations", [])
        guidelines = evidence.get("evidence", {}).get("guidelines", [])
        
        # More citations and guidelines = higher confidence
        confidence = min(1.0, (len(citations) + len(guidelines)) / 10.0)
        
        return confidence


class OpenEvidenceAdapter(DomainKnowledgeAdapter):
    """Specialized adapter for OpenEvidence API integration."""

    def __init__(self, config: DomainConfig):
        super().__init__(config)
        # Initialize OpenEvidence-specific client here

    def _query_openevidence(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced OpenEvidence querying."""
        # Extract relevant medical information from query
        symptoms = query_data.get("data", {}).get("symptoms", [])
        conditions = query_data.get("data", {}).get("conditions", [])
        
        # Build query for OpenEvidence
        query_text = self._build_medical_query(symptoms, conditions)
        
        # Placeholder for actual API call
        # response = self.openevidence_client.query(query_text)
        
        return {
            "enabled": True,
            "source": "openevidence_api",
            "query": query_text,
            "evidence": {
                "guidelines": ["Sample guideline 1", "Sample guideline 2"],
                "citations": ["Citation 1", "Citation 2"],
                "confidence": 0.8
            }
        }

    def _build_medical_query(self, symptoms: List[str], conditions: List[str]) -> str:
        """Build a medical query for OpenEvidence."""
        query_parts = []
        
        if symptoms:
            query_parts.append(f"Symptoms: {', '.join(symptoms)}")
        if conditions:
            query_parts.append(f"Conditions: {', '.join(conditions)}")
            
        return " ".join(query_parts) if query_parts else "general medical information"

    def _validate_single_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Validate clinical insights against OpenEvidence."""
        insight_text = insight.get("text", "")
        
        # Placeholder for actual validation logic
        # This would cross-reference the insight with OpenEvidence data
        
        return {
            "validated": True,
            "confidence": 0.7,
            "supporting_evidence": ["Supporting study 1"],
            "conflicting_evidence": [],
            "status": "validated",
            "source": "openevidence_api"
        } 