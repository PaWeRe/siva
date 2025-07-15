#!/usr/bin/env python3
"""Debug script to test enhanced conversation logic with routing and escalation."""

import requests
import json
import uuid
import time


def test_conversation():
    """Test the enhanced conversation flow with routing and escalation."""
    base_url = "http://localhost:8000"
    session_id = str(uuid.uuid4())

    print(f"🔍 Testing enhanced SIVA conversation with session: {session_id}")
    print("=" * 60)

    # Test backend connection
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Backend connection: {response.status_code}")

        # Check vector store stats
        stats_response = requests.get(f"{base_url}/vector_store/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"📊 Vector store: {stats['total_conversations']} conversations")
            if stats["routes"]:
                print(f"   Routes: {stats['routes']}")

    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return

    def send_message(message, step_name):
        """Send a message and print the detailed response."""
        print(f"\n📤 [{step_name}] Sending: '{message}'")
        payload = {"session_id": session_id, "message": message}

        try:
            response = requests.post(f"{base_url}/chat", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"📥 Agent reply: {result['reply']}")
                print(f"🏁 End call: {result['end_call']}")

                # Show current data collected
                data = result.get("data", {})
                if data:
                    print(f"📋 Collected data:")
                    for key, value in data.items():
                        if key != "detailed_symptoms":
                            print(f"   {key}: {value}")
                        else:
                            print(
                                f"   detailed_symptoms: {len(value) if value else 0} symptoms"
                            )

                # Check for escalation
                if "escalation" in result:
                    print(f"🚨 ESCALATION TRIGGERED!")
                    escalation = result["escalation"]
                    print(
                        f"   Agent prediction: {escalation.get('agent_prediction', 'unknown')}"
                    )
                    print(
                        f"   Reasoning: {escalation.get('reasoning', 'No reasoning')}"
                    )
                    return result, escalation

                return result, None
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None, None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None, None

    def simulate_human_feedback(escalation_data, correct_route):
        """Simulate human expert providing feedback on escalated case."""
        print(f"\n👨‍⚕️ Simulating human expert feedback...")
        print(f"   Agent predicted: {escalation_data.get('agent_prediction')}")
        print(f"   Human corrects to: {correct_route}")

        feedback_payload = {
            "session_id": session_id,
            "agent_prediction": escalation_data.get("agent_prediction", "unknown"),
            "human_label": correct_route,
        }

        try:
            response = requests.post(
                f"{base_url}/escalation/feedback", json=feedback_payload
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Feedback processed: {result.get('message')}")
                print(f"📚 Training added: {result.get('training_added')}")
                return result
            else:
                print(f"❌ Feedback error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Feedback failed: {e}")
            return None

    # Test Scenario 1: Basic checkup (should escalate due to empty vector store)
    print(f"\n🎬 SCENARIO 1: Annual checkup (low-risk case)")
    print("=" * 40)

    basic_steps = [
        ("Initial greeting", "Hello, I'm here for my appointment."),
        ("Provide name", "My name is John Smith."),
        ("Provide birthday", "My birthday is January 15, 1990."),
        (
            "Provide prescriptions",
            "I take Lisinopril 10mg daily for my blood pressure.",
        ),
        ("Provide allergies", "I'm allergic to penicillin."),
        ("Provide conditions", "I have mild high blood pressure."),
        (
            "Provide visit reason",
            "I'm here for my annual checkup and to review my blood pressure medication.",
        ),
    ]

    escalation_data = None
    for step_name, message in basic_steps:
        result, escalation = send_message(message, step_name)
        if not result:
            break

        if escalation:
            escalation_data = escalation
            break

        if result.get("end_call", False):
            print(f"\n🎉 Call ended after: {step_name}")
            break

        time.sleep(0.5)  # Brief pause for readability

    # If basic intake complete, continue to symptoms
    if not escalation_data and result and not result.get("end_call"):
        print(f"\n🩺 Moving to detailed symptom collection...")

        symptom_steps = [
            (
                "Describe symptoms",
                "I've been feeling generally healthy, just want to make sure my blood pressure is under control. No specific symptoms.",
            ),
            (
                "Symptom details",
                "I occasionally feel a mild headache, maybe 3 out of 10 severity, lasting a few hours, usually when I forget my medication.",
            ),
        ]

        for step_name, message in symptom_steps:
            result, escalation = send_message(message, step_name)
            if escalation:
                escalation_data = escalation
                break
            if result and result.get("end_call", False):
                break
            time.sleep(0.5)

    # Handle escalation and provide human feedback
    if escalation_data:
        # Simulate human expert saying this should be "routine" care
        feedback_result = simulate_human_feedback(escalation_data, "routine")

        # Check updated vector store stats
        print(f"\n📊 Checking vector store after feedback...")
        try:
            stats_response = requests.get(f"{base_url}/vector_store/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"   Total conversations: {stats['total_conversations']}")
                print(f"   Routes: {stats.get('routes', {})}")
        except Exception as e:
            print(f"❌ Stats check failed: {e}")


def test_emergency_scenario():
    """Test an emergency scenario that should be routed correctly."""
    base_url = "http://localhost:8000"
    session_id = str(uuid.uuid4())

    print(f"\n🚨 EMERGENCY SCENARIO TEST")
    print("=" * 40)
    print(f"Session: {session_id}")

    def send_message(message, step_name):
        payload = {"session_id": session_id, "message": message}
        try:
            response = requests.post(f"{base_url}/chat", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"📤 [{step_name}]: {message}")
                print(f"📥 Agent: {result['reply']}")
                return result
        except Exception as e:
            print(f"❌ Error: {e}")
        return None

    # Emergency case - chest pain
    emergency_steps = [
        ("Greeting", "Help! I'm having chest pain!"),
        ("Name", "My name is Sarah Johnson."),
        ("Birthday", "March 3, 1985."),
        ("Prescriptions", "I don't take any regular medications."),
        ("Allergies", "No known allergies."),
        ("Conditions", "No medical conditions."),
        ("Visit reason", "I'm having severe chest pain that started an hour ago."),
        (
            "Symptoms",
            "Sharp chest pain, 9 out of 10 severity, started suddenly, radiating to my left arm, with shortness of breath and sweating.",
        ),
    ]

    for step_name, message in emergency_steps:
        result = send_message(message, step_name)
        if not result:
            break

        if "escalation" in result:
            print(f"🚨 ESCALATED: {result['escalation'].get('agent_prediction')}")
            # Human would confirm this is emergency
            simulate_emergency_feedback(session_id, result["escalation"])
            break

        if result.get("end_call", False):
            break

        time.sleep(0.3)


def simulate_emergency_feedback(session_id, escalation_data):
    """Simulate human confirming emergency case."""
    base_url = "http://localhost:8000"
    feedback_payload = {
        "session_id": session_id,
        "agent_prediction": escalation_data.get("agent_prediction", "unknown"),
        "human_label": "emergency",
    }

    try:
        response = requests.post(
            f"{base_url}/escalation/feedback", json=feedback_payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Emergency case confirmed by human expert")
    except Exception as e:
        print(f"❌ Emergency feedback failed: {e}")


def check_system_performance():
    """Check overall system performance and vector store status."""
    base_url = "http://localhost:8000"

    print(f"\n📈 SYSTEM PERFORMANCE CHECK")
    print("=" * 40)

    try:
        # Vector store stats
        stats_response = requests.get(f"{base_url}/vector_store/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"📊 Vector Store:")
            print(f"   Total conversations: {stats['total_conversations']}")
            print(f"   Routes distribution: {stats.get('routes', {})}")

        # System performance
        perf_response = requests.get(f"{base_url}/system/performance")
        if perf_response.status_code == 200:
            perf = perf_response.json()
            performance = perf.get("performance", {})
            print(f"\n🎯 System Performance:")
            print(f"   Total cases evaluated: {performance.get('total_cases', 0)}")
            print(f"   Accuracy: {performance.get('accuracy', 0):.2%}")

            suggestions = perf.get("improvement_suggestions", [])
            if suggestions:
                print(f"\n💡 Improvement Suggestions:")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")

    except Exception as e:
        print(f"❌ Performance check failed: {e}")


if __name__ == "__main__":
    print("🎮 SIVA Debug Test Suite")
    print("Make sure the server is running with: python run_voice_app.py")
    print("=" * 60)

    # Wait a moment for server to be ready
    time.sleep(1)

    # Run tests
    test_conversation()
    test_emergency_scenario()
    check_system_performance()

    print(f"\n🏁 Debug testing complete!")
    print("Key things tested:")
    print("✅ 3-phase conversation flow (intake → symptoms → routing)")
    print("✅ Escalation when vector store has insufficient data")
    print("✅ Human feedback simulation")
    print("✅ Vector store learning and updates")
    print("✅ Emergency scenario handling")
    print("✅ System performance monitoring")
