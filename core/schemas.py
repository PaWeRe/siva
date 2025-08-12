"""Pydantic schemas for SIVA application."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class UserMessage(BaseModel):
    session_id: str
    message: str


class EscalationFeedback(BaseModel):
    session_id: str
    agent_prediction: str
    human_label: str


class ModeRequest(BaseModel):
    mode: str


class PearlExtractionRequest(BaseModel):
    session_id: str
    transcript: str


class PearlValidationRequest(BaseModel):
    session_id: str
    pearl_data: Dict[str, Any]
    physician_id: str


class PearlOutcomeRequest(BaseModel):
    pearl_id: str
    outcome_data: Dict[str, Any]


# Function schemas for OpenAI function calling
FUNCTION_SCHEMAS = [
    {
        "name": "verify_fullname",
        "description": "Collect the user's full name.",
        "parameters": {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                        },
                        "required": ["first_name", "last_name"],
                    },
                }
            },
            "required": ["names"],
        },
    },
    {
        "name": "verify_birthday",
        "description": "Verify the user's birthday.",
        "parameters": {
            "type": "object",
            "properties": {
                "birthday": {
                    "type": "string",
                    "description": "The user's birthday in YYYY-MM-DD format.",
                }
            },
            "required": ["birthday"],
        },
    },
    {
        "name": "list_prescriptions",
        "description": "Collect the user's current prescriptions.",
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
                        "required": ["medication", "dosage"],
                    },
                }
            },
            "required": ["prescriptions"],
        },
    },
    {
        "name": "list_allergies",
        "description": "Collect the user's allergies.",
        "parameters": {
            "type": "object",
            "properties": {"allergies": {"type": "array", "items": {"type": "string"}}},
            "required": ["allergies"],
        },
    },
    {
        "name": "list_conditions",
        "description": "Collect the user's medical conditions.",
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
        "description": "Collect the user's reasons for visiting the doctor.",
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
        "description": "Collect detailed information about patient symptoms.",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symptom": {
                                "type": "string",
                                "description": "The symptom (e.g., chest pain, headache)",
                            },
                            "severity": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Pain/severity scale 1-10",
                            },
                            "duration": {
                                "type": "string",
                                "description": "How long (e.g., 2 hours, 3 days)",
                            },
                            "associated_symptoms": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related symptoms",
                            },
                            "triggers": {
                                "type": "string",
                                "description": "What makes it better or worse",
                            },
                        },
                        "required": ["symptom", "severity", "duration"],
                    },
                },
            },
            "required": ["symptoms"],
        },
    },
    {
        "name": "determine_routing",
        "description": "Determine appropriate care routing based on patient information and similar cases.",
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
                    "description": "The recommended care route",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation for the routing decision",
                },
            },
            "required": ["route", "reasoning"],
        },
    },
]
