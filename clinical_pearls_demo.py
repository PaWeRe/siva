#!/usr/bin/env python3
"""
Clinical Pearls Demo - Experience-Based Medical Decision Support

This demo showcases the dual-use of the SIVA vector database for clinical decision support.
Scenario: Physician on airplane helping patient with rash, using both medical literature
and experience-based evidence to make decisions about emergency landing.

The demo shows:
1. Initial case with no experience - relies on medical literature
2. Similar case with experience - combines literature + clinical experience
3. Experience capture and validation process
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

BASE_URL = "http://localhost:8000"


class MedicalDecision(Enum):
    EMERGENCY_LANDING = "emergency_landing"
    CONTINUE_FLIGHT = "continue_flight"
    MONITOR_CLOSELY = "monitor_closely"
    IMMEDIATE_INTERVENTION = "immediate_intervention"


@dataclass
class ClinicalCase:
    name: str
    description: str
    patient_info: Dict[str, Any]
    symptoms: Dict[str, Any]
    medical_context: Dict[str, Any]
    expected_decision: MedicalDecision
    reasoning: str
    learning_stage: str  # "initial", "learning", "experienced"
    experience_available: bool


class ClinicalPearlsDemo:
    """Clinical pearls demo focusing on experience-based medical decision support."""

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

    def simulate_clinical_conversation(
        self, case: ClinicalCase
    ) -> tuple[Optional[str], bool]:
        """Simulate a clinical decision conversation."""

        print(f"  🎯 Starting clinical case: {case.name}")

        # Create conversation messages based on case
        messages = self._create_clinical_messages(case)

        # Generate unique session ID
        session_id = f"clinical_pearls_{case.learning_stage}_{self.cases_processed}_{uuid.uuid4().hex[:8]}"

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
                        print(f"  ✅ Clinical decision made")
                        break

            except Exception as e:
                print(f"  ❌ Error: {e}")
                return None, False

        return None, False

    def _create_clinical_messages(self, case: ClinicalCase) -> List[str]:
        """Create conversation messages for clinical case."""
        messages = []

        # Initial physician introduction
        messages.append(
            f"I'm Dr. {case.name.split()[0]}, a physician on flight {case.medical_context.get('flight_number', 'AA123')}"
        )

        # Patient presentation
        messages.append(
            f"We have a {case.patient_info['age']}-year-old {case.patient_info['gender']} passenger with {case.symptoms['primary_symptom']}"
        )

        # Medical history
        if case.patient_info.get("medical_conditions"):
            conditions = ", ".join(case.patient_info["medical_conditions"])
            messages.append(f"Patient has {conditions}")

        # Medications
        if case.patient_info.get("medications"):
            meds = ", ".join(
                [
                    f"{med['name']} for {med['indication']}"
                    for med in case.patient_info["medications"]
                ]
            )
            messages.append(f"Patient takes {meds}")

        # Symptom details
        messages.append(
            f"The {case.symptoms['primary_symptom']} appeared {case.symptoms['onset']} ago"
        )
        messages.append(
            f"Symptoms include: {', '.join(case.symptoms['associated_symptoms'])}"
        )

        # Severity assessment
        messages.append(
            f"Severity is {case.symptoms['severity']}/10, {case.symptoms['severity_description']}"
        )

        # Clinical question
        messages.append(
            f"Need to determine if {case.medical_context['decision_point']}"
        )

        return messages

    def provide_clinical_feedback(
        self,
        session_id: str,
        agent_prediction: str,
        correct_decision: MedicalDecision,
        case: ClinicalCase,
    ) -> bool:
        """Provide clinical expert feedback."""
        feedback_payload = {
            "session_id": session_id,
            "agent_prediction": agent_prediction,
            "human_label": correct_decision.value,
        }

        try:
            response = requests.post(
                f"{self.base_url}/escalation/feedback", json=feedback_payload
            )
            if response.status_code == 200:
                result = response.json()
                is_correct = agent_prediction == correct_decision.value
                outcome = "✅ Correct" if is_correct else "❌ Wrong"
                print(
                    f"  👨‍⚕️ Clinical feedback: {agent_prediction} → {correct_decision.value} {outcome}"
                )

                # Add clinical pearl extraction if this is a learning case
                if case.experience_available:
                    self._extract_clinical_pearl(
                        case, correct_decision, agent_prediction
                    )

                return result.get("training_added", False)
            else:
                print(f"  ❌ Feedback failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Feedback error: {e}")
            return False

    def _extract_clinical_pearl(
        self,
        case: ClinicalCase,
        correct_decision: MedicalDecision,
        agent_prediction: str,
    ):
        """Extract clinical pearl from the case."""
        print(f"  💎 Extracting clinical pearl...")

        pearl_data = {
            "case_type": case.symptoms["primary_symptom"],
            "patient_population": f"{case.patient_info['age']}-year-old {case.patient_info['gender']}",
            "medical_context": case.medical_context["decision_point"],
            "correct_decision": correct_decision.value,
            "agent_prediction": agent_prediction,
            "key_factors": case.symptoms["associated_symptoms"],
            "learning_point": case.reasoning,
            "experience_level": case.learning_stage,
        }

        print(
            f"  📝 Clinical Pearl: {case.symptoms['primary_symptom']} in {case.patient_info['age']}-year-old → {correct_decision.value}"
        )
        print(f"  💡 Key Learning: {case.reasoning[:100]}...")

    def run_airplane_clinical_demo(self):
        """Run the airplane clinical pearls demo."""
        print("\n✈️ AIRPLANE CLINICAL PEARLS DEMO")
        print("=" * 70)
        print("Scenario: Physician on airplane helping patient with rash")
        print("Demonstrating dual-use of vector database for medical decision support")
        print("Combining medical literature with clinical experience")
        print()

        # Define clinical cases
        cases = [
            ClinicalCase(
                name="Dr. Smith - Initial Chickenpox Case",
                description="First case of chickenpox-like rash in immunocompromised patient",
                patient_info={
                    "age": 65,
                    "gender": "male",
                    "medical_conditions": ["prostate cancer"],
                    "medications": [
                        {
                            "name": "leuprolide",
                            "indication": "androgen deprivation therapy",
                        }
                    ],
                    "immunocompromised": True,
                },
                symptoms={
                    "primary_symptom": "vesicular rash",
                    "onset": "2 hours",
                    "associated_symptoms": ["fever", "fatigue", "crusted lesions"],
                    "severity": 6,
                    "severity_description": "moderate, spreading rapidly",
                },
                medical_context={
                    "flight_number": "AA123",
                    "decision_point": "if emergency landing is required or can continue to destination",
                    "time_to_destination": "3 hours",
                },
                expected_decision=MedicalDecision.EMERGENCY_LANDING,
                reasoning="Immunocompromised patient with chickenpox-like rash requires immediate medical attention due to risk of complications",
                learning_stage="initial",
                experience_available=False,
            ),
            ClinicalCase(
                name="Dr. Johnson - Similar Case with Experience",
                description="Similar case where experience-based evidence is available",
                patient_info={
                    "age": 58,
                    "gender": "female",
                    "medical_conditions": ["breast cancer"],
                    "medications": [
                        {"name": "doxorubicin", "indication": "chemotherapy"}
                    ],
                    "immunocompromised": True,
                },
                symptoms={
                    "primary_symptom": "vesicular rash",
                    "onset": "3 hours",
                    "associated_symptoms": [
                        "fatigue",
                        "mild fever",
                        "no respiratory symptoms",
                    ],
                    "severity": 4,
                    "severity_description": "mild, stable",
                },
                medical_context={
                    "flight_number": "DL456",
                    "decision_point": "if this requires emergency landing or can continue",
                    "time_to_destination": "2 hours",
                },
                expected_decision=MedicalDecision.CONTINUE_FLIGHT,
                reasoning="Similar to previous case but patient is stable, no respiratory symptoms, and closer to destination",
                learning_stage="experienced",
                experience_available=True,
            ),
            ClinicalCase(
                name="Dr. Williams - Urticarial Rash Case",
                description="Different type of rash requiring different approach",
                patient_info={
                    "age": 45,
                    "gender": "male",
                    "medical_conditions": [],
                    "medications": [],
                    "immunocompromised": False,
                },
                symptoms={
                    "primary_symptom": "urticarial rash",
                    "onset": "1 hour",
                    "associated_symptoms": ["itching", "raised wheals"],
                    "severity": 5,
                    "severity_description": "moderate, spreading but no airway involvement",
                },
                medical_context={
                    "flight_number": "UA789",
                    "decision_point": "if this is allergic reaction requiring emergency landing",
                    "time_to_destination": "4 hours",
                },
                expected_decision=MedicalDecision.MONITOR_CLOSELY,
                reasoning="Allergic reaction without airway involvement can be monitored, but need to watch for progression",
                learning_stage="learning",
                experience_available=True,
            ),
            ClinicalCase(
                name="Dr. Rodriguez - Severe Allergic Reaction",
                description="Severe allergic reaction requiring immediate intervention",
                patient_info={
                    "age": 32,
                    "gender": "female",
                    "medical_conditions": ["asthma"],
                    "medications": [
                        {"name": "albuterol", "indication": "asthma rescue"}
                    ],
                    "immunocompromised": False,
                },
                symptoms={
                    "primary_symptom": "angioedema",
                    "onset": "30 minutes",
                    "associated_symptoms": [
                        "facial swelling",
                        "difficulty breathing",
                        "wheezing",
                    ],
                    "severity": 9,
                    "severity_description": "severe, airway compromise",
                },
                medical_context={
                    "flight_number": "BA101",
                    "decision_point": "if immediate emergency landing is required",
                    "time_to_destination": "5 hours",
                },
                expected_decision=MedicalDecision.IMMEDIATE_INTERVENTION,
                reasoning="Severe allergic reaction with airway compromise requires immediate medical intervention",
                learning_stage="experienced",
                experience_available=True,
            ),
        ]

        print("📊 Starting clinical pearls demo...")
        initial_stats = self.get_system_stats()
        print(
            f"Vector store size: {len(initial_stats.get('vector_conversations', []))}"
        )
        print()

        # Run cases and track learning
        correct_predictions = 0
        total_cases = len(cases)

        for i, case in enumerate(cases, 1):
            print(f"🎯 CLINICAL CASE {i}/{total_cases}: {case.name}")
            print(f"📝 {case.description}")
            print(
                f"👤 Patient: {case.patient_info['age']}-year-old {case.patient_info['gender']}"
            )
            print(f"🏥 Medical Context: {case.medical_context['decision_point']}")
            print(f"📚 Learning Stage: {case.learning_stage}")
            print(f"💡 Expected Decision: {case.expected_decision.value}")
            print()

            # Run the clinical conversation
            agent_prediction, was_escalated = self.simulate_clinical_conversation(case)

            if was_escalated and agent_prediction:
                # Provide clinical feedback
                training_added = self.provide_clinical_feedback(
                    session_id=f"clinical_{i}_{uuid.uuid4().hex[:8]}",
                    agent_prediction=agent_prediction,
                    correct_decision=case.expected_decision,
                    case=case,
                )

                # Track accuracy
                if agent_prediction == case.expected_decision.value:
                    correct_predictions += 1
                    print(f"  ✅ Agent made correct clinical decision!")
                else:
                    print(
                        f"  📚 Agent learned: {agent_prediction} → {case.expected_decision.value}"
                    )

                if training_added:
                    print(f"  💾 Added to clinical knowledge base")
            else:
                print(f"  ⚠️  No escalation occurred")

            # Show current learning progress
            current_stats = self.get_system_stats()
            vector_size = len(current_stats.get("vector_conversations", []))
            accuracy = (correct_predictions / i) * 100

            print(
                f"  📈 Progress: Vector store size: {vector_size}, Accuracy: {accuracy:.1f}%"
            )
            print()

            self.cases_processed += 1
            time.sleep(1)

        # Final results
        print("🏁 CLINICAL PEARLS DEMO COMPLETE!")
        print("=" * 50)
        final_stats = self.get_system_stats()
        final_accuracy = (correct_predictions / total_cases) * 100

        print(f"📊 Final Clinical Results:")
        print(f"   • Clinical cases processed: {total_cases}")
        print(f"   • Agent accuracy: {final_accuracy:.1f}%")
        print(
            f"   • Vector store size: {len(final_stats.get('vector_conversations', []))}"
        )
        print(f"   • Total escalations: {final_stats.get('total_escalations', 0)}")

        # Show what the agent learned
        print(f"\n🧠 Clinical Knowledge Acquired:")
        for conv in final_stats.get("vector_conversations", []):
            route = conv.get("correct_route", "unknown")
            symptoms = conv.get("symptoms_summary", "No description")[:80]
            print(f"   • {route.upper()}: {symptoms}...")

        print(f"\n💎 Key Clinical Pearls Demonstrated:")
        print(f"   ✅ Dual-Use Vector Store: Medical literature + clinical experience")
        print(f"   ✅ Experience-Based Learning: System improves with similar cases")
        print(f"   ✅ Clinical Decision Support: Combines evidence and experience")
        print(f"   ✅ Knowledge Capture: Extracts insights from clinical cases")
        print(f"   ✅ Confidence Assessment: Escalates when uncertain")

        return final_stats

    def demonstrate_experience_capture(self):
        """Demonstrate how clinical experience is captured and used."""
        print("\n💎 CLINICAL EXPERIENCE CAPTURE DEMONSTRATION")
        print("=" * 60)
        print("Showing how the system captures and validates clinical experience")
        print()

        # Simulate experience capture process
        experience_data = {
            "case_type": "vesicular_rash_immunocompromised",
            "clinical_pearl": "Immunocompromised patients with vesicular rash require immediate evaluation",
            "key_factors": [
                "immunocompromised_status",
                "rash_morphology",
                "symptom_severity",
            ],
            "decision_rule": "If immunocompromised + vesicular rash → emergency evaluation",
            "validation": "Supported by medical literature and clinical experience",
            "confidence": 0.85,
        }

        print("📝 Experience Capture Process:")
        print(f"   • Case Type: {experience_data['case_type']}")
        print(f"   • Clinical Pearl: {experience_data['clinical_pearl']}")
        print(f"   • Key Factors: {', '.join(experience_data['key_factors'])}")
        print(f"   • Decision Rule: {experience_data['decision_rule']}")
        print(f"   • Validation: {experience_data['validation']}")
        print(f"   • Confidence: {experience_data['confidence']}")

        print(f"\n🔄 Experience Integration:")
        print(f"   • Stored in vector database with medical literature")
        print(f"   • Available for future similar cases")
        print(f"   • Validated against domain knowledge")
        print(f"   • Continuously updated with new cases")

        print(f"\n🎯 Benefits of Experience-Based Evidence:")
        print(f"   • Faster decision making for similar cases")
        print(f"   • Reduced unnecessary escalations")
        print(f"   • Improved clinical confidence")
        print(f"   • Knowledge sharing across physicians")


def create_clinical_flowchart():
    """Create a flowchart showing the clinical pearls approach."""
    flowchart = """
    CLINICAL PEARLS EXPERIENCE-BASED EVIDENCE FLOWCHART
    ===================================================
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                    CLINICAL CASE PRESENTATION                  │
    │  • Patient symptoms and history                                │
    │  • Medical context (airplane scenario)                         │
    │  • Decision point (emergency landing?)                         │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                DUAL EVIDENCE RETRIEVAL                          │
    │                                                                 │
    │  ┌─────────────────────┐    ┌─────────────────────┐            │
    │  │  MEDICAL LITERATURE │    │ CLINICAL EXPERIENCE │            │
    │  │                     │    │                     │            │
    │  │ • OpenEvidence API  │    │ • Similar cases     │            │
    │  │ • Peer-reviewed     │    │ • Previous outcomes │            │
    │  │   studies           │    │ • Clinical pearls   │            │
    │  │ • Guidelines        │    │ • Decision patterns │            │
    │  │ • Drug interactions │    │ • Risk factors      │            │
    │  └─────────────────────┘    └─────────────────────┘            │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                EVIDENCE SYNTHESIS                               │
    │  • Combine literature + experience                              │
    │  • Weight by confidence and relevance                           │
    │  • Generate clinical recommendation                             │
    │  • Assess decision confidence                                   │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                CLINICAL DECISION                                │
    │                                                                 │
    │  ┌─────────────────────┐    ┌─────────────────────┐            │
    │  │   HIGH CONFIDENCE   │    │   LOW CONFIDENCE    │            │
    │  │                     │    │                     │            │
    │  │ • Make decision     │    │ • Escalate to human │            │
    │  │ • Provide reasoning │    │ • Request review    │            │
    │  │ • Document case     │    │ • Learn from expert │            │
    │  └─────────────────────┘    └─────────────────────┘            │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                EXPERIENCE CAPTURE                               │
    │  • Extract clinical pearl                                      │
    │  • Validate against literature                                 │
    │  • Store in vector database                                    │
    │  • Update decision patterns                                    │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                CONTINUOUS LEARNING                              │
    │  • Improve with each case                                      │
    │  • Share knowledge across physicians                           │
    │  • Reduce unnecessary escalations                              │
    │  • Enhance clinical confidence                                 │
    └─────────────────────────────────────────────────────────────────┘
    
    KEY FEATURES:
    • Dual Evidence: Combines medical literature with clinical experience
    • Experience Capture: Extracts insights from each case
    • Knowledge Sharing: Enables learning across physicians
    • Confidence Assessment: Only escalates when uncertain
    • Continuous Improvement: System gets better with each case
    """

    return flowchart


if __name__ == "__main__":
    # Print the clinical flowchart
    print(create_clinical_flowchart())
    print("\n" + "=" * 80)

    # Run the clinical pearls demo
    demo = ClinicalPearlsDemo()

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

    # Run the clinical pearls demo
    demo.run_airplane_clinical_demo()

    # Demonstrate experience capture
    demo.demonstrate_experience_capture()

    print(f"\n🌐 Visit http://localhost:8000/dashboard to see detailed metrics!")
    print("The dashboard shows:")
    print("• Clinical decision accuracy")
    print("• Experience-based learning curve")
    print("• Vector store contents")
    print("• Escalation patterns")
