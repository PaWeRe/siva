#!/usr/bin/env python3
"""
Test script for unified SIVA infrastructure.
Tests mode switching and evidence display functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_mode_switching():
    """Test switching between patient intake and clinical pearls modes."""
    print("🧪 Testing Mode Switching...")

    # Test getting current mode
    response = requests.get(f"{BASE_URL}/mode/current")
    if response.status_code == 200:
        current_mode = response.json()["mode"]
        print(f"✅ Current mode: {current_mode}")
    else:
        print(f"❌ Failed to get current mode: {response.status_code}")
        return False

    # Test switching to clinical pearls
    response = requests.post(
        f"{BASE_URL}/mode/switch", json={"mode": "clinical_pearls"}
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Switched to: {result['mode']}")
    else:
        print(f"❌ Failed to switch mode: {response.status_code}")
        return False

    # Test switching back to patient intake
    response = requests.post(f"{BASE_URL}/mode/switch", json={"mode": "patient_intake"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Switched to: {result['mode']}")
    else:
        print(f"❌ Failed to switch mode: {response.status_code}")
        return False

    return True


def test_evidence_endpoint():
    """Test the evidence endpoint with a mock session."""
    print("\n🧪 Testing Evidence Endpoint...")

    # Create a mock session by sending a chat message
    session_id = "test_session_123"
    chat_response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "I have chest pain and shortness of breath",
        },
    )

    if chat_response.status_code == 200:
        print("✅ Created test session")
    else:
        print(f"❌ Failed to create test session: {chat_response.status_code}")
        return False

    # Test evidence endpoint
    evidence_response = requests.get(f"{BASE_URL}/evidence/{session_id}")
    if evidence_response.status_code == 200:
        evidence_data = evidence_response.json()
        print(f"✅ Evidence endpoint working")
        print(f"   Mode: {evidence_data['mode']}")
        print(f"   Evidence keys: {list(evidence_data['evidence'].keys())}")

        # Display some evidence details
        evidence = evidence_data["evidence"]
        if "similar_cases" in evidence:
            print(f"   Similar cases found: {len(evidence['similar_cases'])}")
        if "medical_literature" in evidence:
            print(f"   Literature items: {len(evidence['medical_literature'])}")
        if "confidence" in evidence:
            print(f"   Confidence: {evidence['confidence']:.2f}")

    else:
        print(f"❌ Failed to get evidence: {evidence_response.status_code}")
        return False

    return True


def test_clinical_pearls_mode():
    """Test clinical pearls mode specifically."""
    print("\n🧪 Testing Clinical Pearls Mode...")

    # Switch to clinical pearls mode
    requests.post(f"{BASE_URL}/mode/switch", json={"mode": "clinical_pearls"})

    # Create a clinical pearls session
    session_id = "clinical_test_456"
    chat_response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": session_id,
            "message": "Patient presents with atypical chest pain, considering emergency landing",
        },
    )

    if chat_response.status_code == 200:
        print("✅ Created clinical pearls session")
    else:
        print(
            f"❌ Failed to create clinical pearls session: {chat_response.status_code}"
        )
        return False

    # Test evidence in clinical pearls mode
    evidence_response = requests.get(f"{BASE_URL}/evidence/{session_id}")
    if evidence_response.status_code == 200:
        evidence_data = evidence_response.json()
        print(f"✅ Clinical pearls evidence working")
        print(f"   Mode: {evidence_data['mode']}")

        evidence = evidence_data["evidence"]
        if "similar_pearls" in evidence:
            print(f"   Similar pearls found: {len(evidence['similar_pearls'])}")
        if "medical_literature" in evidence:
            print(f"   Literature items: {len(evidence['medical_literature'])}")

    else:
        print(
            f"❌ Failed to get clinical pearls evidence: {evidence_response.status_code}"
        )
        return False

    return True


def main():
    """Run all tests."""
    print("🚀 Testing Unified SIVA Infrastructure")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
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

    # Run tests
    tests = [test_mode_switching, test_evidence_endpoint, test_clinical_pearls_mode]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error: {test.__name__} - {e}")

    print(f"\n🏁 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Unified infrastructure is working.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")


if __name__ == "__main__":
    main()
