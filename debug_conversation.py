#!/usr/bin/env python3
"""Debug script to test conversation logic without voice components."""

import requests
import json
import uuid

def test_conversation():
    """Test the conversation flow step by step."""
    base_url = "http://localhost:8000"
    session_id = str(uuid.uuid4())
    
    print(f"🔍 Testing conversation with session: {session_id}")
    print("=" * 50)
    
    # Test backend connection
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Backend connection: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return
    
    def send_message(message, step_name):
        """Send a message and print the response."""
        print(f"\n📤 [{step_name}] Sending: '{message}'")
        payload = {"session_id": session_id, "message": message}
        
        try:
            response = requests.post(f"{base_url}/chat", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"📥 Agent reply: {result['reply']}")
                print(f"🏁 End call: {result['end_call']}")
                print(f"📊 Data: {json.dumps(result['data'], indent=2)}")
                return result
            else:
                print(f"❌ Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    # Test conversation flow
    steps = [
        ("Initial greeting", "Hello, I'm here for my appointment."),
        ("Provide name", "My name is John Smith."),
        ("Provide birthday", "My birthday is January 15, 1990."),
        ("Provide prescriptions", "I take Lisinopril 10mg daily and Metformin 500mg twice a day."),
        ("Provide allergies", "I'm allergic to penicillin and shellfish."),
        ("Provide conditions", "I have high blood pressure and diabetes."),
        ("Provide visit reason", "I'm here for my annual checkup and to discuss my blood pressure medication."),
    ]
    
    for step_name, message in steps:
        result = send_message(message, step_name)
        if not result:
            break
        
        if result.get('end_call', False):
            print(f"\n🎉 Call ended after: {step_name}")
            break
        
        input("\nPress Enter to continue to next step...")
    
    print("\n🏁 Debug session complete!")

if __name__ == "__main__":
    test_conversation() 