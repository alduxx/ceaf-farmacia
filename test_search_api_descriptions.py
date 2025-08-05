#!/usr/bin/env python3
"""
Test script to check if search API returns descriptions.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import DataManager

def test_search_api_descriptions():
    """Test what the search API would return for descriptions."""
    print("🔍 Testing Search API Description Data")
    print("=" * 45)
    
    # Load the data the same way the app does
    scraped_data = DataManager.load_latest_scraped_data()
    
    if not scraped_data:
        print("❌ No data found")
        return
    
    conditions = scraped_data.get('conditions', [])
    print(f"📊 Total conditions: {len(conditions)}")
    
    # Test what a search would return
    print(f"\n🔍 Testing search functionality...")
    
    # Simulate search for "acne"
    query = "acne"
    search_results = []
    
    for condition in conditions:
        if query.lower() in condition['name'].lower():
            search_results.append(condition)
    
    print(f"📋 Search for '{query}' found {len(search_results)} results")
    
    if search_results:
        sample_result = search_results[0]
        print(f"\n📄 Sample search result structure:")
        print(f"   Name: {sample_result['name']}")
        print(f"   Has description: {'description' in sample_result}")
        
        if 'description' in sample_result:
            desc = sample_result['description']
            print(f"   Description: {repr(desc)}")
            
            # Check if it's the expected format
            if desc and '\n' in desc:
                lines = desc.split('\n')
                print(f"   Format analysis:")
                print(f"     Lines: {len(lines)}")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"     Line {i+1}: {line.strip()}")
            else:
                print(f"   ⚠️  Description format might be wrong")
        else:
            print(f"   ❌ No description field found")
            print(f"   Available fields: {list(sample_result.keys())}")
    
    # Test all conditions for descriptions
    conditions_with_descriptions = [c for c in conditions if c.get('description')]
    print(f"\n📊 Conditions with descriptions: {len(conditions_with_descriptions)}")
    
    if conditions_with_descriptions:
        print(f"\n📋 Sample conditions with descriptions:")
        for i, condition in enumerate(conditions_with_descriptions[:3]):
            print(f"\n{i+1}. {condition['name']}")
            desc = condition.get('description', '')
            if desc:
                # Show a preview
                preview = desc.replace('\n', ' | ')
                if len(preview) > 80:
                    preview = preview[:80] + "..."
                print(f"   Preview: {preview}")
            
            # Check if this would be returned by search API
            result_json = {
                'name': condition['name'],
                'description': condition.get('description', ''),
                'url': condition.get('url', ''),
                'cid_10': condition.get('cid_10', []),
                'medicamentos': condition.get('medicamentos', [])
            }
            
            # Simulate JSON serialization (what the API does)
            json_str = json.dumps(result_json, ensure_ascii=False)
            parsed_back = json.loads(json_str)
            
            if parsed_back.get('description'):
                print(f"   ✅ Would be sent by API with description")
            else:
                print(f"   ❌ Would be sent by API WITHOUT description")
    
    print(f"\n💡 Analysis:")
    total = len(conditions)
    with_desc = len(conditions_with_descriptions)
    percentage = (with_desc / total * 100) if total > 0 else 0
    
    print(f"   Total conditions: {total}")
    print(f"   With descriptions: {with_desc} ({percentage:.1f}%)")
    
    if with_desc > 0:
        print(f"   ✅ Search API should return descriptions")
        print(f"   💡 Check JavaScript console for formatDescription errors")
    else:
        print(f"   ❌ No descriptions available for search API")
        print(f"   💡 Run enhanced scraper or add_descriptions_to_existing_data.py")

if __name__ == "__main__":
    test_search_api_descriptions()