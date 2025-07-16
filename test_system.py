# test_system.py - Test the complete SOAP Note App system
import requests
import time
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8002"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is healthy!")
            print(f"   Status: {data.get('data', {}).get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("💡 Make sure to start backend first: python start_backend.py")
        return False

def test_session_workflow():
    """Test complete session workflow"""
    print("\n🧪 Testing Session Workflow...")
    
    # 1. Start session
    print("1️⃣ Starting new session...")
    response = requests.post(f"{BACKEND_URL}/session/start", json={})
    if response.status_code != 200:
        print(f"❌ Failed to start session: {response.status_code}")
        return False
    
    session_data = response.json()
    session_id = session_data['data']['session_id']
    print(f"✅ Session started: {session_id}")
    
    # 2. Simulate conversation (without actual audio)
    print("2️⃣ Simulating conversation...")
    
    # Mock conversation messages
    mock_messages = [
        {"speaker": "Patient", "text": "Hi doctor, I've been having stomach pain for 2 days", "timestamp": "10:00:01"},
        {"speaker": "Doctor", "text": "Can you describe the pain? Where exactly is it located?", "timestamp": "10:00:15"},
        {"speaker": "Patient", "text": "It's in my upper abdomen, feels like burning sensation", "timestamp": "10:00:30"},
        {"speaker": "Doctor", "text": "Any nausea or vomiting? Have you taken any medications?", "timestamp": "10:00:45"},
        {"speaker": "Patient", "text": "Yes, some nausea but no vomiting. I took some antacids", "timestamp": "10:01:00"},
        {"speaker": "Doctor", "text": "Based on your symptoms, this sounds like gastritis. I'll prescribe medication", "timestamp": "10:01:20"}
    ]
    
    # Add messages to session (simulating voice processing)
    for msg in mock_messages:
        response = requests.post(f"{BACKEND_URL}/add_to_conversation", json={
            "speaker": msg["speaker"],
            "text": msg["text"]
        })
        if response.status_code == 200:
            print(f"   ✅ Added: {msg['speaker']} - {msg['text'][:30]}...")
        else:
            print(f"   ❌ Failed to add message: {response.status_code}")
    
    # 3. Get conversation
    print("3️⃣ Retrieving conversation...")
    response = requests.get(f"{BACKEND_URL}/session/{session_id}/conversation")
    if response.status_code == 200:
        conv_data = response.json()
        message_count = conv_data['data']['message_count']
        print(f"✅ Retrieved conversation with {message_count} messages")
    else:
        print(f"❌ Failed to get conversation: {response.status_code}")
        return False
    
    # 4. Generate SOAP note
    print("4️⃣ Generating SOAP note...")
    response = requests.post(f"{BACKEND_URL}/soap/generate", json={
        "session_id": session_id,
        "patient_name": "John Doe"
    })
    
    if response.status_code == 200:
        soap_data = response.json()
        soap_note = soap_data['data']
        print("✅ SOAP note generated successfully!")
        print(f"   Patient: {soap_note.get('patient_name')}")
        print(f"   Date: {soap_note.get('date')}")
        print(f"   Confidence: {soap_note.get('confidence_score', 0):.1%}")
        
        # Display SOAP sections
        print("\n📋 Generated SOAP Note:")
        print("=" * 50)
        print(f"S - SUBJECTIVE:\n{soap_note.get('subjective', 'N/A')}\n")
        print(f"O - OBJECTIVE:\n{soap_note.get('objective', 'N/A')}\n")
        print(f"A - ASSESSMENT:\n{soap_note.get('assessment', 'N/A')}\n")
        print(f"P - PLAN:\n{soap_note.get('plan', 'N/A')}\n")
        print("=" * 50)
        
    else:
        print(f"❌ Failed to generate SOAP note: {response.status_code}")
        print(f"   Error: {response.text}")
        return False
    
    # 5. Stop session
    print("5️⃣ Stopping session...")
    response = requests.post(f"{BACKEND_URL}/session/stop", json={"session_id": session_id})
    if response.status_code == 200:
        print("✅ Session stopped successfully!")
    else:
        print(f"❌ Failed to stop session: {response.status_code}")
    
    return True

def test_active_sessions():
    """Test active sessions endpoint"""
    print("\n🧪 Testing Active Sessions...")
    response = requests.get(f"{BACKEND_URL}/sessions/active")
    if response.status_code == 200:
        data = response.json()
        session_count = data['data']['count']
        print(f"✅ Active sessions retrieved: {session_count} sessions")
        return True
    else:
        print(f"❌ Failed to get active sessions: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🧪 SOAP Note App System Test")
    print("=" * 40)
    
    # Test backend health
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start it first:")
        print("   python start_backend.py")
        return
    
    # Test session workflow
    if not test_session_workflow():
        print("\n❌ Session workflow test failed")
        return
    
    # Test active sessions
    if not test_active_sessions():
        print("\n❌ Active sessions test failed")
        return
    
    print("\n🎉 All tests passed successfully!")
    print("\n📋 System is ready for use:")
    print("1. Backend is running on: http://localhost:8001")
    print("2. Start frontend: python start_frontend.py")
    print("3. Open browser: http://localhost:8501")
    print("\n✨ Happy SOAP note generation! ✨")

if __name__ == "__main__":
    main()
