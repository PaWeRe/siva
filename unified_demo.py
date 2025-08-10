#!/usr/bin/env python3
"""
Unified SIVA Demo System

This demo showcases two main scenarios:
1. Patient Intake Learning Progression - Shows how the system learns from similar cases
2. Clinical Pearls Experience-Based Evidence - Shows dual-use of vector database for medical decision support

The system demonstrates the unified framework approach where both applications share
the same underlying infrastructure but serve different purposes.
"""

import requests
import json
import time
import uuid
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

BASE_URL = "http://localhost:8000"


class DemoType(Enum):
    PATIENT_INTAKE = "patient_intake"
    CLINICAL_PEARLS = "clinical_pearls"


@dataclass
class DemoScenario:
    name: str
    description: str
    demo_type: DemoType
    messages: List[str]
    expected_outcome: str
    difficulty: str
    learning_stage: str  # "initial", "learning", "experienced"


class UnifiedDemoSystem:
    """Unified demo system for both patient intake and clinical pearls scenarios."""

    def __init__(self):
        self.base_url = BASE_URL
        self.session_counter = 0

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

    def simulate_conversation(
        self,
        session_id: str,
        messages: List[str],
        expected_outcome: str,
        demo_type: DemoType,
    ) -> tuple[Optional[str], bool]:
        """Simulate a complete conversation with routing decision."""

        print(f"  🎯 Starting {demo_type.value} conversation...")

        # Send each message in the conversation
        for i, message in enumerate(messages):
            payload = {"session_id": session_id, "message": message}
            try:
                response = requests.post(f"{self.base_url}/chat", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    print(f"  📤 Step {i+1}: {message[:50]}...")
                    print(f"  📥 Agent: {result['reply'][:100]}...")

                    # Check if escalated
                    if "escalation" in result:
                        agent_prediction = result["escalation"]["agent_prediction"]
                        print(f"  🚨 ESCALATED: Agent predicted '{agent_prediction}'")
                        return agent_prediction, True

                    if result.get("end_call", False):
                        print(f"  ✅ Call ended normally")
                        break

            except Exception as e:
                print(f"  ❌ Error: {e}")
                return None, False

        return None, False

    def provide_human_feedback(
        self, session_id: str, agent_prediction: str, correct_outcome: str
    ) -> bool:
        """Provide human expert feedback."""
        feedback_payload = {
            "session_id": session_id,
            "agent_prediction": agent_prediction,
            "human_label": correct_outcome,
        }

        try:
            response = requests.post(
                f"{self.base_url}/escalation/feedback", json=feedback_payload
            )
            if response.status_code == 200:
                result = response.json()
                is_correct = agent_prediction == correct_outcome
                outcome = "✅ Correct" if is_correct else "❌ Wrong"
                print(
                    f"  👨‍⚕️ Human feedback: {agent_prediction} → {correct_outcome} {outcome}"
                )
                return result.get("training_added", False)
            else:
                print(f"  ❌ Feedback failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Feedback error: {e}")
            return False

    def run_patient_intake_demo(self) -> Dict[str, Any]:
        """Run patient intake learning progression demo."""
        print("\n🏥 PATIENT INTAKE LEARNING PROGRESSION DEMO")
        print("=" * 60)
        print("This demo shows how SIVA learns from patient intake cases")
        print("The system starts with no experience and learns from human feedback")
        print()

        # Define patient intake scenarios in learning progression
        scenarios = [
            DemoScenario(
                name="Atypical Heart Attack (Female) - Initial",
                description="First case of atypical heart attack presentation",
                demo_type=DemoType.PATIENT_INTAKE,
                messages=[
                    "Hi, I'm here for my appointment",
                    "I'm Sarah Johnson, born March 15, 1965",
                    "I take atorvastatin for cholesterol",
                    "No known allergies",
                    "I have high cholesterol and diabetes",
                    "I've been feeling very tired and nauseous for the past 2 days",
                    "The fatigue is severe, 7 out of 10, came on gradually over 2 days. I also have jaw pain and indigestion, especially when I walk upstairs",
                ],
                expected_outcome="emergency",
                difficulty="High - atypical presentation",
                learning_stage="initial",
            ),
            DemoScenario(
                name="Similar Atypical Heart Attack - Learning",
                description="Similar case after learning from first example",
                demo_type=DemoType.PATIENT_INTAKE,
                messages=[
                    "Hello, I need to see a doctor",
                    "I'm Janet Murphy, age 58",
                    "Born February 14, 1966",
                    "I take metformin for diabetes",
                    "No allergies",
                    "I have diabetes and high blood pressure",
                    "I've been having upper back pain and nausea since this morning",
                    "The pain is 6 out of 10, started 4 hours ago, radiating to my jaw, with shortness of breath and sweating",
                ],
                expected_outcome="emergency",
                difficulty="Medium - now has learned examples",
                learning_stage="learning",
            ),
            DemoScenario(
                name="Another Atypical Heart Attack - Experienced",
                description="Third similar case showing improved confidence",
                demo_type=DemoType.PATIENT_INTAKE,
                messages=[
                    "Hi, I'm here for an appointment",
                    "I'm Maria Rodriguez, age 62",
                    "Born July 8, 1962",
                    "I take lisinopril for blood pressure",
                    "Allergic to penicillin",
                    "I have hypertension and arthritis",
                    "I've been having unusual fatigue and chest discomfort for the past day",
                    "The discomfort is 5 out of 10, feels like pressure, with some jaw pain and sweating",
                ],
                expected_outcome="emergency",
                difficulty="Low - system now confident",
                learning_stage="experienced",
            ),
            DemoScenario(
                name="Pediatric Fever Assessment",
                description="High fever in young child requiring immediate attention",
                demo_type=DemoType.PATIENT_INTAKE,
                messages=[
                    "Hello, I'm here with my 18-month-old daughter",
                    "I'm Lisa Chen, the mother",
                    "My birthday is August 10, 1988",
                    "My daughter doesn't take any medications",
                    "She has no known allergies",
                    "No medical conditions",
                    "She's had a fever for 6 hours and seems very lethargic",
                    "Her fever is 104°F, she's been crying inconsolably, has a stiff neck, and is barely responsive",
                ],
                expected_outcome="emergency",
                difficulty="High - pediatric emergency signs",
                learning_stage="initial",
            ),
            DemoScenario(
                name="Mental Health Crisis",
                description="Psychiatric emergency requiring immediate intervention",
                demo_type=DemoType.PATIENT_INTAKE,
                messages=[
                    "I need help, I've been having dark thoughts",
                    "My name is Michael Torres",
                    "Born December 22, 1992",
                    "I take sertraline 100mg daily",
                    "No allergies",
                    "I have depression and anxiety",
                    "I've been having thoughts of hurting myself for the past week",
                    "The thoughts are constant, 9 out of 10 intensity, getting worse daily. I have a plan and I don't think I can stay safe",
                ],
                expected_outcome="emergency",
                difficulty="High - suicide risk assessment",
                learning_stage="initial",
            ),
        ]

        print("📊 Starting with empty vector store...")
        initial_stats = self.get_system_stats()
        print(
            f"Vector store size: {len(initial_stats.get('vector_conversations', []))}"
        )
        print()

        # Run scenarios and track learning
        correct_predictions = 0
        total_scenarios = len(scenarios)

        for i, scenario in enumerate(scenarios, 1):
            print(f"🎯 SCENARIO {i}/{total_scenarios}: {scenario.name}")
            print(f"📝 {scenario.description}")
            print(f"🔥 Difficulty: {scenario.difficulty}")
            print(f"📚 Learning Stage: {scenario.learning_stage}")
            print()

            # Generate unique session ID
            session_id = (
                f"patient_intake_{scenario.learning_stage}_{i}_{uuid.uuid4().hex[:8]}"
            )

            # Run the conversation
            agent_prediction, was_escalated = self.simulate_conversation(
                session_id, scenario.messages, scenario.expected_outcome
            )

            if was_escalated and agent_prediction:
                # Provide human feedback
                training_added = self.provide_human_feedback(
                    session_id, agent_prediction, scenario.expected_outcome
                )

                # Track accuracy
                if agent_prediction == scenario.expected_outcome:
                    correct_predictions += 1
                    print(f"  ✅ Agent got it right!")
                else:
                    print(
                        f"  📚 Agent learned: {agent_prediction} → {scenario.expected_outcome}"
                    )

                if training_added:
                    print(f"  💾 Added to training data")
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

            # Brief pause between scenarios
            time.sleep(1)

        # Final results
        print("🏁 PATIENT INTAKE DEMO COMPLETE!")
        print("=" * 50)
        final_stats = self.get_system_stats()
        final_accuracy = (correct_predictions / total_scenarios) * 100

        print(f"📊 Final Results:")
        print(f"   • Scenarios processed: {total_scenarios}")
        print(f"   • Agent accuracy: {final_accuracy:.1f}%")
        print(
            f"   • Vector store size: {len(final_stats.get('vector_conversations', []))}"
        )
        print(f"   • Total escalations: {final_stats.get('total_escalations', 0)}")

        # Show what the agent learned
        print(f"\n🧠 Knowledge Acquired:")
        for conv in final_stats.get("vector_conversations", []):
            route = conv.get("correct_route", "unknown")
            symptoms = conv.get("symptoms_summary", "No description")[:80]
            print(f"   • {route.upper()}: {symptoms}...")

        return final_stats

    def run_clinical_pearls_demo(self) -> Dict[str, Any]:
        """Run clinical pearls experience-based evidence demo."""
        print("\n💎 CLINICAL PEARLS EXPERIENCE-BASED EVIDENCE DEMO")
        print("=" * 70)
        print(
            "This demo shows dual-use of vector database for medical decision support"
        )
        print("Scenario: Physician on airplane helping patient with rash")
        print()

        # Define clinical pearls scenarios
        scenarios = [
            DemoScenario(
                name="Initial Chickenpox Case - No Experience",
                description="First case of chickenpox-like rash in immunocompromised patient",
                demo_type=DemoType.CLINICAL_PEARLS,
                messages=[
                    "I'm Dr. Smith, a physician on flight AA123",
                    "We have a 65-year-old male passenger with a rash",
                    "Patient has prostate cancer and takes androgen deprivation therapy",
                    "The rash appeared 2 hours ago, starting on chest and spreading",
                    "Rash is vesicular, some lesions are crusted, patient reports mild fever",
                    "Patient is concerned about chickenpox and immunocompromised status",
                    "Need to determine if emergency landing is required or can continue to destination",
                ],
                expected_outcome="emergency_landing",
                difficulty="High - no previous experience",
                learning_stage="initial",
            ),
            DemoScenario(
                name="Similar Case After Experience - With Evidence",
                description="Similar case where experience-based evidence is available",
                demo_type=DemoType.CLINICAL_PEARLS,
                messages=[
                    "I'm Dr. Johnson, physician on flight DL456",
                    "We have a 58-year-old female with similar rash presentation",
                    "Patient has breast cancer, on chemotherapy, immunocompromised",
                    "Rash appeared 3 hours ago, vesicular lesions, some crusted",
                    "Patient reports fatigue and mild fever, no respiratory symptoms",
                    "Similar to previous case but different patient demographics",
                    "Need to assess if this requires emergency landing or can continue",
                ],
                expected_outcome="continue_flight",
                difficulty="Medium - has learned from previous case",
                learning_stage="experienced",
            ),
            DemoScenario(
                name="Different Rash Type - Learning New Pattern",
                description="New type of rash requiring different approach",
                demo_type=DemoType.CLINICAL_PEARLS,
                messages=[
                    "I'm Dr. Williams, physician on flight UA789",
                    "We have a 45-year-old male with urticarial rash",
                    "Patient has no known immunocompromising conditions",
                    "Rash appeared suddenly 1 hour ago, raised wheals, very itchy",
                    "Patient reports no fever, no other symptoms",
                    "Rash is spreading rapidly but no airway involvement",
                    "Need to determine if this is allergic reaction requiring emergency landing",
                ],
                expected_outcome="continue_flight",
                difficulty="Medium - new pattern but less complex",
                learning_stage="learning",
            ),
        ]

        print("📊 Starting clinical pearls demo...")
        initial_stats = self.get_system_stats()
        print(
            f"Vector store size: {len(initial_stats.get('vector_conversations', []))}"
        )
        print()

        # Run scenarios and track learning
        correct_predictions = 0
        total_scenarios = len(scenarios)

        for i, scenario in enumerate(scenarios, 1):
            print(f"🎯 CLINICAL SCENARIO {i}/{total_scenarios}: {scenario.name}")
            print(f"📝 {scenario.description}")
            print(f"🔥 Difficulty: {scenario.difficulty}")
            print(f"📚 Learning Stage: {scenario.learning_stage}")
            print()

            # Generate unique session ID
            session_id = (
                f"clinical_pearls_{scenario.learning_stage}_{i}_{uuid.uuid4().hex[:8]}"
            )

            # Run the conversation
            agent_prediction, was_escalated = self.simulate_conversation(
                session_id, scenario.messages, scenario.expected_outcome
            )

            if was_escalated and agent_prediction:
                # Provide human feedback
                training_added = self.provide_human_feedback(
                    session_id, agent_prediction, scenario.expected_outcome
                )

                # Track accuracy
                if agent_prediction == scenario.expected_outcome:
                    correct_predictions += 1
                    print(f"  ✅ Agent got it right!")
                else:
                    print(
                        f"  📚 Agent learned: {agent_prediction} → {scenario.expected_outcome}"
                    )

                if training_added:
                    print(f"  💾 Added to training data")
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

            # Brief pause between scenarios
            time.sleep(1)

        # Final results
        print("🏁 CLINICAL PEARLS DEMO COMPLETE!")
        print("=" * 50)
        final_stats = self.get_system_stats()
        final_accuracy = (correct_predictions / total_scenarios) * 100

        print(f"📊 Final Results:")
        print(f"   • Clinical scenarios processed: {total_scenarios}")
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

        return final_stats

    def run_unified_demo(self):
        """Run the complete unified demo showing both scenarios."""
        print("🧠 SIVA UNIFIED FRAMEWORK DEMO")
        print("=" * 60)
        print("This demo showcases the unified SIVA framework approach")
        print(
            "Demonstrating both patient intake learning and clinical pearls experience"
        )
        print()

        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code != 200:
                print(
                    "❌ SIVA server not running. Please start with: python run_voice_app.py"
                )
                return
        except:
            print(
                "❌ Cannot connect to SIVA server. Please start with: python run_voice_app.py"
            )
            return

        print("✅ Connected to SIVA server")
        print()

        # Ask if user wants to reset system
        reset = input("Reset system to start fresh? (y/n): ").lower().strip()
        if reset == "y":
            if not self.clear_system():
                print("❌ Failed to reset system. Continuing anyway...")
            print()

        # Run patient intake demo
        print("🎬 Starting Patient Intake Learning Progression Demo...")
        patient_stats = self.run_patient_intake_demo()

        print("\n" + "=" * 80)
        print("🔄 TRANSITIONING TO CLINICAL PEARLS DEMO")
        print("=" * 80)
        print(
            "Now demonstrating dual-use of vector database for clinical decision support"
        )
        print("The same infrastructure serves different medical applications")
        print()

        # Run clinical pearls demo
        print("🎬 Starting Clinical Pearls Experience-Based Evidence Demo...")
        clinical_stats = self.run_clinical_pearls_demo()

        # Final unified summary
        print("\n" + "=" * 80)
        print("🏆 UNIFIED FRAMEWORK DEMO COMPLETE")
        print("=" * 80)

        total_vector_size = len(clinical_stats.get("vector_conversations", []))
        total_escalations = clinical_stats.get("total_escalations", 0)

        print(f"📊 Unified Framework Results:")
        print(f"   • Combined vector store size: {total_vector_size}")
        print(f"   • Total escalations: {total_escalations}")
        print(f"   • Framework successfully handled both use cases")

        print(f"\n🎯 Key Demonstrations:")
        print(
            f"   ✅ Patient Intake: Learning progression from no experience to confidence"
        )
        print(f"   ✅ Clinical Pearls: Experience-based evidence for medical decisions")
        print(
            f"   ✅ Unified Infrastructure: Same vector store serves multiple applications"
        )
        print(
            f"   ✅ Dual-Use Database: Both structured data and experience-based insights"
        )

        print(f"\n🌐 Visit http://localhost:8000/dashboard to see detailed metrics!")
        print("The dashboard shows:")
        print("• Learning curve over time")
        print("• Escalation precision metrics")
        print("• Vector store contents")
        print("• Real-time performance tracking")


def create_flowchart():
    """Create a flowchart showing the unified approach."""
    flowchart = """
    SIVA UNIFIED FRAMEWORK FLOWCHART
    ================================
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                    UNIFIED SIVA FRAMEWORK                      │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    VOICE INTERFACE                             │
    │  • Speech-to-Text (Whisper)                                    │
    │  • Text-to-Speech (Cartesia)                                   │
    │  • Intent Classification                                        │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                DUAL-PURPOSE VECTOR STORE                       │
    │  • Experience-Based Evidence                                   │
    │  • Similar Case Retrieval                                      │
    │  • Confidence Assessment                                       │
    │  • Learning from Human Feedback                                │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                DOMAIN KNOWLEDGE ADAPTER                        │
    │  • OpenEvidence API Integration                                │
    │  • Medical Literature Search                                   │
    │  • Evidence-Based Recommendations                              │
    │  • Validation Against Literature                               │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                  DECISION MAKING                               │
    │  • Combine Experience + Literature                             │
    │  • Confidence Assessment                                       │
    │  • Escalation Decision                                         │
    │  • Response Generation                                          │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                LEARNING PIPELINE                               │
    │  • Extract Insights from Feedback                              │
    │  • Validate Against Domain Knowledge                           │
    │  • Update Knowledge Base                                       │
    │  • Continuous Improvement                                      │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    APPLICATIONS                                 │
    │                                                                 │
    │  ┌─────────────────────┐    ┌─────────────────────┐            │
    │  │   PATIENT INTAKE    │    │  CLINICAL PEARLS    │            │
    │  │                     │    │                     │            │
    │  │ • Symptom Collection│    │ • Medical Decisions │            │
    │  │ • Care Routing      │    │ • Experience Sharing│            │
    │  │ • Escalation Logic  │    │ • Evidence Synthesis│            │
    │  │ • Learning from     │    │ • Knowledge Capture │            │
    │  │   Similar Cases     │    │ • Continuous        │            │
    │  │                     │    │   Learning          │            │
    │  └─────────────────────┘    └─────────────────────┘            │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    
    KEY FEATURES:
    • Unified Infrastructure: Both applications share the same core components
    • Dual-Use Vector Store: Stores both structured data and experience-based insights
    • Experience + Literature: Combines clinical experience with medical literature
    • Continuous Learning: Improves from human feedback and new cases
    • Confidence-Based Escalation: Only escalates when confidence is low
    • Voice-First Interface: Natural voice interaction for healthcare scenarios
    """

    return flowchart


if __name__ == "__main__":
    # Print the flowchart
    print(create_flowchart())
    print("\n" + "=" * 80)

    # Run the unified demo
    demo_system = UnifiedDemoSystem()
    demo_system.run_unified_demo()
