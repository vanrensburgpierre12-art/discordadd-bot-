#!/usr/bin/env python3
"""
Test script for simulating webhook calls from ad networks
Useful for testing the rewards platform locally
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:5000/postback"
TEST_USERS = [
    "123456789",
    "987654321", 
    "555666777",
    "111222333",
    "444555666"
]

TEST_OFFERS = [
    "survey_complete_001",
    "video_watch_002",
    "app_install_003",
    "signup_004",
    "quiz_complete_005"
]

def test_single_webhook(user_id, points, offer_id):
    """Test a single webhook call"""
    payload = {
        "uid": user_id,
        "points": points,
        "offer_id": offer_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TestBot/1.0"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {user_id} earned {points} points")
            print(f"   Response: {result}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    return response.status_code == 200

def test_duplicate_prevention():
    """Test that duplicate offer completions are prevented"""
    print("\n🧪 Testing Duplicate Prevention...")
    
    user_id = "test_user_123"
    offer_id = "duplicate_test_offer"
    points = 25
    
    # First call should succeed
    print(f"1️⃣ First call for {user_id} with {offer_id}")
    success1 = test_single_webhook(user_id, points, offer_id)
    
    # Second call with same offer_id should fail
    print(f"2️⃣ Second call for {user_id} with {offer_id} (should fail)")
    success2 = test_single_webhook(user_id, points, offer_id)
    
    if success1 and not success2:
        print("✅ Duplicate prevention working correctly!")
    else:
        print("❌ Duplicate prevention not working as expected")

def test_invalid_data():
    """Test webhook with invalid data"""
    print("\n🧪 Testing Invalid Data Handling...")
    
    test_cases = [
        {"uid": "", "points": 20, "offer_id": "test"},
        {"points": 20, "offer_id": "test"},  # Missing uid
        {"uid": "123", "offer_id": "test"},  # Missing points
        {"uid": "123", "points": -5, "offer_id": "test"},  # Negative points
        {"uid": "123", "points": "invalid", "offer_id": "test"},  # Invalid points type
    ]
    
    for i, payload in enumerate(test_cases, 1):
        print(f"{i}️⃣ Testing invalid payload: {payload}")
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")

def test_bulk_webhooks():
    """Test multiple webhook calls to simulate real usage"""
    print("\n🧪 Testing Bulk Webhooks...")
    
    successful_calls = 0
    total_calls = 20
    
    for i in range(total_calls):
        user_id = random.choice(TEST_USERS)
        offer_id = f"{random.choice(TEST_OFFERS)}_{i:03d}"
        points = random.randint(10, 50)
        
        print(f"📡 Call {i+1}/{total_calls}: {user_id} -> {points} points")
        
        if test_single_webhook(user_id, points, offer_id):
            successful_calls += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print(f"\n📊 Bulk Test Results: {successful_calls}/{total_calls} successful calls")

def test_health_endpoints():
    """Test health and stats endpoints"""
    print("\n🧪 Testing Health Endpoints...")
    
    endpoints = [
        ("/", "Home page"),
        ("/health", "Health check"),
        ("/stats", "Platform statistics")
    ]
    
    base_url = WEBHOOK_URL.replace("/postback", "")
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {description}: {response.status_code}")
            
            if response.status_code == 200 and endpoint == "/stats":
                stats = response.json()
                print(f"   Users: {stats.get('total_users', 'N/A')}")
                print(f"   Total Points: {stats.get('total_points_in_circulation', 'N/A')}")
                print(f"   Redemptions: {stats.get('total_redemptions', 'N/A')}")
                
        except Exception as e:
            print(f"❌ {description}: {e}")

def main():
    """Main test function"""
    print("🎮 Discord Rewards Platform - Webhook Test Suite")
    print("=" * 60)
    print(f"Target URL: {WEBHOOK_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(WEBHOOK_URL.replace("/postback", "/health"), timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
        else:
            print("⚠️  Server responded but health check failed")
    except:
        print("❌ Server is not running or not accessible")
        print("Please start the Flask backend first: python flask_app.py")
        return
    
    # Run tests
    test_health_endpoints()
    test_single_webhook("test_user_001", 30, "test_offer_001")
    test_duplicate_prevention()
    test_invalid_data()
    test_bulk_webhooks()
    
    print("\n🎉 Test suite completed!")
    print("\nNext steps:")
    print("1. Check the Discord bot for notifications")
    print("2. Verify points were added to users")
    print("3. Test the /balance and /redeem commands")

if __name__ == "__main__":
    main()