# Copyright Sierra
"""
Healthcare User Simulator for SIVA patient intake testing.
Generates realistic patient responses for testing the healthcare agent.
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PatientProfile:
    """Profile for a simulated patient."""

    first_name: str
    last_name: str
    birthday: str
    prescriptions: List[Dict[str, str]]
    allergies: List[str]
    conditions: List[str]
    visit_reasons: List[str]
    symptoms: List[Dict[str, Any]]


class HealthcareUserSimulator:
    """Simulates a patient for healthcare intake testing."""

    def __init__(self):
        # Sample patient data for realistic responses
        self.sample_names = [
            ("John", "Smith"),
            ("Mary", "Johnson"),
            ("David", "Williams"),
            ("Sarah", "Brown"),
            ("Michael", "Jones"),
            ("Lisa", "Garcia"),
            ("Robert", "Miller"),
            ("Jennifer", "Davis"),
            ("William", "Rodriguez"),
            ("Linda", "Martinez"),
        ]

        self.sample_prescriptions = [
            {"medication": "Lisinopril", "dosage": "10mg daily"},
            {"medication": "Metformin", "dosage": "500mg twice daily"},
            {"medication": "Atorvastatin", "dosage": "20mg daily"},
            {"medication": "Amlodipine", "dosage": "5mg daily"},
            {"medication": "Omeprazole", "dosage": "20mg daily"},
            {"medication": "Ibuprofen", "dosage": "400mg as needed"},
            {"medication": "Acetaminophen", "dosage": "500mg as needed"},
        ]

        self.sample_allergies = [
            "Penicillin",
            "Peanuts",
            "Shellfish",
            "Latex",
            "Sulfa drugs",
            "Aspirin",
            "Codeine",
            "Eggs",
            "Dairy",
            "Wheat",
        ]

        self.sample_conditions = [
            "Hypertension",
            "Diabetes",
            "Asthma",
            "Arthritis",
            "Depression",
            "Anxiety",
            "High cholesterol",
            "GERD",
            "Migraines",
            "Insomnia",
        ]

        self.sample_visit_reasons = [
            "Annual checkup",
            "Follow-up appointment",
            "Chest pain",
            "Headache",
            "Fever",
            "Cough",
            "Back pain",
            "Stomach pain",
            "Dizziness",
            "Medication refill",
            "Blood pressure check",
            "Blood work",
        ]

        self.sample_symptoms = [
            {
                "symptom": "Chest pain",
                "severity": 8,
                "duration": "2 hours",
                "associated_symptoms": ["Shortness of breath", "Sweating"],
                "triggers": "Exercise, stress",
            },
            {
                "symptom": "Headache",
                "severity": 6,
                "duration": "1 day",
                "associated_symptoms": ["Nausea", "Light sensitivity"],
                "triggers": "Stress, lack of sleep",
            },
            {
                "symptom": "Fever",
                "severity": 7,
                "duration": "3 days",
                "associated_symptoms": ["Chills", "Body aches"],
                "triggers": "Infection",
            },
            {
                "symptom": "Back pain",
                "severity": 5,
                "duration": "1 week",
                "associated_symptoms": ["Stiffness"],
                "triggers": "Lifting heavy objects",
            },
        ]

    def generate_patient_profile(self) -> PatientProfile:
        """Generate a random patient profile."""
        first_name, last_name = random.choice(self.sample_names)

        # Generate random birthday (adult patient)
        year = random.randint(1950, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        birthday = f"{year:04d}-{month:02d}-{day:02d}"

        # Generate random prescriptions (0-3 prescriptions)
        num_prescriptions = random.randint(0, 3)
        prescriptions = random.sample(self.sample_prescriptions, num_prescriptions)

        # Generate random allergies (0-2 allergies)
        num_allergies = random.randint(0, 2)
        allergies = random.sample(self.sample_allergies, num_allergies)

        # Generate random conditions (0-2 conditions)
        num_conditions = random.randint(0, 2)
        conditions = random.sample(self.sample_conditions, num_conditions)

        # Generate random visit reasons (1-2 reasons)
        num_reasons = random.randint(1, 2)
        visit_reasons = random.sample(self.sample_visit_reasons, num_reasons)

        # Generate random symptoms (0-2 symptoms)
        num_symptoms = random.randint(0, 2)
        symptoms = random.sample(self.sample_symptoms, num_symptoms)

        return PatientProfile(
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            prescriptions=prescriptions,
            allergies=allergies,
            conditions=conditions,
            visit_reasons=visit_reasons,
            symptoms=symptoms,
        )

    def generate_response(self, agent_message: str, profile: PatientProfile) -> str:
        """Generate a realistic patient response based on the agent's message."""
        message_lower = agent_message.lower()

        # Greeting response
        if any(
            word in message_lower for word in ["hello", "hi", "greeting", "introduce"]
        ):
            return (
                f"Hi, I'm {profile.first_name} {profile.last_name}. Nice to meet you."
            )

        # Name collection
        if "name" in message_lower:
            return f"My name is {profile.first_name} {profile.last_name}."

        # Birthday collection
        if "birthday" in message_lower or "date of birth" in message_lower:
            return f"My birthday is {profile.birthday}."

        # Prescriptions collection
        if "prescription" in message_lower or "medication" in message_lower:
            if profile.prescriptions:
                med_list = ", ".join(
                    [f"{p['medication']} {p['dosage']}" for p in profile.prescriptions]
                )
                return f"I'm currently taking {med_list}."
            else:
                return "I'm not currently taking any medications."

        # Allergies collection
        if "allerg" in message_lower:
            if profile.allergies:
                allergies_list = ", ".join(profile.allergies)
                return f"I'm allergic to {allergies_list}."
            else:
                return "I don't have any known allergies."

        # Medical conditions collection
        if "condition" in message_lower or "diagnosis" in message_lower:
            if profile.conditions:
                conditions_list = ", ".join(profile.conditions)
                return f"I have {conditions_list}."
            else:
                return "I don't have any chronic medical conditions."

        # Visit reasons collection
        if "reason" in message_lower and "visit" in message_lower:
            reasons_list = ", ".join(profile.visit_reasons)
            return f"I'm here for {reasons_list}."

        # Symptoms collection
        if "symptom" in message_lower:
            if profile.symptoms:
                symptom_desc = []
                for symptom in profile.symptoms:
                    desc = f"{symptom['symptom']} with severity {symptom['severity']}/10 for {symptom['duration']}"
                    if symptom["associated_symptoms"]:
                        desc += f", also experiencing {', '.join(symptom['associated_symptoms'])}"
                    symptom_desc.append(desc)
                return f"My symptoms are: {'; '.join(symptom_desc)}."
            else:
                return "I don't have any specific symptoms right now."

        # Default response
        return (
            "I'm not sure how to answer that. Could you please rephrase your question?"
        )

    def simulate_conversation(self, agent_messages: List[str]) -> List[str]:
        """Simulate a complete conversation with the agent."""
        profile = self.generate_patient_profile()
        responses = []

        for agent_message in agent_messages:
            response = self.generate_response(agent_message, profile)
            responses.append(response)

        return responses


def create_user_simulator() -> HealthcareUserSimulator:
    """Create a healthcare user simulator."""
    return HealthcareUserSimulator()
