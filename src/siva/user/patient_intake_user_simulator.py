"""
Patient Intake User Simulator for SIVA.
Extends the base user simulator with healthcare-specific functionality.
"""

import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from siva.user.user_simulator import UserSimulator
from siva.user.base import UserState, ValidUserInputMessage
from siva.data_model.message import UserMessage
from siva.data_model.tasks import UserInstructions
from siva.environment.tool import Tool


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
    communication_style: (
        str  # "cooperative", "reluctant", "confused", "anxious", "rushed"
    )
    english_proficiency: str  # "fluent", "basic", "limited"


class PatientIntakeUserSimulator(UserSimulator):
    """Patient intake specific user simulator with healthcare data and response patterns."""

    def __init__(
        self,
        tools: Optional[List[Tool]] = None,
        instructions: Optional[UserInstructions] = None,
        llm: Optional[str] = None,
        llm_args: Optional[Dict[str, Any]] = None,
        patient_profile: Optional[PatientProfile] = None,
    ):
        super().__init__(
            tools=tools, instructions=instructions, llm=llm, llm_args=llm_args
        )

        # Initialize sample data first
        self._initialize_sample_data()

        # Then generate patient profile
        self.patient_profile = patient_profile or self._generate_default_profile()

    def _initialize_sample_data(self):
        """Initialize healthcare-specific sample data."""
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
            ("James", "Wilson"),
            ("Patricia", "Anderson"),
            ("Richard", "Taylor"),
            ("Barbara", "Thomas"),
            ("Joseph", "Hernandez"),
        ]

        self.sample_prescriptions = [
            {"medication": "Lisinopril", "dosage": "10mg daily"},
            {"medication": "Metformin", "dosage": "500mg twice daily"},
            {"medication": "Atorvastatin", "dosage": "20mg daily"},
            {"medication": "Amlodipine", "dosage": "5mg daily"},
            {"medication": "Omeprazole", "dosage": "20mg daily"},
            {"medication": "Ibuprofen", "dosage": "400mg as needed"},
            {"medication": "Acetaminophen", "dosage": "500mg as needed"},
            {"medication": "Albuterol", "dosage": "2 puffs as needed"},
            {"medication": "Zoloft", "dosage": "50mg daily"},
            {"medication": "Xanax", "dosage": "0.5mg as needed"},
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
            "Tree nuts",
            "Soy",
            "Fish",
            "Strawberries",
            "Kiwi",
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
            "Obesity",
            "Heart disease",
            "COPD",
            "Hypothyroidism",
            "Fibromyalgia",
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
            "Rash",
            "Joint pain",
            "Shortness of breath",
        ]

        self.sample_symptoms = [
            {
                "symptom": "Chest pain",
                "severity": 8,
                "duration": "2 hours",
                "associated_symptoms": ["Shortness of breath", "Sweating"],
                "triggers": ["Physical activity", "Stress"],
                "relieving_factors": ["Rest", "Nitroglycerin"],
            },
            {
                "symptom": "Headache",
                "severity": 6,
                "duration": "3 days",
                "associated_symptoms": ["Nausea", "Light sensitivity"],
                "triggers": ["Stress", "Lack of sleep"],
                "relieving_factors": ["Dark room", "Pain medication"],
            },
            {
                "symptom": "Fever",
                "severity": 7,
                "duration": "1 day",
                "associated_symptoms": ["Chills", "Body aches"],
                "triggers": ["Infection"],
                "relieving_factors": ["Tylenol", "Rest"],
            },
            {
                "symptom": "Cough",
                "severity": 5,
                "duration": "1 week",
                "associated_symptoms": ["Sore throat", "Congestion"],
                "triggers": ["Cold air", "Lying down"],
                "relieving_factors": ["Cough syrup", "Honey"],
            },
            {
                "symptom": "Back pain",
                "severity": 7,
                "duration": "2 weeks",
                "associated_symptoms": ["Stiffness", "Radiating pain"],
                "triggers": ["Lifting", "Sitting too long"],
                "relieving_factors": ["Heat", "Stretching"],
            },
        ]

        self.communication_styles = [
            "cooperative",
            "reluctant",
            "confused",
            "anxious",
            "rushed",
        ]
        self.english_proficiencies = ["fluent", "basic", "limited"]

    def _generate_default_profile(self) -> PatientProfile:
        """Generate a default patient profile for testing."""
        first_name, last_name = random.choice(self.sample_names)

        # Generate realistic birthday (18-85 years old)
        current_year = datetime.now().year
        birth_year = random.randint(current_year - 85, current_year - 18)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birthday = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"

        # Generate random medical data
        num_prescriptions = random.randint(0, 3)
        prescriptions = (
            random.sample(self.sample_prescriptions, num_prescriptions)
            if num_prescriptions > 0
            else []
        )

        num_allergies = random.randint(0, 2)
        allergies = (
            random.sample(self.sample_allergies, num_allergies)
            if num_allergies > 0
            else []
        )

        num_conditions = random.randint(0, 2)
        conditions = (
            random.sample(self.sample_conditions, num_conditions)
            if num_conditions > 0
            else []
        )

        visit_reasons = random.sample(self.sample_visit_reasons, 1)

        num_symptoms = random.randint(0, 1)
        symptoms = (
            random.sample(self.sample_symptoms, num_symptoms)
            if num_symptoms > 0
            else []
        )

        communication_style = random.choice(self.communication_styles)
        english_proficiency = random.choice(self.english_proficiencies)

        return PatientProfile(
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            prescriptions=prescriptions,
            allergies=allergies,
            conditions=conditions,
            visit_reasons=visit_reasons,
            symptoms=symptoms,
            communication_style=communication_style,
            english_proficiency=english_proficiency,
        )

    def generate_healthcare_response(self, agent_message: str) -> str:
        """Generate a healthcare-specific response based on the patient profile."""
        message_lower = agent_message.lower()

        # Name response
        if "name" in message_lower:
            return self._generate_name_response()

        # Birthday response
        if any(word in message_lower for word in ["birthday", "birth", "date", "born"]):
            return self._generate_birthday_response()

        # Prescriptions response
        if any(
            word in message_lower
            for word in ["medication", "prescription", "medicine", "drug"]
        ):
            return self._generate_prescriptions_response()

        # Allergies response
        if any(word in message_lower for word in ["allergy", "allergic", "reaction"]):
            return self._generate_allergies_response()

        # Conditions response
        if any(
            word in message_lower
            for word in ["condition", "diagnosis", "problem", "issue"]
        ):
            return self._generate_conditions_response()

        # Visit reason response
        if any(
            word in message_lower for word in ["visit", "appointment", "reason", "why"]
        ):
            return self._generate_visit_reason_response()

        # Symptoms response
        if any(
            word in message_lower for word in ["symptom", "pain", "feeling", "problem"]
        ):
            return self._generate_symptoms_response()

        # Default response - use the base simulator
        return "I'm not sure what you're asking. Could you please clarify?"

    def _generate_name_response(self) -> str:
        """Generate response for name collection."""
        if self.patient_profile.communication_style == "cooperative":
            return f"My name is {self.patient_profile.first_name} {self.patient_profile.last_name}."
        elif self.patient_profile.communication_style == "reluctant":
            return f"It's {self.patient_profile.first_name} {self.patient_profile.last_name}."
        elif self.patient_profile.communication_style == "confused":
            return f"Um, I think it's {self.patient_profile.first_name}... {self.patient_profile.last_name}."
        elif self.patient_profile.communication_style == "anxious":
            return f"My name? It's {self.patient_profile.first_name} {self.patient_profile.last_name}. Why do you need to know?"
        else:  # rushed
            return (
                f"{self.patient_profile.first_name} {self.patient_profile.last_name}."
            )

    def _generate_birthday_response(self) -> str:
        """Generate response for birthday collection."""
        if self.patient_profile.communication_style == "cooperative":
            return f"I was born on {self.patient_profile.birthday}."
        elif self.patient_profile.communication_style == "reluctant":
            return f"{self.patient_profile.birthday}."
        elif self.patient_profile.communication_style == "confused":
            return f"Let me think... {self.patient_profile.birthday}, I think."
        elif self.patient_profile.communication_style == "anxious":
            return f"My birthday is {self.patient_profile.birthday}. Is that important?"
        else:  # rushed
            return f"{self.patient_profile.birthday}."

    def _generate_prescriptions_response(self) -> str:
        """Generate response for prescriptions collection."""
        if not self.patient_profile.prescriptions:
            if self.patient_profile.communication_style == "cooperative":
                return "I don't take any medications currently."
            elif self.patient_profile.communication_style == "reluctant":
                return "None."
            elif self.patient_profile.communication_style == "confused":
                return "I don't think I take any... let me check... no, none."
            elif self.patient_profile.communication_style == "anxious":
                return "No medications. Why do you need to know?"
            else:  # rushed
                return "None."
        else:
            med_list = [
                f"{med['medication']} {med['dosage']}"
                for med in self.patient_profile.prescriptions
            ]

            if self.patient_profile.communication_style == "cooperative":
                return f"I take {', '.join(med_list)}."
            elif self.patient_profile.communication_style == "reluctant":
                return f"{', '.join(med_list)}."
            elif self.patient_profile.communication_style == "confused":
                return f"I think I take... {', '.join(med_list)}."
            elif self.patient_profile.communication_style == "anxious":
                return f"I take {', '.join(med_list)}. Is that a problem?"
            else:  # rushed
                return f"{', '.join(med_list)}."

    def _generate_allergies_response(self) -> str:
        """Generate response for allergies collection."""
        if not self.patient_profile.allergies:
            if self.patient_profile.communication_style == "cooperative":
                return "I don't have any known allergies."
            elif self.patient_profile.communication_style == "reluctant":
                return "None."
            elif self.patient_profile.communication_style == "confused":
                return "I don't think I'm allergic to anything... no, none."
            elif self.patient_profile.communication_style == "anxious":
                return "No allergies. Why do you need to know?"
            else:  # rushed
                return "None."
        else:
            if self.patient_profile.communication_style == "cooperative":
                return f"I'm allergic to {', '.join(self.patient_profile.allergies)}."
            elif self.patient_profile.communication_style == "reluctant":
                return f"{', '.join(self.patient_profile.allergies)}."
            elif self.patient_profile.communication_style == "confused":
                return f"I think I'm allergic to... {', '.join(self.patient_profile.allergies)}."
            elif self.patient_profile.communication_style == "anxious":
                return f"I'm allergic to {', '.join(self.patient_profile.allergies)}. Is that important?"
            else:  # rushed
                return f"{', '.join(self.patient_profile.allergies)}."

    def _generate_conditions_response(self) -> str:
        """Generate response for medical conditions collection."""
        if not self.patient_profile.conditions:
            if self.patient_profile.communication_style == "cooperative":
                return "I don't have any chronic medical conditions."
            elif self.patient_profile.communication_style == "reluctant":
                return "None."
            elif self.patient_profile.communication_style == "confused":
                return "I don't think I have any conditions... no, none."
            elif self.patient_profile.communication_style == "anxious":
                return "No conditions. Why do you need to know?"
            else:  # rushed
                return "None."
        else:
            if self.patient_profile.communication_style == "cooperative":
                return f"I have {', '.join(self.patient_profile.conditions)}."
            elif self.patient_profile.communication_style == "reluctant":
                return f"{', '.join(self.patient_profile.conditions)}."
            elif self.patient_profile.communication_style == "confused":
                return (
                    f"I think I have... {', '.join(self.patient_profile.conditions)}."
                )
            elif self.patient_profile.communication_style == "anxious":
                return f"I have {', '.join(self.patient_profile.conditions)}. Is that a problem?"
            else:  # rushed
                return f"{', '.join(self.patient_profile.conditions)}."

    def _generate_visit_reason_response(self) -> str:
        """Generate response for visit reason collection."""
        reason = (
            self.patient_profile.visit_reasons[0]
            if self.patient_profile.visit_reasons
            else "Checkup"
        )

        if self.patient_profile.communication_style == "cooperative":
            return f"I'm here for {reason}."
        elif self.patient_profile.communication_style == "reluctant":
            return f"{reason}."
        elif self.patient_profile.communication_style == "confused":
            return f"I think I'm here for... {reason}."
        elif self.patient_profile.communication_style == "anxious":
            return (
                f"I'm here for {reason}. Is that why you're asking all these questions?"
            )
        else:  # rushed
            return f"{reason}."

    def _generate_symptoms_response(self) -> str:
        """Generate response for symptoms collection."""
        if not self.patient_profile.symptoms:
            if self.patient_profile.communication_style == "cooperative":
                return "I don't have any current symptoms."
            elif self.patient_profile.communication_style == "reluctant":
                return "None."
            elif self.patient_profile.communication_style == "confused":
                return "I don't think I have any symptoms... no, none."
            elif self.patient_profile.communication_style == "anxious":
                return "No symptoms. Why do you need to know?"
            else:  # rushed
                return "None."
        else:
            symptom_desc = []
            for symptom in self.patient_profile.symptoms:
                desc = f"{symptom['symptom']} (severity {symptom['severity']}/10, duration {symptom['duration']})"
                symptom_desc.append(desc)

            if self.patient_profile.communication_style == "cooperative":
                return f"I have {', '.join(symptom_desc)}."
            elif self.patient_profile.communication_style == "reluctant":
                return f"{', '.join(symptom_desc)}."
            elif self.patient_profile.communication_style == "confused":
                return f"I think I have... {', '.join(symptom_desc)}."
            elif self.patient_profile.communication_style == "anxious":
                return f"I have {', '.join(symptom_desc)}. Is that serious?"
            else:  # rushed
                return f"{', '.join(symptom_desc)}."

    def generate_next_message(
        self, message: ValidUserInputMessage, state: UserState
    ) -> tuple[UserMessage, UserState]:
        """Override to add healthcare-specific response generation."""
        # Try healthcare-specific response first
        if hasattr(message, "content") and message.content:
            healthcare_response = self.generate_healthcare_response(message.content)
            if (
                healthcare_response
                != "I'm not sure what you're asking. Could you please clarify?"
            ):
                # Create a simple user message with the healthcare response
                user_message = UserMessage(
                    role="user",
                    content=healthcare_response,
                )
                state.messages.append(user_message)
                return user_message, state

        # Fall back to the base implementation
        return super().generate_next_message(message, state)

    def set_patient_profile(self, profile: PatientProfile):
        """Set a specific patient profile for the simulator."""
        self.patient_profile = profile

    def get_patient_profile(self) -> PatientProfile:
        """Get the current patient profile."""
        return self.patient_profile
