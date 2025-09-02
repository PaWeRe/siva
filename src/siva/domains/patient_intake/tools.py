# Copyright Sierra
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json
import re
from datetime import datetime
from enum import Enum

from siva.environment.tool import Tool, as_tool


class ValidationStatus(Enum):
    """Enumeration of validation statuses."""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_CLARIFICATION = "requires_clarification"


@dataclass
class STTResult:
    """Result from Speech-to-Text processing."""

    text: str
    confidence: float
    success: bool


@dataclass
class TTSResult:
    """Result from Text-to-Speech processing."""

    audio_data: bytes
    success: bool
    duration_ms: int


class PatientIntakeTools:
    """Enhanced tools for patient intake domain with validation."""

    def __init__(self, session_data: Optional[Dict[str, Any]] = None):
        self.session_data = session_data or {}
        self.validation_status = {}

    def speech_to_text(self, audio_data: bytes) -> STTResult:
        """
        Convert speech to text.

        Args:
            audio_data: Raw audio data

        Returns:
            STTResult with transcribed text and confidence
        """
        # For now, return a placeholder
        # This will be connected to your existing STT logic
        return STTResult(
            text="[STT placeholder - audio data received]", confidence=0.9, success=True
        )

    def text_to_speech(self, text: str, voice: str = "default") -> TTSResult:
        """
        Convert text to speech.

        Args:
            text: Text to convert to speech
            voice: Voice to use for synthesis

        Returns:
            TTSResult with audio data
        """
        # For now, return a placeholder
        # This will be connected to your existing TTS logic
        return TTSResult(
            audio_data=b"[TTS placeholder - text received]",
            success=True,
            duration_ms=1000,
        )

    def verify_fullname(self, names: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Collect and validate the user's full name.

        Args:
            names: List of name objects with first_name and last_name, or full_name

        Returns:
            Success status and validation result
        """
        if not names:
            return {
                "success": False,
                "error": "No names provided",
                "validation_status": ValidationStatus.INVALID.value,
            }

        name = names[0]  # Take the first name

        # Handle both formats: first_name/last_name or full_name
        if "full_name" in name:
            full_name = name.get("full_name", "").strip()
            if not full_name:
                return {
                    "success": False,
                    "error": "Full name is required",
                    "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
                }
            # Split full name into first and last name for validation
            name_parts = full_name.split()
            if len(name_parts) < 2:
                return {
                    "success": False,
                    "error": "Both first and last name are required",
                    "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
                }
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])
        else:
            first_name = name.get("first_name", "").strip()
            last_name = name.get("last_name", "").strip()
            full_name = f"{first_name} {last_name}"

        # Validation
        if not first_name or not last_name:
            return {
                "success": False,
                "error": "Both first and last name are required",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        if len(first_name) < 2 or len(last_name) < 2:
            return {
                "success": False,
                "error": "Names must be at least 2 characters long",
                "validation_status": ValidationStatus.INVALID.value,
            }

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["full_name"] = full_name

        return {
            "success": True,
            "message": f"Stored full name: {full_name}",
            "full_name": full_name,
            "validation_status": ValidationStatus.VALID.value,
        }

    def verify_birthday(self, birthday: str) -> Dict[str, Any]:
        """
        Verify and validate the user's birthday.

        Args:
            birthday: Birthday in YYYY-MM-DD format

        Returns:
            Success status and validation result
        """
        # Format validation
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", birthday):
            return {
                "success": False,
                "error": "Invalid format. Please use YYYY-MM-DD format",
                "validation_status": ValidationStatus.INVALID.value,
            }

        try:
            # Parse date
            date_obj = datetime.strptime(birthday, "%Y-%m-%d")
            current_year = datetime.now().year

            # Reasonableness check (age between 0 and 120)
            if date_obj.year < current_year - 120 or date_obj.year > current_year:
                return {
                    "success": False,
                    "error": "Birthday seems unreasonable. Please check the year.",
                    "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
                }

            # Store in session data
            if "data" not in self.session_data:
                self.session_data["data"] = {}
            self.session_data["data"]["birthday"] = birthday

            return {
                "success": True,
                "message": f"Stored birthday: {birthday}",
                "birthday": birthday,
                "validation_status": ValidationStatus.VALID.value,
            }

        except ValueError:
            return {
                "success": False,
                "error": "Invalid date format",
                "validation_status": ValidationStatus.INVALID.value,
            }

    def list_prescriptions(
        self, prescriptions: List[Union[str, Dict[str, str]]]
    ) -> Dict[str, Any]:
        """
        Collect and validate the user's current prescriptions.

        Args:
            prescriptions: List of prescription strings or prescription objects with medication and dosage

        Returns:
            Success status and stored prescriptions
        """
        if not prescriptions:
            # Allow empty list for "no prescriptions"
            if "data" not in self.session_data:
                self.session_data["data"] = {}
            self.session_data["data"]["prescriptions"] = []

            return {
                "success": True,
                "message": "No prescriptions recorded",
                "prescriptions": [],
                "validation_status": ValidationStatus.VALID.value,
            }

        # Validate each prescription
        validated_prescriptions = []
        for prescription in prescriptions:
            if isinstance(prescription, str):
                # Handle string format: "Lisinopril 10mg daily"
                medication = prescription.strip()
                dosage = ""
            elif isinstance(prescription, dict):
                # Handle dictionary format: {"medication": "...", "dosage": "..."}
                medication = prescription.get("medication", "").strip()
                dosage = prescription.get("dosage", "").strip()
            else:
                continue  # Skip invalid formats

            if not medication:
                return {
                    "success": False,
                    "error": "Medication name is required for each prescription",
                    "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
                }

            validated_prescriptions.append({"medication": medication, "dosage": dosage})

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["prescriptions"] = validated_prescriptions

        return {
            "success": True,
            "message": f"Stored {len(validated_prescriptions)} prescription(s)",
            "prescriptions": validated_prescriptions,
            "validation_status": ValidationStatus.VALID.value,
        }

    def list_allergies(self, allergies: List[str]) -> Dict[str, Any]:
        """
        Collect and validate the user's allergies.

        Args:
            allergies: List of allergy strings

        Returns:
            Success status and stored allergies
        """
        if not allergies:
            # Allow empty list for "no allergies"
            if "data" not in self.session_data:
                self.session_data["data"] = {}
            self.session_data["data"]["allergies"] = []

            return {
                "success": True,
                "message": "No allergies recorded",
                "allergies": [],
                "validation_status": ValidationStatus.VALID.value,
            }

        # Validate and clean allergies
        validated_allergies = []
        for allergy in allergies:
            cleaned_allergy = allergy.strip()
            if cleaned_allergy:
                validated_allergies.append(cleaned_allergy)

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["allergies"] = validated_allergies

        return {
            "success": True,
            "message": f"Stored {len(validated_allergies)} allergy(ies)",
            "allergies": validated_allergies,
            "validation_status": ValidationStatus.VALID.value,
        }

    def list_conditions(self, conditions: List[str]) -> Dict[str, Any]:
        """
        Collect and validate the user's medical conditions.

        Args:
            conditions: List of medical condition strings

        Returns:
            Success status and stored conditions
        """
        if not conditions:
            # Allow empty list for "no conditions"
            if "data" not in self.session_data:
                self.session_data["data"] = {}
            self.session_data["data"]["medical_conditions"] = []

            return {
                "success": True,
                "message": "No medical conditions recorded",
                "conditions": [],
                "validation_status": ValidationStatus.VALID.value,
            }

        # Validate and clean conditions
        validated_conditions = []
        for condition in conditions:
            cleaned_condition = condition.strip()
            if cleaned_condition:
                validated_conditions.append(cleaned_condition)

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["medical_conditions"] = validated_conditions

        return {
            "success": True,
            "message": f"Stored {len(validated_conditions)} medical condition(s)",
            "conditions": validated_conditions,
            "validation_status": ValidationStatus.VALID.value,
        }

    def list_visit_reasons(self, visit_reasons: List[str]) -> Dict[str, Any]:
        """
        Collect and validate the user's reasons for visit.

        Args:
            visit_reasons: List of visit reason strings

        Returns:
            Success status and stored visit reasons
        """
        if not visit_reasons:
            return {
                "success": False,
                "error": "At least one reason for visit is required",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        # Validate and clean visit reasons
        validated_reasons = []
        for reason in visit_reasons:
            cleaned_reason = reason.strip()
            if cleaned_reason:
                validated_reasons.append(cleaned_reason)

        if not validated_reasons:
            return {
                "success": False,
                "error": "At least one valid reason for visit is required",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["visit_reasons"] = validated_reasons

        return {
            "success": True,
            "message": f"Stored {len(validated_reasons)} visit reason(s)",
            "visit_reasons": validated_reasons,
            "validation_status": ValidationStatus.VALID.value,
        }

    def collect_detailed_symptoms(
        self, symptoms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Collect detailed symptom information.

        Args:
            symptoms: List of symptom objects with severity, duration, etc.

        Returns:
            Success status and stored symptoms
        """
        if not symptoms:
            return {
                "success": False,
                "error": "At least one symptom is required",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        # Validate each symptom
        validated_symptoms = []
        for symptom in symptoms:
            symptom_name = symptom.get("symptom", "").strip()
            severity = symptom.get("severity", 0)
            duration = symptom.get("duration", "").strip()

            if not symptom_name:
                return {
                    "success": False,
                    "error": "Symptom name is required for each symptom",
                    "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
                }

            # Validate severity (1-10 scale)
            if not isinstance(severity, int) or severity < 1 or severity > 10:
                return {
                    "success": False,
                    "error": "Severity must be a number between 1 and 10",
                    "validation_status": ValidationStatus.INVALID.value,
                }

            validated_symptoms.append(
                {
                    "symptom": symptom_name,
                    "severity": severity,
                    "duration": duration,
                    "associated_symptoms": symptom.get("associated_symptoms", []),
                    "triggers": symptom.get("triggers", []),
                }
            )

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["detailed_symptoms"] = validated_symptoms

        return {
            "success": True,
            "message": f"Stored {len(validated_symptoms)} detailed symptom(s)",
            "symptoms": validated_symptoms,
            "validation_status": ValidationStatus.VALID.value,
        }

    def determine_routing(self, route: str, reasoning: str) -> Dict[str, Any]:
        """
        Determine appropriate care routing based on collected information.

        Args:
            route: Care route (emergency, urgent, routine, self_care, information)
            reasoning: Reasoning for the routing decision

        Returns:
            Success status and routing decision
        """
        valid_routes = ["emergency", "urgent", "routine", "self_care", "information"]

        # Make route case-insensitive
        route_lower = route.lower().strip()

        if route_lower not in valid_routes:
            return {
                "success": False,
                "error": f"Invalid route. Must be one of: {', '.join(valid_routes)}",
                "validation_status": ValidationStatus.INVALID.value,
            }

        if not reasoning.strip():
            return {
                "success": False,
                "error": "Reasoning is required for routing decision",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        routing_decision = {
            "route": route_lower,
            "reasoning": reasoning.strip(),
            "timestamp": datetime.now().isoformat(),
        }

        # Store in session data
        if "data" not in self.session_data:
            self.session_data["data"] = {}
        self.session_data["data"]["routing_decision"] = routing_decision

        return {
            "success": True,
            "message": f"Routing decision made: {route_lower}",
            "routing_decision": routing_decision,
            "validation_status": ValidationStatus.VALID.value,
        }

    def escalate_to_human(self, reason: str) -> Dict[str, Any]:
        """
        Escalate the conversation to a human agent.

        Args:
            reason: Reason for escalation

        Returns:
            Success status and escalation info
        """
        if not reason.strip():
            return {
                "success": False,
                "error": "Escalation reason is required",
                "validation_status": ValidationStatus.REQUIRES_CLARIFICATION.value,
            }

        escalation_info = {
            "reason": reason.strip(),
            "timestamp": datetime.now().isoformat(),
            "patient_data": self.session_data.get("data", {}),
        }

        # Store in session data
        if "escalation_data" not in self.session_data:
            self.session_data["escalation_data"] = {}
        self.session_data["escalation_data"] = escalation_info

        return {
            "success": True,
            "message": f"Conversation escalated: {reason}",
            "escalation_info": escalation_info,
            "validation_status": ValidationStatus.VALID.value,
        }

    def terminate_conversation(self, reason: str) -> Dict[str, Any]:
        """
        Terminate the conversation.

        Args:
            reason: Reason for termination

        Returns:
            Success status and termination info
        """
        termination_info = {
            "reason": reason.strip() if reason else "Workflow completed",
            "timestamp": datetime.now().isoformat(),
            "patient_data": self.session_data.get("data", {}),
            "conversation_duration": self._get_conversation_duration(),
        }

        # Store in session data
        if "termination_data" not in self.session_data:
            self.session_data["termination_data"] = {}
        self.session_data["termination_data"] = termination_info

        return {
            "success": True,
            "message": f"Conversation terminated: {termination_info['reason']}",
            "termination_info": termination_info,
            "validation_status": ValidationStatus.VALID.value,
        }

    def _get_conversation_duration(self) -> Optional[float]:
        """Get conversation duration in seconds."""
        if "conversation_start_time" in self.session_data:
            start_time = self.session_data["conversation_start_time"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            return (datetime.now() - start_time).total_seconds()
        return None

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """Get function schemas for OpenAI function calling."""
        return [
            {
                "name": "verify_fullname",
                "description": "Collect and validate the user's full name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "full_name": {"type": "string"},
                                },
                                "anyOf": [
                                    {"required": ["first_name", "last_name"]},
                                    {"required": ["full_name"]},
                                ],
                            },
                        }
                    },
                    "required": ["names"],
                },
            },
            {
                "name": "verify_birthday",
                "description": "Verify and validate the user's birthday",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birthday": {
                            "type": "string",
                            "description": "The user's birthday in YYYY-MM-DD format",
                        }
                    },
                    "required": ["birthday"],
                },
            },
            {
                "name": "list_prescriptions",
                "description": "Collect and validate the user's current prescriptions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prescriptions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "medication": {"type": "string"},
                                    "dosage": {"type": "string"},
                                },
                                "required": ["medication"],
                            },
                        }
                    },
                    "required": ["prescriptions"],
                },
            },
            {
                "name": "list_allergies",
                "description": "Collect and validate the user's allergies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "allergies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["allergies"],
                },
            },
            {
                "name": "list_conditions",
                "description": "Collect and validate the user's medical conditions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "conditions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["conditions"],
                },
            },
            {
                "name": "list_visit_reasons",
                "description": "Collect and validate the user's reasons for visit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "visit_reasons": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["visit_reasons"],
                },
            },
            {
                "name": "collect_detailed_symptoms",
                "description": "Collect detailed symptom information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symptoms": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symptom": {"type": "string"},
                                    "severity": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 10,
                                    },
                                    "duration": {"type": "string"},
                                    "associated_symptoms": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "triggers": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": ["symptom", "severity"],
                            },
                        }
                    },
                    "required": ["symptoms"],
                },
            },
            {
                "name": "determine_routing",
                "description": "Determine appropriate care routing based on collected information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "route": {
                            "type": "string",
                            "enum": [
                                "emergency",
                                "urgent",
                                "routine",
                                "self_care",
                                "information",
                            ],
                        },
                        "reasoning": {"type": "string"},
                    },
                    "required": ["route", "reasoning"],
                },
            },
            {
                "name": "escalate_to_human",
                "description": "Escalate the conversation to a human agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"},
                    },
                    "required": ["reason"],
                },
            },
            {
                "name": "terminate_conversation",
                "description": "Terminate the conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"},
                    },
                    "required": [],
                },
            },
        ]

    def get_tools(self) -> list[Tool]:
        """Get the tools as Tool objects."""
        from siva.environment.tool import as_tool

        tools = []

        # Add all the domain-specific tools
        tools.append(as_tool(self.verify_fullname))
        tools.append(as_tool(self.verify_birthday))
        tools.append(as_tool(self.list_prescriptions))
        tools.append(as_tool(self.list_allergies))
        tools.append(as_tool(self.list_conditions))
        tools.append(as_tool(self.list_visit_reasons))
        tools.append(as_tool(self.collect_detailed_symptoms))
        tools.append(as_tool(self.determine_routing))
        tools.append(as_tool(self.escalate_to_human))
        tools.append(as_tool(self.terminate_conversation))

        return tools


def create_patient_intake_tools(
    session_data: Optional[Dict[str, Any]] = None,
) -> PatientIntakeTools:
    """Create a PatientIntakeTools instance."""
    return PatientIntakeTools(session_data=session_data)
