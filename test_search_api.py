#!/usr/bin/env python3
"""
Test the enhanced search API endpoints.
"""

import requests
import json
import time

def test_search_endpoints():
    print("🔍 Testing Enhanced Search API")
    print("=" * 35)
    
    base_url = "http://127.0.0.1:5000"
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Test 1: Search by condition name
    print("1️⃣  Testing condition search...")
    try:
        response = requests.get(f"{base_url}/search?q=acne")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total']} results for 'acne'")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test 2: Search by medication
    print("2️⃣  Testing medication search...")
    try:
        response = requests.get(f"{base_url}/search/medication?q=isotretinoína")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total']} results for 'isotretinoína'")
            if data['results']:
                print(f"   📋 Found condition: {data['results'][0]['name']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test 3: Search by CID-10
    print("3️⃣  Testing CID-10 search...")
    try:
        response = requests.get(f"{base_url}/search/cid?q=L70")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total']} results for 'L70'")
            if data['results']:
                print(f"   📋 Found condition: {data['results'][0]['name']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test 4: Check condition detail page
    print("4️⃣  Testing condition detail page...")
    try:
        response = requests.get(f"{base_url}/condition/Acne Grave")
        if response.status_code == 200:
            print("   ✅ Condition detail page loads successfully")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    print("\n💡 If connection errors occurred, make sure the web server is running:")
    print("   python run.py")

if __name__ == "__main__":
    test_search_endpoints()