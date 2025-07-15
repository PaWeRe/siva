#!/usr/bin/env python3
"""Learning progression demo - shows how SIVA improves with challenging scenarios."""

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"


def clear_system():
    """Reset the system to start fresh."""
    try:
        response = requests.post(f"{BASE_URL}/dashboard/reset")
        if response.status_code == 200:
            print("✅ System reset successfully")
        else:
            print(f"❌ Reset failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Reset error: {e}")


def simulate_conversation(session_id, messages, expected_route):
    """Simulate a complete conversation with routing decision."""

    # Send each message in the conversation
    for i, message in enumerate(messages):
        payload = {"session_id": session_id, "message": message}
        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload)
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
                    break

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None, False

    return None, False


def provide_human_feedback(session_id, agent_prediction, correct_route):
    """Provide human expert feedback."""
    feedback_payload = {
        "session_id": session_id,
        "agent_prediction": agent_prediction,
        "human_label": correct_route,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/escalation/feedback", json=feedback_payload
        )
        if response.status_code == 200:
            result = response.json()
            is_correct = agent_prediction == correct_route
            outcome = "✅ Correct" if is_correct else "❌ Wrong"
            print(
                f"  👨‍⚕️ Human feedback: {agent_prediction} → {correct_route} {outcome}"
            )
            return result.get("training_added", False)
        else:
            print(f"  ❌ Feedback failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Feedback error: {e}")
        return False


def get_system_stats():
    """Get current system statistics."""
    try:
        response = requests.get(f"{BASE_URL}/dashboard/metrics")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Stats error: {e}")
    return {}


def run_challenging_scenarios():
    """Run scenarios that demonstrate learning progression."""

    print("🎬 CHALLENGING SCENARIOS DEMO")
    print("=" * 50)
    print("This demo shows how SIVA learns from difficult cases")
    print()

    # Define challenging scenarios
    scenarios = [
        {
            "name": "Atypical Heart Attack (Female)",
            "description": "Subtle symptoms that could be missed",
            "messages": [
                "Hi, I'm here for my appointment",
                "I'm Sarah Johnson, born March 15, 1965",
                "I take atorvastatin for cholesterol",
                "No known allergies",
                "I have high cholesterol and diabetes",
                "I've been feeling very tired and nauseous for the past 2 days",
                "The fatigue is severe, 7 out of 10, came on gradually over 2 days. I also have jaw pain and indigestion, especially when I walk upstairs",
            ],
            "expected_route": "emergency",
            "difficulty": "High - atypical presentation",
        },
        {
            "name": "Pediatric Fever Assessment",
            "description": "High fever in young child requiring immediate attention",
            "messages": [
                "Hello, I'm here with my 18-month-old daughter",
                "I'm Lisa Chen, the mother",
                "My birthday is August 10, 1988",
                "My daughter doesn't take any medications",
                "She has no known allergies",
                "No medical conditions",
                "She's had a fever for 6 hours and seems very lethargic",
                "Her fever is 104°F, she's been crying inconsolably, has a stiff neck, and is barely responsive",
            ],
            "expected_route": "emergency",
            "difficulty": "High - pediatric emergency signs",
        },
        {
            "name": "Mental Health Crisis",
            "description": "Psychiatric emergency requiring immediate intervention",
            "messages": [
                "I need help, I've been having dark thoughts",
                "My name is Michael Torres",
                "Born December 22, 1992",
                "I take sertraline 100mg daily",
                "No allergies",
                "I have depression and anxiety",
                "I've been having thoughts of hurting myself for the past week",
                "The thoughts are constant, 9 out of 10 intensity, getting worse daily. I have a plan and I don't think I can stay safe",
            ],
            "expected_route": "emergency",
            "difficulty": "High - suicide risk assessment",
        },
        {
            "name": "Stroke Mimicker",
            "description": "Symptoms that could be stroke but are actually migraine",
            "messages": [
                "I'm having trouble speaking clearly",
                "Robert Kim, age 45",
                "January 5, 1979",
                "I take sumatriptan as needed for migraines",
                "Allergic to aspirin",
                "I have chronic migraines",
                "I have slurred speech and numbness on my right side",
                "This started 30 minutes ago, 6 out of 10 severity, but I recognize this pattern from my severe migraines. The numbness always starts on one side",
            ],
            "expected_route": "urgent",
            "difficulty": "Medium - requires careful stroke vs migraine differentiation",
        },
        {
            "name": "Medication Overdose",
            "description": "Accidental overdose requiring immediate care",
            "messages": [
                "I think I took too much of my medication by mistake",
                "Mary Williams, age 78",
                "June 3, 1946",
                "I take warfarin, digoxin, and metoprolol",
                "No allergies",
                "I have atrial fibrillation and heart failure",
                "I accidentally took my evening medications twice",
                "I took double doses 2 hours ago, feeling dizzy and weak, heart rate feels very slow, about to faint",
            ],
            "expected_route": "emergency",
            "difficulty": "High - drug toxicity",
        },
    ]

    print("📊 Starting with empty vector store...")
    initial_stats = get_system_stats()
    print(
        f"Vector store size: {initial_stats.get('vector_conversations', []).__len__()}"
    )
    print()

    # Run scenarios and track learning
    correct_predictions = 0
    total_scenarios = len(scenarios)

    for i, scenario in enumerate(scenarios, 1):
        print(f"🎯 SCENARIO {i}/{total_scenarios}: {scenario['name']}")
        print(f"📝 {scenario['description']}")
        print(f"🔥 Difficulty: {scenario['difficulty']}")
        print()

        # Generate unique session ID
        session_id = f"demo_challenging_{i}_{uuid.uuid4().hex[:8]}"

        # Run the conversation
        agent_prediction, was_escalated = simulate_conversation(
            session_id, scenario["messages"], scenario["expected_route"]
        )

        if was_escalated and agent_prediction:
            # Provide human feedback
            training_added = provide_human_feedback(
                session_id, agent_prediction, scenario["expected_route"]
            )

            # Track accuracy
            if agent_prediction == scenario["expected_route"]:
                correct_predictions += 1
                print(f"  ✅ Agent got it right!")
            else:
                print(
                    f"  📚 Agent learned: {agent_prediction} → {scenario['expected_route']}"
                )

            if training_added:
                print(f"  💾 Added to training data")
        else:
            print(f"  ⚠️  No escalation occurred")

        # Show current learning progress
        current_stats = get_system_stats()
        vector_size = len(current_stats.get("vector_conversations", []))
        accuracy = (correct_predictions / i) * 100

        print(
            f"  📈 Progress: Vector store size: {vector_size}, Accuracy: {accuracy:.1f}%"
        )
        print()

        # Brief pause between scenarios
        time.sleep(1)

    # Final results
    print("🏁 DEMO COMPLETE!")
    print("=" * 50)
    final_stats = get_system_stats()
    final_accuracy = (correct_predictions / total_scenarios) * 100

    print(f"📊 Final Results:")
    print(f"   • Scenarios processed: {total_scenarios}")
    print(f"   • Agent accuracy: {final_accuracy:.1f}%")
    print(f"   • Vector store size: {len(final_stats.get('vector_conversations', []))}")
    print(f"   • Total escalations: {final_stats.get('total_escalations', 0)}")
    print(f"   • Learning examples: {len(final_stats.get('vector_conversations', []))}")

    # Show what the agent learned
    print(f"\n🧠 Knowledge Acquired:")
    for conv in final_stats.get("vector_conversations", []):
        route = conv.get("correct_route", "unknown")
        symptoms = conv.get("symptoms_summary", "No description")[:80]
        print(f"   • {route.upper()}: {symptoms}...")

    print(f"\n🎉 The agent is now better prepared for similar challenging cases!")
    return final_stats


