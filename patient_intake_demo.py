#!/usr/bin/env python3
"""
Patient Intake Learning Progression Demo

This demo showcases how SIVA learns from patient intake cases, starting with no experience
and gradually building confidence through human feedback and similar case recognition.

The demo shows:
1. Initial cases with no experience - system escalates due to low confidence
2. Learning cases - system learns from human feedback
3. Experienced cases - system makes confident decisions based on learned patterns
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

BASE_URL = "http://localhost:8000"


class CareRoute(Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    SELF_CARE = "self_care"
    INFORMATION = "information"


@dataclass
class PatientCase:
    name: str
    description: str
    patient_info: Dict[str, Any]
    symptoms: Dict[str, Any]
    expected_route: CareRoute
    reasoning: str
    learning_stage: str  # "initial", "learning", "experienced"
    difficulty: str
    escalation_expected: bool


class PatientIntakeDemo:
    """Patient intake demo focusing on learning progression."""

    def __init__(self):
        self.base_url = BASE_URL
        self.cases_processed = 0

    def clear_system(self):
        """Reset the system to start fresh."""
        try:
            response = requests.post(f"{self.base_url}/dashboard/reset")
            if response.status_code == 200:
                print("✅ System reset successfully")
                return True
            else:
                print(f"❌ Reset failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Reset error: {e}")
            return False

    def get_system_stats(self):
        """Get current system statistics."""
        try:
            response = requests.get(f"{self.base_url}/dashboard/metrics")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Stats error: {e}")
        return {}

    def simulate_patient_conversation(
        self, case: PatientCase
    ) -> tuple[Optional[str], bool]:
        """Simulate a patient intake conversation."""

        print(f"  🎯 Starting patient case: {case.name}")

        # Create conversation messages based on case
        messages = self._create_patient_messages(case)

        # Generate unique session ID
        session_id = f"patient_intake_{case.learning_stage}_{self.cases_processed}_{uuid.uuid4().hex[:8]}"

        # Send each message in the conversation
        for i, message in enumerate(messages):
            payload = {"session_id": session_id, "message": message}
            try:
                response = requests.post(f"{self.base_url}/chat", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    print(f"  📤 Step {i+1}: {message[:60]}...")
                    print(f"  📥 Agent: {result['reply'][:100]}...")

                    # Check if escalated
                    if "escalation" in result:
                        agent_prediction = result["escalation"]["agent_prediction"]
                        print(f"  🚨 ESCALATED: Agent predicted '{agent_prediction}'")
                        return agent_prediction, True

                    if result.get("end_call", False):
                        print(f"  ✅ Patient intake completed")
                        break

            except Exception as e:
                print(f"  ❌ Error: {e}")
                return None, False

        return None, False

    def _create_patient_messages(self, case: PatientCase) -> List[str]:
        """Create conversation messages for patient case."""
        messages = []

        # Initial greeting
        messages.append("Hi, I'm here for my appointment")

        # Patient identification
        messages.append(
            f"I'm {case.patient_info['name']}, born {case.patient_info['birthday']}"
        )

        # Medications
        if case.patient_info.get("medications"):
            meds = ", ".join(
                [
                    f"{med['name']} for {med['indication']}"
                    for med in case.patient_info["medications"]
                ]
            )
            messages.append(f"I take {meds}")
        else:
            messages.append("I don't take any medications")

        # Allergies
        if case.patient_info.get("allergies"):
            allergies = ", ".join(case.patient_info["allergies"])
            messages.append(f"I'm allergic to {allergies}")
        else:
            messages.append("I have no known allergies")

        # Medical conditions
        if case.patient_info.get("conditions"):
            conditions = ", ".join(case.patient_info["conditions"])
            messages.append(f"I have {conditions}")
        else:
            messages.append("I have no medical conditions")

        # Reason for visit
        messages.append(f"I'm here because {case.symptoms['reason_for_visit']}")

        # Detailed symptoms
        messages.append(
            f"I've been experiencing {case.symptoms['primary_symptom']} for {case.symptoms['duration']}"
        )
        messages.append(
            f"The {case.symptoms['primary_symptom']} is {case.symptoms['severity']}/10 severity"
        )

        # Additional symptoms
        if case.symptoms.get("associated_symptoms"):
            additional = ", ".join(case.symptoms["associated_symptoms"])
            messages.append(f"I also have {additional}")

        return messages

    def provide_human_feedback(
        self,
        session_id: str,
        agent_prediction: str,
        correct_route: CareRoute,
        case: PatientCase,
    ) -> bool:
        """Provide human expert feedback."""
        feedback_payload = {
            "session_id": session_id,
            "agent_prediction": agent_prediction,
            "human_label": correct_route.value,
        }

        try:
            response = requests.post(
                f"{self.base_url}/escalation/feedback", json=feedback_payload
            )
            if response.status_code == 200:
                result = response.json()
                is_correct = agent_prediction == correct_route.value
                outcome = "✅ Correct" if is_correct else "❌ Wrong"
                print(
                    f"  👨‍⚕️ Human feedback: {agent_prediction} → {correct_route.value} {outcome}"
                )

                # Show learning progress
                if case.learning_stage == "learning":
                    print(f"  📚 System learning from this case...")
                elif case.learning_stage == "experienced":
                    print(f"  🧠 System applying learned patterns...")

                return result.get("training_added", False)
            else:
                print(f"  ❌ Feedback failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Feedback error: {e}")
            return False

    def run_learning_progression_demo(self):
        """Run the patient intake learning progression demo."""
        print("\n🏥 PATIENT INTAKE LEARNING PROGRESSION DEMO")
        print("=" * 70)
        print("This demo shows how SIVA learns from patient intake cases")
        print("The system starts with no experience and learns from human feedback")
        print("Demonstrating progression from escalation to confident decision-making")
        print()

        # Define patient cases in learning progression
        cases = [
            PatientCase(
                name="Sarah Johnson - Atypical Heart Attack (Initial)",
                description="First case of atypical heart attack presentation",
                patient_info={
                    "name": "Sarah Johnson",
                    "birthday": "March 15, 1965",
                    "medications": [
                        {"name": "atorvastatin", "indication": "cholesterol"}
                    ],
                    "allergies": [],
                    "conditions": ["high cholesterol", "diabetes"],
                },
                symptoms={
                    "reason_for_visit": "I've been feeling very tired and nauseous",
                    "primary_symptom": "fatigue and nausea",
                    "duration": "2 days",
                    "severity": 7,
                    "associated_symptoms": [
                        "jaw pain",
                        "indigestion",
                        "shortness of breath",
                    ],
                },
                expected_route=CareRoute.EMERGENCY,
                reasoning="Atypical heart attack symptoms in diabetic patient require emergency evaluation",
                learning_stage="initial",
                difficulty="High - atypical presentation",
                escalation_expected=True,
            ),
            PatientCase(
                name="Janet Murphy - Similar Atypical Heart Attack (Learning)",
                description="Similar case after learning from first example",
                patient_info={
                    "name": "Janet Murphy",
                    "birthday": "February 14, 1966",
                    "medications": [{"name": "metformin", "indication": "diabetes"}],
                    "allergies": [],
                    "conditions": ["diabetes", "high blood pressure"],
                },
                symptoms={
                    "reason_for_visit": "I've been having upper back pain and nausea",
                    "primary_symptom": "upper back pain and nausea",
                    "duration": "4 hours",
                    "severity": 6,
                    "associated_symptoms": [
                        "jaw pain",
                        "shortness of breath",
                        "sweating",
                    ],
                },
                expected_route=CareRoute.EMERGENCY,
                reasoning="Similar to previous case but system now has learned examples",
                learning_stage="learning",
                difficulty="Medium - now has learned examples",
                escalation_expected=True,
            ),
            PatientCase(
                name="Maria Rodriguez - Another Atypical Heart Attack (Experienced)",
                description="Third similar case showing improved confidence",
                patient_info={
                    "name": "Maria Rodriguez",
                    "birthday": "July 8, 1962",
                    "medications": [
                        {"name": "lisinopril", "indication": "blood pressure"}
                    ],
                    "allergies": ["penicillin"],
                    "conditions": ["hypertension", "arthritis"],
                },
                symptoms={
                    "reason_for_visit": "I've been having unusual fatigue and chest discomfort",
                    "primary_symptom": "fatigue and chest discomfort",
                    "duration": "1 day",
                    "severity": 5,
                    "associated_symptoms": [
                        "jaw pain",
                        "sweating",
                        "pressure sensation",
                    ],
                },
                expected_route=CareRoute.EMERGENCY,
                reasoning="System now confident in recognizing atypical heart attack patterns",
                learning_stage="experienced",
                difficulty="Low - system now confident",
                escalation_expected=False,
            ),
            PatientCase(
                name="Lisa Chen - Pediatric Fever (Initial)",
                description="High fever in young child requiring immediate attention",
                patient_info={
                    "name": "Lisa Chen",
                    "birthday": "August 10, 1988",
                    "medications": [],
                    "allergies": [],
                    "conditions": [],
                },
                symptoms={
                    "reason_for_visit": "I'm here with my 18-month-old daughter who has a fever",
                    "primary_symptom": "high fever in child",
                    "duration": "6 hours",
                    "severity": 10,
                    "associated_symptoms": [
                        "lethargy",
                        "crying inconsolably",
                        "stiff neck",
                        "barely responsive",
                    ],
                },
                expected_route=CareRoute.EMERGENCY,
                reasoning="Pediatric fever with neurological symptoms requires immediate evaluation",
                learning_stage="initial",
                difficulty="High - pediatric emergency signs",
                escalation_expected=True,
            ),
            PatientCase(
                name="Michael Torres - Mental Health Crisis (Initial)",
                description="Psychiatric emergency requiring immediate intervention",
                patient_info={
                    "name": "Michael Torres",
                    "birthday": "December 22, 1992",
                    "medications": [{"name": "sertraline", "indication": "depression"}],
                    "allergies": [],
                    "conditions": ["depression", "anxiety"],
                },
                symptoms={
                    "reason_for_visit": "I need help, I've been having dark thoughts",
                    "primary_symptom": "suicidal thoughts",
                    "duration": "1 week",
                    "severity": 9,
                    "associated_symptoms": [
                        "constant thoughts",
                        "worsening daily",
                        "has a plan",
                        "cannot stay safe",
                    ],
                },
                expected_route=CareRoute.EMERGENCY,
                reasoning="Active suicidal ideation with plan requires immediate psychiatric evaluation",
                learning_stage="initial",
                difficulty="High - suicide risk assessment",
                escalation_expected=True,
            ),
            PatientCase(
                name="Robert Kim - Stroke Mimicker (Learning)",
                description="Symptoms that could be stroke but are actually migraine",
                patient_info={
                    "name": "Robert Kim",
                    "birthday": "January 5, 1979",
                    "medications": [{"name": "sumatriptan", "indication": "migraines"}],
                    "allergies": ["aspirin"],
                    "conditions": ["chronic migraines"],
                },
                symptoms={
                    "reason_for_visit": "I'm having trouble speaking clearly",
                    "primary_symptom": "slurred speech and numbness",
                    "duration": "30 minutes",
                    "severity": 6,
                    "associated_symptoms": [
                        "right side numbness",
                        "recognizes migraine pattern",
                    ],
                },
                expected_route=CareRoute.URGENT,
                reasoning="Stroke-like symptoms but patient recognizes migraine pattern",
                learning_stage="learning",
                difficulty="Medium - requires stroke vs migraine differentiation",
                escalation_expected=True,
            ),
        ]

        print("📊 Starting with empty vector store...")
        initial_stats = self.get_system_stats()
        print(
            f"Vector store size: {len(initial_stats.get('vector_conversations', []))}"
        )
        print()

        # Run cases and track learning
        correct_predictions = 0
        total_cases = len(cases)
        escalations = 0

        for i, case in enumerate(cases, 1):
            print(f"🎯 PATIENT CASE {i}/{total_cases}: {case.name}")
            print(f"📝 {case.description}")
            print(
                f"👤 Patient: {case.patient_info['name']}, {case.patient_info['birthday']}"
            )
            print(f"🏥 Expected Route: {case.expected_route.value}")
            print(f"📚 Learning Stage: {case.learning_stage}")
            print(f"🔥 Difficulty: {case.difficulty}")
            print(f"🚨 Escalation Expected: {case.escalation_expected}")
            print()

            # Run the patient conversation
            agent_prediction, was_escalated = self.simulate_patient_conversation(case)

            if was_escalated:
                escalations += 1
                if agent_prediction:
                    # Provide human feedback
                    training_added = self.provide_human_feedback(
                        session_id=f"patient_{i}_{uuid.uuid4().hex[:8]}",
                        agent_prediction=agent_prediction,
                        correct_route=case.expected_route,
                        case=case,
                    )

                    # Track accuracy
                    if agent_prediction == case.expected_route.value:
                        correct_predictions += 1
                        print(f"  ✅ Agent made correct routing decision!")
                    else:
                        print(
                            f"  📚 Agent learned: {agent_prediction} → {case.expected_route.value}"
                        )

                    if training_added:
                        print(f"  💾 Added to training data")
            else:
                print(f"  ⚠️  No escalation occurred (system was confident)")

            # Show current learning progress
            current_stats = self.get_system_stats()
            vector_size = len(current_stats.get("vector_conversations", []))
            accuracy = (
                (correct_predictions / escalations) * 100 if escalations > 0 else 0
            )

            print(
                f"  📈 Progress: Vector store size: {vector_size}, Accuracy: {accuracy:.1f}%, Escalations: {escalations}"
            )
            print()

            self.cases_processed += 1
            time.sleep(1)

        # Final results
        print("🏁 PATIENT INTAKE DEMO COMPLETE!")
        print("=" * 50)
        final_stats = self.get_system_stats()
        final_accuracy = (
            (correct_predictions / escalations) * 100 if escalations > 0 else 0
        )

        print(f"📊 Final Patient Intake Results:")
        print(f"   • Patient cases processed: {total_cases}")
        print(f"   • Cases escalated: {escalations}")
        print(f"   • Agent accuracy: {final_accuracy:.1f}%")
        print(
            f"   • Vector store size: {len(final_stats.get('vector_conversations', []))}"
        )

        # Show what the agent learned
        print(f"\n🧠 Knowledge Acquired:")
        for conv in final_stats.get("vector_conversations", []):
            route = conv.get("correct_route", "unknown")
            symptoms = conv.get("symptoms_summary", "No description")[:80]
            print(f"   • {route.upper()}: {symptoms}...")

        print(f"\n🎯 Learning Progression Demonstrated:")
        print(f"   ✅ Initial Cases: System escalates due to lack of experience")
        print(f"   ✅ Learning Cases: System learns from human feedback")
        print(f"   ✅ Experienced Cases: System makes confident decisions")
        print(f"   ✅ Pattern Recognition: Identifies similar cases")
        print(f"   ✅ Confidence Building: Reduces unnecessary escalations")

        return final_stats

    def demonstrate_learning_phases(self):
        """Demonstrate the different learning phases."""
        print("\n📚 LEARNING PHASES DEMONSTRATION")
        print("=" * 50)
        print("Showing how the system progresses through learning phases")
        print()

        phases = [
            {
                "phase": "Initial",
                "description": "No prior experience",
                "behavior": "Escalates most cases",
                "confidence": "Low",
                "examples": "First atypical heart attack case",
            },
            {
                "phase": "Learning",
                "description": "Building experience from feedback",
                "behavior": "Escalates but learning patterns",
                "confidence": "Medium",
                "examples": "Similar cases with human feedback",
            },
            {
                "phase": "Experienced",
                "description": "Confident with learned patterns",
                "behavior": "Makes decisions independently",
                "confidence": "High",
                "examples": "Recognizes familiar patterns",
            },
        ]

        for phase in phases:
            print(f"🔄 {phase['phase']} Phase:")
            print(f"   • Description: {phase['description']}")
            print(f"   • Behavior: {phase['behavior']}")
            print(f"   • Confidence: {phase['confidence']}")
            print(f"   • Examples: {phase['examples']}")
            print()

        print("🎯 Key Benefits:")
        print("   • Reduces unnecessary escalations over time")
        print("   • Improves patient experience")
        print("   • Maintains safety through confidence assessment")
        print("   • Enables continuous learning")


def create_learning_flowchart():
    """Create a flowchart showing the learning progression."""
    flowchart = """
    PATIENT INTAKE LEARNING PROGRESSION FLOWCHART
    =============================================
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                    PATIENT PRESENTATION                        │
    │  • Patient arrives with symptoms                               │
    │  • System collects basic information                           │
    │  • Detailed symptom assessment                                 │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                SIMILAR CASE RETRIEVAL                          │
    │  • Search vector store for similar cases                       │
    │  • Calculate similarity scores                                 │
    │  • Assess confidence level                                     │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                CONFIDENCE ASSESSMENT                           │
    │                                                                 │
    │  ┌─────────────────────┐    ┌─────────────────────┐            │
    │  │   LOW CONFIDENCE    │    │  HIGH CONFIDENCE    │            │
    │  │                     │    │                     │            │
    │  │ • < 3 similar cases │    │ • ≥ 3 similar cases │            │
    │  │ • Escalate to human │    │ • Make decision     │            │
    │  │ • Learn from expert │    │ • Document case     │            │
    │  └─────────────────────┘    └─────────────────────┘            │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                LEARNING PHASES                                 │
    │                                                                 │
    │  ┌─────────────────────┐    ┌─────────────────────┐            │
    │  │      INITIAL        │    │      LEARNING       │            │
    │  │                     │    │                     │            │
    │  │ • No experience     │    │ • Building patterns │            │
    │  │ • Always escalate   │    │ • Learning from     │            │
    │  │ • High safety       │    │   feedback          │            │
    │  │                     │    │ • Medium confidence │            │
    │  └─────────────────────┘    └─────────────────────┘            │
    │                                                                 │
    │  ┌─────────────────────┐                                        │
    │  │    EXPERIENCED      │                                        │
    │  │                     │                                        │
    │  │ • Pattern recognition│                                        │
    │  │ • Confident decisions│                                        │
    │  │ • Reduced escalations│                                        │
    │  │ • High efficiency   │                                        │
    │  └─────────────────────┘                                        │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                KNOWLEDGE CAPTURE                               │
    │  • Extract insights from human feedback                        │
    │  • Store in vector database                                    │
    │  • Update decision patterns                                    │
    │  • Improve future confidence                                   │
    └─────────────────────────────────────────────────────────────────┘
    
    KEY FEATURES:
    • Progressive Learning: System improves with each case
    • Safety First: Always escalates when uncertain
    • Pattern Recognition: Identifies similar cases
    • Confidence Building: Reduces unnecessary escalations
    • Continuous Improvement: Learns from human expertise
    """

    return flowchart


if __name__ == "__main__":
    # Print the learning flowchart
    print(create_learning_flowchart())
    print("\n" + "=" * 80)

    # Run the patient intake demo
    demo = PatientIntakeDemo()

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(
                "❌ SIVA server not running. Please start with: python run_voice_app.py"
            )
            exit(1)
    except:
        print(
            "❌ Cannot connect to SIVA server. Please start with: python run_voice_app.py"
        )
        exit(1)

    print("✅ Connected to SIVA server")
    print()

    # Ask if user wants to reset system
    reset = input("Reset system to start fresh? (y/n): ").lower().strip()
    if reset == "y":
        if not demo.clear_system():
            print("❌ Failed to reset system. Continuing anyway...")
        print()

    # Run the patient intake demo
    demo.run_learning_progression_demo()

    # Demonstrate learning phases
    demo.demonstrate_learning_phases()

    print(f"\n🌐 Visit http://localhost:8000/dashboard to see detailed metrics!")
    print("The dashboard shows:")
    print("• Learning curve over time")
    print("• Escalation precision metrics")
    print("• Vector store contents")
    print("• Real-time performance tracking")
