#!/usr/bin/env python3
"""
Test script to demonstrate MongoDB recovery
"""
import time
import requests
import threading

def test_recovery_flow():
    """Test the complete recovery flow"""
    print("\n" + "="*60)
    print("🧪 Testing Autonomous Recovery Agent")
    print("="*60)
    
    base_url = "http://localhost:5000"
    
    print("\n1. Checking initial health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   ✅ Health check: {response.status_code}")
        print(f"   Response: {response.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    print("\n2. Checking recovery status...")
    try:
        response = requests.get(f"{base_url}/recovery/status", timeout=5)
        print(f"   ✅ Recovery status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Recovery status failed: {e}")
    
    print("\n3. Checking recovery health...")
    try:
        response = requests.get(f"{base_url}/recovery/health", timeout=5)
        data = response.json()
        if data.get("status") == "ok":
            db_health = data.get("health", {}).get("database", {})
            print(f"   ✅ Database status: {db_health.get('status', 'unknown')}")
            print(f"   📊 Reachable: {db_health.get('is_reachable', False)}")
    except Exception as e:
        print(f"   ❌ Recovery health failed: {e}")
    
    print("\n4. Testing MongoDB failure...")
    print("   ⚠️  Please stop MongoDB now (net stop MongoDB)")
    print("   Waiting 30 seconds for agent to detect failure...")
    time.sleep(30)
    
    print("\n5. Checking status after MongoDB stop...")
    try:
        response = requests.get(f"{base_url}/recovery/health", timeout=5)
        data = response.json()
        if data.get("status") == "ok":
            db_health = data.get("health", {}).get("database", {})
            status = db_health.get('status', 'unknown')
            print(f"   📊 Database status: {status}")
            
            if status == "disconnected":
                print("   ✅ Agent correctly detected MongoDB is down!")
                print("   🔄 Recovery attempts should be in progress...")
    except Exception as e:
        print(f"   ❌ Check failed: {e}")
    
    print("\n6. Testing recovery...")
    print("   ⚡ Please start MongoDB now (net start MongoDB)")
    print("   Waiting 30 seconds for agent to detect recovery...")
    time.sleep(30)
    
    print("\n7. Checking final status...")
    try:
        response = requests.get(f"{base_url}/recovery/health", timeout=5)
        data = response.json()
        if data.get("status") == "ok":
            db_health = data.get("health", {}).get("database", {})
            status = db_health.get('status', 'unknown')
            reachable = db_health.get('is_reachable', False)
            
            print(f"   📊 Database status: {status}")
            print(f"   ✅ Reachable: {reachable}")
            
            if reachable:
                print("   🎉 MongoDB recovered successfully!")
            else:
                print("   ⚠️  MongoDB still not reachable")
    except Exception as e:
        print(f"   ❌ Final check failed: {e}")
    
    print("\n" + "="*60)
    print("Test complete! Check the logs for recovery messages.")
    print("="*60)

if __name__ == "__main__":
    # Give Flask time to start
    print("Waiting for Flask to start...")
    time.sleep(5)
    
    test_recovery_flow()