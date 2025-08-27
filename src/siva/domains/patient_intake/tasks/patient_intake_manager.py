import json
import random
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from siva.data_model.tasks import Task, StructuredUserInstructions
from siva.utils import DATA_DIR


@dataclass
class PatientScenario:
    """A patient intake scenario for testing."""

    id: str
    name: str
    age: int
    reason_for_visit: str
    symptoms: List[Dict[str, Any]]
    medical_history: Dict[str, Any]
    communication_style: str
    complexity: str  # "simple", "moderate", "complex"


class PatientIntakeTaskManager:
    """Manages patient intake task generation for testing."""

    def __init__(self):
        self.scenarios = self._create_scenarios()

    def _create_scenarios(self) -> List[PatientScenario]:
        """Create realistic patient intake scenarios."""
        scenarios = []

        # Simple scenarios - basic information collection
        scenarios.extend(
            [
                PatientScenario(
                    id="PI001",
                    name="John Smith",
                    age=35,
                    reason_for_visit="Annual checkup",
                    symptoms=[],
                    medical_history={
                        "prescriptions": ["Lisinopril 10mg daily"],
                        "allergies": ["Penicillin"],
                        "conditions": ["Hypertension"],
                    },
                    communication_style="cooperative",
                    complexity="simple",
                ),
                PatientScenario(
                    id="PI002",
                    name="Sarah Johnson",
                    age=28,
                    reason_for_visit="Follow-up appointment",
                    symptoms=[],
                    medical_history={
                        "prescriptions": [],
                        "allergies": [],
                        "conditions": [],
                    },
                    communication_style="cooperative",
                    complexity="simple",
                ),
                PatientScenario(
                    id="PI003",
                    name="Michael Davis",
                    age=45,
                    reason_for_visit="Cold symptoms",
                    symptoms=[
                        {"name": "Runny nose", "severity": 3, "duration": "3 days"},
                        {"name": "Sore throat", "severity": 4, "duration": "2 days"},
                    ],
                    medical_history={
                        "prescriptions": [],
                        "allergies": ["Peanuts"],
                        "conditions": [],
                    },
                    communication_style="cooperative",
                    complexity="simple",
                ),
            ]
        )

        # Moderate scenarios - more complex information
        scenarios.extend(
            [
                PatientScenario(
                    id="PI004",
                    name="Lisa Garcia",
                    age=52,
                    reason_for_visit="Chest pain",
                    symptoms=[
                        {"name": "Chest pain", "severity": 7, "duration": "2 hours"},
                        {
                            "name": "Shortness of breath",
                            "severity": 6,
                            "duration": "2 hours",
                        },
                    ],
                    medical_history={
                        "prescriptions": [
                            "Metformin 500mg twice daily",
                            "Atorvastatin 20mg daily",
                        ],
                        "allergies": ["Sulfa drugs"],
                        "conditions": ["Diabetes", "High cholesterol"],
                    },
                    communication_style="anxious",
                    complexity="moderate",
                ),
                PatientScenario(
                    id="PI005",
                    name="Robert Wilson",
                    age=67,
                    reason_for_visit="Follow-up for arthritis",
                    symptoms=[
                        {"name": "Joint pain", "severity": 5, "duration": "2 weeks"},
                        {"name": "Stiffness", "severity": 4, "duration": "2 weeks"},
                    ],
                    medical_history={
                        "prescriptions": [
                            "Ibuprofen 400mg as needed",
                            "Omeprazole 20mg daily",
                        ],
                        "allergies": ["Aspirin"],
                        "conditions": ["Arthritis", "GERD"],
                    },
                    communication_style="cooperative",
                    complexity="moderate",
                ),
            ]
        )

        # Complex scenarios - challenging communication or multiple issues
        scenarios.extend(
            [
                PatientScenario(
                    id="PI006",
                    name="Maria Rodriguez",
                    age=38,
                    reason_for_visit="Multiple symptoms",
                    symptoms=[
                        {"name": "Headache", "severity": 8, "duration": "1 week"},
                        {"name": "Nausea", "severity": 6, "duration": "3 days"},
                        {"name": "Fatigue", "severity": 7, "duration": "1 week"},
                    ],
                    medical_history={
                        "prescriptions": ["Zoloft 50mg daily", "Xanax 0.5mg as needed"],
                        "allergies": ["Codeine"],
                        "conditions": ["Depression", "Anxiety"],
                    },
                    communication_style="confused",
                    complexity="complex",
                ),
                PatientScenario(
                    id="PI007",
                    name="David Thompson",
                    age=29,
                    reason_for_visit="Emergency symptoms",
                    symptoms=[
                        {
                            "name": "Severe chest pain",
                            "severity": 9,
                            "duration": "30 minutes",
                        },
                        {
                            "name": "Difficulty breathing",
                            "severity": 8,
                            "duration": "30 minutes",
                        },
                        {"name": "Sweating", "severity": 7, "duration": "30 minutes"},
                    ],
                    medical_history={
                        "prescriptions": [],
                        "allergies": ["Shellfish"],
                        "conditions": [],
                    },
                    communication_style="distressed",
                    complexity="complex",
                ),
            ]
        )

        return scenarios

    def create_task(self, scenario: PatientScenario) -> Task:
        """Create a task from a patient scenario."""

        # Create user instructions
        instructions = self._create_instructions(scenario)

        # Create task description
        description = f"Patient intake for {scenario.name} ({scenario.age} years old) - {scenario.reason_for_visit}"

        # Create evaluation criteria
        evaluation_criteria = self._create_evaluation_criteria(scenario)

        task = Task(
            id=f"patient_intake_{scenario.id}",
            description={
                "purpose": "Patient intake information collection",
                "info": description,
            },
            user_scenario={
                "instructions": instructions,
                "persona": self._get_persona(scenario.communication_style),
            },
            ticket=f"Patient intake for {scenario.name} - {scenario.reason_for_visit}",
            initial_state={},
            evaluation_criteria=evaluation_criteria,
        )

        return task

    def _create_instructions(
        self, scenario: PatientScenario
    ) -> StructuredUserInstructions:
        """Create user instructions for the scenario."""

        # Build known info
        known_info = f"""
        Name: {scenario.name}
        Age: {scenario.age} years old
        Reason for visit: {scenario.reason_for_visit}
        """

        if scenario.symptoms:
            known_info += "\nCurrent symptoms:\n"
            for symptom in scenario.symptoms:
                known_info += f"- {symptom['name']} (severity: {symptom['severity']}/10, duration: {symptom['duration']})\n"

        if scenario.medical_history["prescriptions"]:
            known_info += f"\nCurrent prescriptions: {', '.join(scenario.medical_history['prescriptions'])}"

        if scenario.medical_history["allergies"]:
            known_info += (
                f"\nKnown allergies: {', '.join(scenario.medical_history['allergies'])}"
            )

        if scenario.medical_history["conditions"]:
            known_info += f"\nMedical conditions: {', '.join(scenario.medical_history['conditions'])}"

        # Build task instructions
        task_instructions = f"""
        You are {scenario.name}, a {scenario.age}-year-old patient visiting Tsidi Health Services.
        You are here for: {scenario.reason_for_visit}
        
        Your communication style is: {scenario.communication_style}
        
        You should:
        1. Respond naturally to the agent's questions
        2. Provide the information listed in your known info when asked
        3. Be {scenario.communication_style} in your communication
        4. Answer questions about your symptoms, medications, and medical history
        5. Cooperate with the intake process
        """

        return StructuredUserInstructions(
            task_instructions=task_instructions,
            domain="patient_intake",
            reason_for_call=scenario.reason_for_visit,
            known_info=known_info,
        )

    def _get_persona(self, communication_style: str) -> str:
        """Get persona description based on communication style."""
        personas = {
            "cooperative": "You are a cooperative patient who is willing to provide information and follow instructions.",
            "anxious": "You are an anxious patient who may need reassurance and clear explanations.",
            "confused": "You are a confused patient who may need help understanding questions and may provide unclear responses.",
            "distressed": "You are a distressed patient who may be in pain or experiencing severe symptoms.",
            "reluctant": "You are a reluctant patient who may be hesitant to provide personal information.",
        }
        return personas.get(communication_style, personas["cooperative"])

    def _create_evaluation_criteria(self, scenario: PatientScenario) -> Dict[str, Any]:
        """Create evaluation criteria for the task."""

        # Expected actions - the agent should collect all required information
        expected_actions = [
            {
                "action_id": "verify_fullname",
                "name": "verify_fullname",
                "requestor": "assistant",
                "arguments": {"names": [{"full_name": scenario.name}]},
            },
            {
                "action_id": "verify_birthday",
                "name": "verify_birthday",
                "requestor": "assistant",
                "arguments": {"birthday": self._calculate_birthday(scenario.age)},
            },
        ]

        # Add prescription verification if applicable
        if scenario.medical_history["prescriptions"]:
            expected_actions.append(
                {
                    "action_id": "list_prescriptions",
                    "name": "list_prescriptions",
                    "requestor": "assistant",
                    "arguments": {
                        "prescriptions": scenario.medical_history["prescriptions"]
                    },
                }
            )

        # Add allergy verification if applicable
        if scenario.medical_history["allergies"]:
            expected_actions.append(
                {
                    "action_id": "list_allergies",
                    "name": "list_allergies",
                    "requestor": "assistant",
                    "arguments": {"allergies": scenario.medical_history["allergies"]},
                }
            )

        # Add conditions verification if applicable
        if scenario.medical_history["conditions"]:
            expected_actions.append(
                {
                    "action_id": "list_conditions",
                    "name": "list_conditions",
                    "requestor": "assistant",
                    "arguments": {"conditions": scenario.medical_history["conditions"]},
                }
            )

        # Add visit reasons verification
        expected_actions.append(
            {
                "action_id": "list_visit_reasons",
                "name": "list_visit_reasons",
                "requestor": "assistant",
                "arguments": {"visit_reasons": [scenario.reason_for_visit]},
            }
        )

        # Add symptoms collection if applicable
        if scenario.symptoms:
            expected_actions.append(
                {
                    "action_id": "collect_detailed_symptoms",
                    "name": "collect_detailed_symptoms",
                    "requestor": "assistant",
                    "arguments": {"symptoms": scenario.symptoms},
                }
            )

        # Add routing decision
        expected_actions.append(
            {
                "action_id": "determine_routing",
                "name": "determine_routing",
                "requestor": "assistant",
                "arguments": {"route": self._determine_route(scenario)},
            }
        )

        return {
            "actions": expected_actions,
            "env_assertions": [],
            "reward_basis": ["ACTION"],
        }

    def _calculate_birthday(self, age: int) -> str:
        """Calculate a realistic birthday for the given age."""
        current_year = datetime.now().year
        birth_year = current_year - age
        # Use a random month and day
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Use 28 to avoid month/day issues
        return f"{birth_year}-{month:02d}-{day:02d}"

    def _determine_route(self, scenario: PatientScenario) -> str:
        """Determine appropriate care route based on symptoms."""
        if not scenario.symptoms:
            return "Routine"

        # Check for emergency symptoms
        emergency_symptoms = [
            "severe chest pain",
            "difficulty breathing",
            "stroke",
            "unconscious",
        ]
        for symptom in scenario.symptoms:
            if any(
                emergency in symptom["name"].lower() for emergency in emergency_symptoms
            ):
                return "Emergency"

        # Check for urgent symptoms
        urgent_symptoms = ["chest pain", "high fever", "severe pain"]
        for symptom in scenario.symptoms:
            if any(urgent in symptom["name"].lower() for urgent in urgent_symptoms):
                return "Urgent"

        # Check severity
        max_severity = max(symptom["severity"] for symptom in scenario.symptoms)
        if max_severity >= 7:
            return "Urgent"
        elif max_severity >= 5:
            return "Routine"
        else:
            return "Self-Care"

    def create_tasks(self, save_tasks: bool = True) -> List[Task]:
        """Create all patient intake tasks."""
        tasks = []

        for scenario in self.scenarios:
            task = self.create_task(scenario)
            tasks.append(task)
            print(f"Created task: {task.id}")

        if save_tasks:
            file_path = DATA_DIR / "siva" / "domains" / "patient_intake" / "tasks.json"
            with open(file_path, "w") as f:
                json.dump([t.model_dump() for t in tasks], f, indent=2)
            print(f"Saved {len(tasks)} tasks to {file_path}")

        return tasks


def create_patient_intake_tasks(save_tasks: bool = True) -> List[Task]:
    """Create patient intake tasks."""
    manager = PatientIntakeTaskManager()
    return manager.create_tasks(save_tasks)


if __name__ == "__main__":
    create_patient_intake_tasks()
