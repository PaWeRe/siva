"""
Comprehensive patient scenario data for testing SIVA learning system.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class RouteType(Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    SELF_CARE = "self_care"
    INFORMATION = "information"


@dataclass
class PatientScenario:
    """Represents a complete patient interaction scenario."""

    name: str
    route: RouteType
    conversation_flow: List[str]
    expected_symptoms: List[str]
    severity_indicators: List[str]
    timeline_urgency: str
    demographic: Dict[str, str]
    description: str


# Emergency scenarios - require immediate attention
EMERGENCY_SCENARIOS = [
    PatientScenario(
        name="Acute Myocardial Infarction",
        route=RouteType.EMERGENCY,
        conversation_flow=[
            "Hello, I'm John Miller, I'm 58 years old, born March 15, 1966",
            "I take metoprolol for high blood pressure",
            "No allergies",
            "I have high blood pressure and high cholesterol",
            "I'm having severe crushing chest pain that started 20 minutes ago",
            "The pain is 10 out of 10, feels like an elephant sitting on my chest",
            "It's radiating to my left arm and jaw",
            "I'm sweating profusely and feel nauseous",
            "I also feel short of breath and dizzy",
        ],
        expected_symptoms=[
            "severe chest pain",
            "radiation to arm/jaw",
            "sweating",
            "nausea",
            "shortness of breath",
        ],
        severity_indicators=[
            "10/10 pain",
            "crushing sensation",
            "radiation",
            "associated symptoms",
        ],
        timeline_urgency="acute onset - 20 minutes",
        demographic={
            "age": "58",
            "gender": "male",
            "risk_factors": "hypertension, hyperlipidemia",
        },
        description="Classic presentation of heart attack with typical symptoms",
    ),
    PatientScenario(
        name="Stroke Symptoms",
        route=RouteType.EMERGENCY,
        conversation_flow=[
            "Hi, I'm Sarah Chen, I'm 72, born August 8, 1952",
            "I take warfarin for atrial fibrillation",
            "No allergies",
            "I have atrial fibrillation and diabetes",
            "My daughter called because something's wrong with me",
            "I suddenly can't speak clearly about 30 minutes ago",
            "The right side of my face feels droopy",
            "My right arm feels weak and heavy",
            "I'm having trouble understanding what people are saying",
            "I feel confused and my vision seems blurry",
        ],
        expected_symptoms=[
            "speech difficulty",
            "facial drooping",
            "arm weakness",
            "confusion",
        ],
        severity_indicators=[
            "sudden onset",
            "neurological deficits",
            "FAST criteria positive",
        ],
        timeline_urgency="acute onset - 30 minutes",
        demographic={
            "age": "72",
            "gender": "female",
            "risk_factors": "afib, diabetes, anticoagulated",
        },
        description="Acute stroke with clear neurological deficits",
    ),
    PatientScenario(
        name="Severe Allergic Reaction",
        route=RouteType.EMERGENCY,
        conversation_flow=[
            "I'm Mike Johnson, 34 years old, birthday June 22, 1990",
            "No regular medications",
            "I'm allergic to peanuts",
            "No medical conditions",
            "I think I accidentally ate something with peanuts 15 minutes ago",
            "My throat is closing up and it's hard to breathe",
            "My whole body is covered in hives",
            "My face and lips are swelling",
            "I feel like I'm going to pass out",
            "This is getting worse by the minute",
        ],
        expected_symptoms=[
            "throat closing",
            "difficulty breathing",
            "hives",
            "facial swelling",
        ],
        severity_indicators=[
            "airway compromise",
            "systemic reaction",
            "rapid progression",
        ],
        timeline_urgency="acute onset - 15 minutes, progressing",
        demographic={"age": "34", "gender": "male", "known_allergies": "peanuts"},
        description="Anaphylactic reaction requiring immediate intervention",
    ),
]

# Urgent scenarios - need same-day attention
URGENT_SCENARIOS = [
    PatientScenario(
        name="High Fever with Concerning Symptoms",
        route=RouteType.URGENT,
        conversation_flow=[
            "Hello, I'm Lisa Rodriguez, 29 years old, born November 3, 1995",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I've had a high fever for 3 days now",
            "My temperature has been 103-104°F",
            "I have a severe headache that won't go away",
            "The headache is 8 out of 10, throbbing",
            "I'm having chills and my whole body aches",
            "I also have a stiff neck and bright lights hurt my eyes",
        ],
        expected_symptoms=[
            "high fever",
            "severe headache",
            "neck stiffness",
            "photophobia",
        ],
        severity_indicators=[
            "persistent high fever",
            "neurological signs",
            "concerning duration",
        ],
        timeline_urgency="3 days duration, high fever",
        demographic={"age": "29", "gender": "female", "immunocompetent": True},
        description="Possible meningitis or serious infection requiring urgent evaluation",
    ),
    PatientScenario(
        name="Severe Abdominal Pain",
        route=RouteType.URGENT,
        conversation_flow=[
            "I'm Robert Kim, 45, birthday February 14, 1979",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I have severe abdominal pain that started this morning",
            "The pain is in my right lower abdomen",
            "It's 8 out of 10 and getting worse",
            "It started around my belly button and moved to the right side",
            "I've vomited twice and have no appetite",
            "Walking makes it much worse",
        ],
        expected_symptoms=[
            "severe abdominal pain",
            "right lower quadrant",
            "vomiting",
            "anorexia",
        ],
        severity_indicators=[
            "8/10 pain",
            "classic migration pattern",
            "peritoneal signs",
        ],
        timeline_urgency="acute onset this morning, worsening",
        demographic={"age": "45", "gender": "male"},
        description="Possible appendicitis requiring urgent surgical evaluation",
    ),
    PatientScenario(
        name="Persistent Chest Pain",
        route=RouteType.URGENT,
        conversation_flow=[
            "Hi, I'm Emma Thompson, 52, born May 20, 1972",
            "I take lisinopril for blood pressure",
            "No allergies",
            "I have high blood pressure",
            "I've been having chest pain on and off for 2 days",
            "It's not as severe as a heart attack, maybe 6 out of 10",
            "The pain comes and goes, especially when I walk upstairs",
            "It feels tight and pressure-like",
            "Sometimes it goes to my left shoulder",
            "Rest makes it better but I'm worried",
        ],
        expected_symptoms=["chest pain", "exertional", "pressure-like", "radiation"],
        severity_indicators=[
            "exertional pattern",
            "cardiac risk factors",
            "concerning pattern",
        ],
        timeline_urgency="2 days, intermittent but concerning",
        demographic={"age": "52", "gender": "female", "risk_factors": "hypertension"},
        description="Possible unstable angina requiring urgent cardiac evaluation",
    ),
]

# Routine scenarios - can wait for normal appointment
ROUTINE_SCENARIOS = [
    PatientScenario(
        name="Annual Physical Exam",
        route=RouteType.ROUTINE,
        conversation_flow=[
            "Hello, I'm David Wilson, 35 years old, born September 12, 1989",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I'm here for my yearly physical exam",
            "No specific symptoms or concerns",
            "Just want to make sure everything is okay",
            "I exercise regularly and eat well",
            "Family history of diabetes, so I want to stay on top of things",
        ],
        expected_symptoms=[],
        severity_indicators=[],
        timeline_urgency="routine preventive care",
        demographic={"age": "35", "gender": "male", "health_conscious": True},
        description="Routine preventive care visit",
    ),
    PatientScenario(
        name="Chronic Condition Follow-up",
        route=RouteType.ROUTINE,
        conversation_flow=[
            "I'm Helen Foster, 68, birthday January 30, 1956",
            "I take metformin and atorvastatin",
            "No allergies",
            "I have diabetes and high cholesterol",
            "I'm here for my regular diabetes check-up",
            "My blood sugars have been well controlled",
            "No new symptoms or problems",
            "I check my sugars daily and they're usually 90-130",
            "I've been following my diet and exercise plan",
        ],
        expected_symptoms=[],
        severity_indicators=[],
        timeline_urgency="routine follow-up",
        demographic={
            "age": "68",
            "gender": "female",
            "chronic_conditions": "diabetes, hyperlipidemia",
        },
        description="Routine management of stable chronic conditions",
    ),
    PatientScenario(
        name="Mild Ongoing Issue",
        route=RouteType.ROUTINE,
        conversation_flow=[
            "Hi, I'm Tom Anderson, 42, born April 7, 1982",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I've been having some mild back pain for about a month",
            "It's maybe 3 out of 10, comes and goes",
            "Probably from sitting at my desk too much",
            "It's not interfering with my daily activities",
            "I've been doing some stretches and it helps a bit",
        ],
        expected_symptoms=["mild back pain", "chronic", "activity-related"],
        severity_indicators=["low severity", "functional", "manageable"],
        timeline_urgency="chronic, non-urgent",
        demographic={"age": "42", "gender": "male", "occupation": "desk job"},
        description="Mild chronic back pain suitable for routine evaluation",
    ),
]

# Self-care scenarios - can manage at home
SELF_CARE_SCENARIOS = [
    PatientScenario(
        name="Common Cold",
        route=RouteType.SELF_CARE,
        conversation_flow=[
            "Hello, I'm Amy Parker, 26, born December 15, 1998",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I have a runny nose and mild cough for 3 days",
            "The symptoms are maybe 2 out of 10 severity",
            "Just typical cold symptoms, no fever",
            "I'm drinking lots of fluids and resting",
            "It seems to be getting a little better each day",
        ],
        expected_symptoms=["runny nose", "mild cough", "no fever"],
        severity_indicators=["mild symptoms", "improving", "viral pattern"],
        timeline_urgency="3 days, stable/improving",
        demographic={"age": "26", "gender": "female", "health_status": "healthy"},
        description="Typical viral upper respiratory infection",
    ),
    PatientScenario(
        name="Minor Headache",
        route=RouteType.SELF_CARE,
        conversation_flow=[
            "I'm James Lee, 31, birthday August 18, 1993",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I have a mild headache that started yesterday",
            "It's about 3 out of 10, not too bad",
            "I think it's from not drinking enough water",
            "I've been stressed at work lately",
            "Ibuprofen helps and it's getting better",
        ],
        expected_symptoms=["mild headache", "tension-type"],
        severity_indicators=[
            "low severity",
            "responsive to OTC meds",
            "identifiable triggers",
        ],
        timeline_urgency="yesterday, mild and improving",
        demographic={"age": "31", "gender": "male", "work_stress": True},
        description="Tension headache manageable with self-care",
    ),
    PatientScenario(
        name="Minor Digestive Issue",
        route=RouteType.SELF_CARE,
        conversation_flow=[
            "Hi, I'm Rachel Green, 28, born July 25, 1996",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I've had some mild stomach upset for 2 days",
            "Just some bloating and mild discomfort",
            "Maybe 2 out of 10 for severity",
            "I think it's from eating too much spicy food this weekend",
            "I'm eating bland foods and it's getting better",
        ],
        expected_symptoms=["mild stomach upset", "bloating", "dietary related"],
        severity_indicators=["mild severity", "improving", "clear trigger"],
        timeline_urgency="2 days, mild and resolving",
        demographic={"age": "28", "gender": "female", "dietary_indiscretion": True},
        description="Minor digestive upset from dietary indiscretion",
    ),
]

# Information scenarios - seeking medical advice/information
INFORMATION_SCENARIOS = [
    PatientScenario(
        name="Medication Questions",
        route=RouteType.INFORMATION,
        conversation_flow=[
            "Hello, I'm Patricia Brown, 55, born October 10, 1969",
            "I take lisinopril and simvastatin",
            "No allergies",
            "I have high blood pressure and cholesterol",
            "I don't have any new symptoms",
            "I have questions about my medications",
            "Can I take ibuprofen with my blood pressure medicine?",
            "Also, what time of day is best to take my cholesterol pill?",
            "And do I need to avoid any foods?",
        ],
        expected_symptoms=[],
        severity_indicators=[],
        timeline_urgency="non-urgent information seeking",
        demographic={"age": "55", "gender": "female", "educated_patient": True},
        description="Medication counseling and drug interaction questions",
    ),
    PatientScenario(
        name="Preventive Care Questions",
        route=RouteType.INFORMATION,
        conversation_flow=[
            "I'm Mark Davis, 48, birthday March 3, 1976",
            "No medications",
            "No allergies",
            "No medical conditions",
            "I don't have any symptoms or problems",
            "I want to know about preventive screening",
            "When should I start getting colonoscopies?",
            "Do I need any heart tests at my age?",
            "My father had a heart attack at 55, should I be worried?",
        ],
        expected_symptoms=[],
        severity_indicators=[],
        timeline_urgency="preventive planning",
        demographic={"age": "48", "gender": "male", "family_history": "CAD"},
        description="Preventive care and screening guidelines information",
    ),
]

# Combined scenarios list
ALL_SCENARIOS = {
    "emergency": EMERGENCY_SCENARIOS,
    "urgent": URGENT_SCENARIOS,
    "routine": ROUTINE_SCENARIOS,
    "self_care": SELF_CARE_SCENARIOS,
    "information": INFORMATION_SCENARIOS,
}


def get_all_scenarios() -> List[PatientScenario]:
    """Get all patient scenarios as a flat list."""
    scenarios = []
    for scenario_list in ALL_SCENARIOS.values():
        scenarios.extend(scenario_list)
    return scenarios


def get_scenarios_by_route(route: RouteType) -> List[PatientScenario]:
    """Get scenarios for a specific route type."""
    return ALL_SCENARIOS.get(route.value, [])


def get_scenario_by_name(name: str) -> PatientScenario:
    """Get a specific scenario by name."""
    for scenario in get_all_scenarios():
        if scenario.name == name:
            return scenario
    raise ValueError(f"Scenario '{name}' not found")
