"""Enhanced UnifiedProcessor with routing and escalation capabilities."""

import json
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI

from .vector_store import VectorStore
from .llm_judge import LLMJudge
from .schemas import FUNCTION_SCHEMAS


class UnifiedProcessor:
    """Main processor for handling patient conversations and routing decisions."""

    def __init__(
        self,
        session: Dict[str, Any],
        vector_store: VectorStore,
        llm_judge: LLMJudge,
        openai_client: OpenAI,
        retrieval_threshold: int = 3,
        current_mode: str = "patient_intake",
    ):
        self.session = session
        self.vector_store = vector_store
        self.llm_judge = llm_judge
        self.client = openai_client
        self.retrieval_threshold = retrieval_threshold

        # Initialize session with mode and phase tracking
        if "mode" not in self.session:
            self.session["mode"] = current_mode

        if "phase" not in self.session:
            if self.session["mode"] == "patient_intake":
                self.session["phase"] = (
                    "basic_intake"  # basic_intake -> detailed_symptoms -> routing
                )
            else:  # physician_consultation
                self.session["phase"] = (
                    "recording"  # recording -> extraction -> validation
                )

        if "messages" not in self.session:
            self.session["messages"] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
        if "data" not in self.session:
            self.session["data"] = {}
        if "escalation_data" not in self.session:
            self.session["escalation_data"] = {}

    def _get_system_prompt(self) -> str:
        """Get system prompt based on current mode and phase."""
        mode = self.session.get("mode", "patient_intake")
        phase = self.session.get("phase", "basic_intake")

        if mode == "physician_consultation":
            return self._get_physician_consultation_prompt(phase)
        else:  # patient_intake
            return self._get_patient_intake_prompt(phase)

    def _get_physician_consultation_prompt(self, phase: str) -> str:
        """Get system prompt for physician consultation mode."""
        if phase == "recording":
            return (
                "You are a Clinical Observer, silently recording a physician-patient conversation. "
                "Your role is to provide real-time clinical decision support without interrupting the conversation. "
                "DO NOT SPEAK OR RESPOND VERBALLY. Only provide silent analysis and suggestions. "
                "Focus on: symptom analysis, differential diagnosis, medication interactions, and evidence-based recommendations. "
                "Extract clinical insights and display them on screen for the physician's reference. "
                "Your responses should be internal analysis only - never spoken to the patient or physician."
            )
        elif phase == "extraction":
            return (
                "You are extracting clinical insights from the recorded conversation. "
                "Identify: patient presentation, physician decision, clinical reasoning, and key factors. "
                "Structure the information clearly for physician review and learning."
            )
        else:  # validation
            return (
                "You are presenting the extracted clinical insights for physician validation. "
                "Format the information clearly and request approval or modifications."
            )

    def _get_patient_intake_prompt(self, phase: str) -> str:
        """Get system prompt for patient intake mode."""
        if phase == "basic_intake":
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
        elif phase == "detailed_symptoms":
            return (
                "You are John, continuing the intake process. "
                "Now collect DETAILED information about the patient's symptoms. "
                "For each symptom, ask about: severity (1-10 scale), duration, associated symptoms, and triggers. "
                "Be thorough but efficient. Use the collect_detailed_symptoms function to store this information. "
                "After collecting detailed symptoms, proceed to determine the appropriate care route."
            )
        elif phase == "routing":
            similar_cases = self.vector_store.retrieve_similar(self.session["messages"])
            examples = self.vector_store.get_few_shot_examples(similar_cases)

            if examples:
                return f"""You are John, making a routing decision based on patient information.
                
Here are similar cases for reference:
{examples}

Based on the patient's symptoms and these examples, determine the appropriate care route:
- emergency: Life-threatening (severe chest pain, stroke signs, difficulty breathing)
- urgent: Serious but not life-threatening (high fever, severe pain)  
- routine: Ongoing or non-urgent (mild symptoms, follow-ups)
- self_care: Minor issues (cold, mild headache)
- information: Questions about medication or prevention

Use the determine_routing function to make your decision."""
            else:
                return (
                    "You are John, making a routing decision. "
                    "Based on the patient's symptoms, determine appropriate care route. "
                    "Use the determine_routing function, but note this will likely be escalated "
                    "since we have limited similar cases for reference."
                )

    def handle_function_call(self, function_call):
        """Handle function calls and store data."""
        name = function_call["name"]
        arguments = function_call.get("arguments", {})

        # Store basic intake data
        if name == "verify_fullname":
            self.session["data"]["full_name"] = arguments.get("names")
        elif name == "verify_birthday":
            self.session["data"]["birthday"] = arguments.get("birthday")
        elif name == "list_prescriptions":
            self.session["data"]["prescriptions"] = arguments.get("prescriptions")
        elif name == "list_allergies":
            self.session["data"]["allergies"] = arguments.get("allergies")
        elif name == "list_conditions":
            self.session["data"]["conditions"] = arguments.get("conditions")
        elif name == "list_visit_reasons":
            self.session["data"]["visit_reasons"] = arguments.get("visit_reasons")

        # Store detailed symptoms
        elif name == "collect_detailed_symptoms":
            self.session["data"]["detailed_symptoms"] = arguments.get("symptoms")

        # Store routing decision
        elif name == "determine_routing":
            self.session["data"]["routing"] = {
                "route": arguments.get("route"),
                "reasoning": arguments.get("reasoning"),
            }

    def all_basic_info_collected(self) -> bool:
        """Check if all basic intake info is collected."""
        data = self.session.get("data", {})
        required = [
            "full_name",
            "birthday",
            "prescriptions",
            "allergies",
            "conditions",
            "visit_reasons",
        ]

        for key in required:
            if key not in data:
                return False
            value = data[key]
            if isinstance(value, list):
                continue  # Accept empty lists
            elif isinstance(value, str):
                if not value.strip():
                    return False
            elif value is None:
                return False
        return True

    def has_detailed_symptoms(self) -> bool:
        """Check if detailed symptoms are collected."""
        return "detailed_symptoms" in self.session.get("data", {})

    def has_routing_decision(self) -> bool:
        """Check if routing decision is made."""
        return "routing" in self.session.get("data", {})

    def should_escalate(self) -> bool:
        """Determine if case should be escalated based on retrieval threshold."""
        similar_count = self.vector_store.count_similar_cases(self.session["messages"])
        print(
            f"[UnifiedProcessor] Found {similar_count} similar cases, threshold: {self.retrieval_threshold}"
        )
        return similar_count < self.retrieval_threshold

    def _calculate_confidence(
        self, similar_cases: List[Tuple[Dict, float]], domain_evidence: Dict[str, Any]
    ) -> float:
        """Calculate combined confidence based on similar cases and medical literature."""
        # Calculate confidence from similar cases
        num_similar = len(similar_cases)
        case_confidence = 0.0
        if num_similar >= self.retrieval_threshold:
            case_confidence = min(1.0, num_similar / (self.retrieval_threshold * 2))
        else:
            case_confidence = num_similar / self.retrieval_threshold

        # Calculate confidence from medical literature
        literature_evidence = domain_evidence.get("evidence", [])
        literature_confidence = min(
            1.0, len(literature_evidence) / 3.0
        )  # Max confidence with 3+ literature items

        # Combine confidence (weighted average: 60% cases, 40% literature)
        combined_confidence = (case_confidence * 0.6) + (literature_confidence * 0.4)

        return combined_confidence

    def next_prompt(
        self, user_message: Optional[str] = None
    ) -> tuple[str, bool, Optional[Dict]]:
        """
        Process next step in conversation.
        Returns: (reply, end_call, escalation_info)
        """
        print(f"=== IntakeProcessor.next_prompt ===")
        print(f"Phase: {self.session.get('phase')}")
        print(f"User message: '{user_message}'")
        print(f"Current data: {self.session.get('data', {})}")

        if user_message:
            self.session["messages"].append({"role": "user", "content": user_message})

        # Call OpenAI with function calling
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=self.session["messages"],
            functions=FUNCTION_SCHEMAS,
            function_call="auto",
            max_tokens=300,
            temperature=0.3,
        )

        message = response.choices[0].message
        print(f"LLM response: {message.content}")
        print(f"Function call: {message.function_call}")

        self.session["messages"].append(message.model_dump(exclude_unset=True))

        # Handle function calls
        if message.function_call:
            function_call = message.function_call.model_dump()
            arguments = json.loads(function_call["arguments"])
            function_call["arguments"] = arguments
            self.handle_function_call(function_call)

            # Add function response
            self.session["messages"].append(
                {"role": "function", "name": function_call["name"], "content": "OK"}
            )

            # Check for phase transitions
            if (
                self.session["phase"] == "basic_intake"
                and self.all_basic_info_collected()
            ):
                self.session["phase"] = "detailed_symptoms"
                self.session["messages"].append(
                    {"role": "system", "content": self._get_system_prompt()}
                )
            elif (
                self.session["phase"] == "detailed_symptoms"
                and self.has_detailed_symptoms()
            ):
                self.session["phase"] = "routing"
                self.session["messages"].append(
                    {"role": "system", "content": self._get_system_prompt()}
                )
            elif self.session["phase"] == "routing" and self.has_routing_decision():
                # Check if we should escalate
                if self.should_escalate():
                    return self._prepare_escalation()
                else:
                    return self._finalize_routing()

            # Continue conversation
            return self.next_prompt(None)

        # No function call - regular response
        return message.content, False, None

    def _prepare_escalation(self) -> tuple[str, bool, Dict]:
        """Prepare escalation data for human review."""
        routing_data = self.session["data"].get("routing", {})
        escalation_info = {
            "session_id": self.session.get("session_id"),
            "agent_prediction": routing_data.get("route", "unknown"),
            "reasoning": routing_data.get("reasoning", "No reasoning provided"),
            "patient_data": self.session["data"],
            "conversation": self.session["messages"],
        }

        self.session["escalation_data"] = escalation_info

        escalation_message = (
            f"I've analyzed your symptoms and believe this may require {routing_data.get('route', 'unknown')} care. "
            f"However, I'd like to have a human expert review this case to ensure you get the best care. "
            f"Let me connect you with one of our specialists."
        )

        return escalation_message, True, escalation_info

    def _finalize_routing(self) -> tuple[str, bool, None]:
        """Finalize routing decision when confident."""
        routing_data = self.session["data"].get("routing", {})
        route = routing_data.get("route", "unknown")
        reasoning = routing_data.get("reasoning", "")

        final_message = f"Based on your symptoms, I recommend {route} care. {reasoning} I'll connect you with the appropriate department now."

        return final_message, True, None

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get("messages", [])

    def get_data(self) -> Dict[str, Any]:
        return self.session.get("data", {})

    def get_escalation_data(self) -> Dict[str, Any]:
        return self.session.get("escalation_data", {})

    def get_real_time_evidence(self) -> Dict[str, Any]:
        """Get real-time evidence for display panel."""
        mode = self.session.get("mode", "patient_intake")

        if mode == "patient_intake":
            return self._get_patient_intake_evidence()
        else:  # physician_consultation
            return self._get_physician_consultation_evidence()

    def _get_patient_intake_evidence(self) -> Dict[str, Any]:
        """Get evidence for patient intake mode."""
        phase = self.session.get("phase", "basic_intake")
        data = self.session.get("data", {})

        # Always show extracted data from the start
        extracted_data = data

        # Show evidence after visit reasons are collected (not after detailed symptoms)
        has_visit_reasons = "visit_reasons" in data and data["visit_reasons"]

        if phase == "basic_intake" and not has_visit_reasons:
            return {
                "similar_cases": [],
                "medical_literature": [],
                "search_terms": [],
                "extracted_data": extracted_data,
                "confidence": 0.0,
                "confidence_breakdown": {
                    "case_confidence": 0.0,
                    "literature_confidence": 0.0,
                },
                "evidence_ready": False,
                "message": "Medical evidence will appear once visit reason is provided...",
            }

        # Get similar cases from vector store
        similar_cases = self.vector_store.retrieve_similar(self.session["messages"])

        # Get domain evidence (medical literature)
        domain_evidence = self._get_domain_evidence()

        return {
            "similar_cases": [
                {
                    "symptoms": case.get("symptoms_summary", "Unknown"),
                    "route": case.get("correct_route", "Unknown"),
                    "similarity": score,
                }
                for case, score in similar_cases[:3]  # Top 3 similar cases
            ],
            "medical_literature": domain_evidence.get("evidence", []),
            "search_terms": domain_evidence.get("search_terms", []),
            "extracted_data": extracted_data,
            "confidence": self._calculate_confidence(similar_cases, domain_evidence),
            "confidence_breakdown": {
                "case_confidence": min(
                    1.0, len(similar_cases) / self.retrieval_threshold
                ),
                "literature_confidence": min(
                    1.0, len(domain_evidence.get("evidence", [])) / 3.0
                ),
            },
            "evidence_ready": True,
        }

    def _get_physician_consultation_evidence(self) -> Dict[str, Any]:
        """Get evidence for physician consultation mode."""
        # Get similar clinical cases
        similar_cases = self.vector_store.retrieve_similar(self.session["messages"])

        # Get domain evidence (medical literature)
        domain_evidence = self._get_domain_evidence()

        return {
            "similar_cases": [
                {
                    "presentation": case.get("patient_presentation", "Unknown"),
                    "decision": case.get("physician_decision", "Unknown"),
                    "similarity": score,
                }
                for case, score in similar_cases[:3]  # Top 3 similar cases
            ],
            "medical_literature": domain_evidence.get("evidence", []),
            "search_terms": domain_evidence.get("search_terms", []),
            "extracted_data": self.session.get("data", {}),
            "confidence": self._calculate_confidence(similar_cases, domain_evidence),
            "confidence_breakdown": {
                "case_confidence": min(
                    1.0, len(similar_cases) / self.retrieval_threshold
                ),
                "literature_confidence": min(
                    1.0, len(domain_evidence.get("evidence", [])) / 3.0
                ),
            },
        }

    def _get_domain_evidence(self) -> Dict[str, Any]:
        """Get domain evidence from medical literature (mocked OpenEvidence API)."""
        try:
            # Extract key terms from conversation for literature search
            conversation_text = " ".join(
                [
                    msg.get("content", "")
                    for msg in self.session.get("messages", [])
                    if msg.get("role") == "user"
                ]
            ).lower()

            # Extract patient data for more targeted literature search
            patient_data = self.session.get("data", {})
            visit_reasons = patient_data.get("visit_reasons", [])

            # Mock OpenEvidence API response based on conversation content and visit reasons
            evidence_items = []

            # Check visit reasons first for initial recommendations
            if visit_reasons:
                for reason in visit_reasons:
                    reason_lower = reason.lower()

                    if "chest pain" in reason_lower:
                        evidence_items.extend(
                            [
                                "Chest pain evaluation guidelines: Immediate assessment for cardiac causes",
                                "Risk stratification for chest pain: Consider age, risk factors, and presentation",
                                "Atypical chest pain patterns require comprehensive cardiac workup",
                            ]
                        )

                    elif "headache" in reason_lower:
                        evidence_items.extend(
                            [
                                "Headache classification: Primary vs secondary headache evaluation",
                                "Red flag symptoms for headache: Sudden onset, fever, neurological deficits",
                                "Migraine vs tension headache: Clinical differentiation guidelines",
                            ]
                        )

                    elif "fever" in reason_lower:
                        evidence_items.extend(
                            [
                                "Fever evaluation in adults: Focus on duration and associated symptoms",
                                "Infectious vs non-infectious fever: Diagnostic approach",
                                "Fever with rash: Consider viral exanthems and drug reactions",
                            ]
                        )

                    elif (
                        "shortness of breath" in reason_lower
                        or "breathing" in reason_lower
                    ):
                        evidence_items.extend(
                            [
                                "Dyspnea evaluation: Cardiac vs pulmonary vs systemic causes",
                                "Acute dyspnea: Immediate assessment for life-threatening conditions",
                                "Chronic dyspnea: Systematic approach to diagnosis",
                            ]
                        )

                    elif "abdominal pain" in reason_lower:
                        evidence_items.extend(
                            [
                                "Acute abdominal pain: Surgical vs medical causes",
                                "Abdominal pain localization: Organ-specific differential diagnosis",
                                "Chronic abdominal pain: Functional vs organic causes",
                            ]
                        )

            # Add general evidence if no specific conditions found
            if not evidence_items:
                evidence_items = [
                    "Patient history and medication review essential for accurate diagnosis",
                    "New symptoms in patients with chronic conditions require thorough evaluation",
                    "Drug interactions and side effects common in patients on multiple medications",
                ]

            return {
                "evidence": evidence_items,
                "source": "OpenEvidence API",
                "search_terms": self._extract_search_terms(
                    conversation_text, patient_data
                ),
            }
        except Exception as e:
            return {"evidence": [], "error": str(e)}

    def _extract_search_terms(
        self, conversation_text: str, patient_data: Dict[str, Any]
    ) -> List[str]:
        """Extract relevant search terms for literature search."""
        terms = []

        # Extract visit reasons first (most important for initial search)
        if "visit_reasons" in patient_data:
            terms.extend(patient_data["visit_reasons"])

        # Extract symptoms from conversation
        symptom_keywords = [
            "rash",
            "pain",
            "fever",
            "cough",
            "shortness of breath",
            "nausea",
            "fatigue",
            "headache",
            "chest pain",
            "abdominal pain",
        ]
        for keyword in symptom_keywords:
            if keyword in conversation_text:
                terms.append(keyword)

        # Extract conditions from patient data
        if "conditions" in patient_data:
            terms.extend(patient_data["conditions"])

        # Extract medications
        if "prescriptions" in patient_data:
            for med in patient_data["prescriptions"]:
                if isinstance(med, dict) and "medication" in med:
                    terms.append(med["medication"])

        return terms[:5]  # Limit to top 5 terms
