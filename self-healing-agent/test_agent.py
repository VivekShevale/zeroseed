#!/usr/bin/env python3
"""
Test script for the Self-Healing Agent.
"""
import requests
import time
import json

def test_agent():
    """Test the agent functionality"""
    
    print("🧪 Testing Self-Healing Agent...")
    
    # Test 1: Check if agent is running
    print("\n1. Checking agent health...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"   ✅ Agent health: {response.status_code}")
        print(f"   📊 Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Agent not reachable: {e}")
        return
    
    # Test 2: Check agent status
    print("\n2. Checking agent status...")
    try:
        response = requests.get("http://localhost:5000/status", timeout=5)
        status = response.json()
        print(f"   🤖 Agent running: {status.get('agent_running')}")
        print(f"   📈 Services monitored: {status.get('services_monitored')}")
        print(f"   ⚡ Total actions: {status.get('total_actions')}")
    except Exception as e:
        print(f"   ❌ Error getting status: {e}")
    
    # Test 3: Check mock service
    print("\n3. Checking mock service...")
    try:
        response = requests.get("http://localhost:6000/health", timeout=5)
        health = response.json()
        print(f"   🖥️ Service status: {health.get('status')}")
        print(f"   📊 Details: {json.dumps(health.get('details', {}), indent=4)}")
    except Exception as e:
        print(f"   ❌ Mock service not reachable: {e}")
    
    # Test 4: Test restart endpoint
    print("\n4. Testing restart endpoint...")
    try:
        response = requests.post(
            "http://localhost:6000/agent/restart",
            json={},
            timeout=5
        )
        print(f"   🔄 Restart status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Restart successful: {response.json()}")
    except Exception as e:
        print(f"   ❌ Restart failed: {e}")
    
    # Test 5: Simulate an issue
    print("\n5. Simulating memory leak...")
    try:
        response = requests.post(
            "http://localhost:6000/agent/simulate/memory_leak",
            json={},
            timeout=5
        )
        print(f"   🚨 Simulation response: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Memory leak simulated")
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
    
    # Test 6: Check health after simulation
    print("\n6. Checking health after simulation...")
    try:
        time.sleep(2)
        response = requests.get("http://localhost:6000/health", timeout=5)
        health = response.json()
        print(f"   🩺 Service status: {health.get('status')}")
        print(f"   💾 Memory usage: {health.get('details', {}).get('memory_usage')}%")
    except Exception as e:
        print(f"   ❌ Error checking health: {e}")
    
    # Test 7: Add a custom issue
    print("\n7. Adding custom issue to catalog...")
    try:
        response = requests.post(
            "http://localhost:5000/agent/add_issue",
            json={
                "issue": "CUSTOM_ISSUE",
                "action": "notify",
                "auto": True,
                "confidence": 0.8
            },
            timeout=5
        )
        print(f"   📝 Add issue response: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Custom issue added")
    except Exception as e:
        print(f"   ❌ Failed to add issue: {e}")
    
    # Test 8: Ingest metrics
    print("\n8. Ingesting metrics...")
    try:
        response = requests.post(
            "http://localhost:5000/agent/metrics",
            json={
                "service_id": "test-service",
                "metrics": {
                    "health": "UP",
                    "cpu": 75,
                    "memory": 85,
                    "latency": 200,
                    "error_rate": 0.1
                }
            },
            timeout=5
        )
        print(f"   📊 Metrics ingestion: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Metrics received: {response.json()}")
    except Exception as e:
        print(f"   ❌ Metrics ingestion failed: {e}")
    
    print("\n" + "="*50)
    print("🧪 Test completed!")
    print("="*50)
    print("\nNext steps:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Start the agent using the Start button")
    print("3. Watch it detect and fix issues automatically")
    print("4. Access the dashboard at http://localhost:5000/dashboard")

if __name__ == "__main__":
    test_agent()