def test_learned_knowledge():
    """Test if the agent can now handle similar cases better."""
    print("\n🧪 TESTING LEARNED KNOWLEDGE")
    print("=" * 40)
    print("Testing with a similar case to see if learning worked...")

    # Test with a similar atypical heart attack case
    test_messages = [
        "Hello, I need to see a doctor",
        "I'm Janet Murphy, age 58",
        "Born February 14, 1966",
        "I take metformin for diabetes",
        "No allergies",
        "I have diabetes and high blood pressure",
        "I've been having upper back pain and nausea since this morning",
        "The pain is 6 out of 10, started 4 hours ago, radiating to my jaw, with shortness of breath and sweating",
    ]

    session_id = f"test_learned_{uuid.uuid4().hex[:8]}"
    agent_prediction, was_escalated = simulate_conversation(
        session_id, test_messages, "emergency"
    )

    if was_escalated:
        print(f"🤔 Agent predicted: {agent_prediction}")
        if agent_prediction == "emergency":
            print(
                "✅ SUCCESS! Agent correctly identified another atypical heart attack"
            )
        else:
            print(
                f"📚 Still learning: predicted {agent_prediction} instead of emergency"
            )
    else:
        print("ℹ️  Agent was confident enough to route directly (good sign!)")


if __name__ == "__main__":
    print("🧠 SIVA LEARNING PROGRESSION DEMO")
    print("=" * 60)
    print("This demo shows how SIVA improves with challenging medical scenarios")
    print("The agent will initially struggle but learn from human expert feedback")
    print()

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
        clear_system()
        print()

    # Run the demo
    final_stats = run_challenging_scenarios()

    # Test learned knowledge
    test_learned_knowledge()

    print(f"\n🎯 Visit http://localhost:8000/dashboard to see detailed metrics!")
    print("The dashboard shows:")
    print("• Learning curve over time")
    print("• Escalation precision metrics")
    print("• Vector store contents")
    print("• Real-time performance tracking")
