#!/usr/bin/env python3
"""
Test what data the web application is actually loading.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_webapp_data():
    """Test what data the webapp will load."""
    print("🔍 Testing Web Application Data Loading")
    print("=" * 45)
    
    # Simulate what the app does
    from app import DataManager
    
    # Load data the same way the app does
    scraped_data = DataManager.load_latest_scraped_data()
    
    if not scraped_data:
        print("❌ No data loaded by DataManager")
        return
    
    conditions = scraped_data.get('conditions', [])
    print(f"📊 DataManager loaded {len(conditions)} conditions")
    
    # Test search simulation
    query = "acne"
    search_results = []
    
    for condition in conditions:
        if query.lower() in condition['name'].lower():
            search_results.append(condition)
    
    print(f"🔍 Search simulation for '{query}': {len(search_results)} results")
    
    if search_results:
        condition = search_results[0]
        print(f"\n📋 Sample condition that would be returned by API:")
        print(f"   Name: {condition['name']}")
        print(f"   URL: {condition.get('url', 'No URL')}")
        print(f"   Has description: {'description' in condition}")
        
        if 'description' in condition:
            desc = condition['description']
            print(f"   Description length: {len(desc) if desc else 0}")
            print(f"   Description preview: {repr(desc[:100] if desc else '')}")
            
            # This is what would be sent in JSON
            json_data = {
                'name': condition['name'],
                'description': condition.get('description', ''),
                'url': condition.get('url', '')
            }
            
            json_str = json.dumps(json_data, ensure_ascii=False)
            print(f"   JSON size: {len(json_str)} characters")
            
            # Parse back to simulate what JavaScript gets
            parsed = json.loads(json_str)
            print(f"   Parsed description: {repr(parsed.get('description', ''))}")
            
        else:
            print(f"   ❌ No description field in condition data")
            print(f"   Available fields: {list(condition.keys())}")
    
    # Check the actual file being used
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if 
            (f.startswith('ceaf_conditions_') or 
             f.startswith('enhanced_ceaf_conditions_') or 
             f.startswith('enhanced_parsed_ceaf_conditions_') or
             f.startswith('enhanced_with_descriptions_')) 
            and f.endswith('.json')]
    
    if files:
        latest_file = sorted(files)[-1]
        print(f"\n📁 Latest data file being used: {latest_file}")
        
        # Check file size and modification time
        filepath = os.path.join(data_dir, latest_file)
        file_size = os.path.getsize(filepath)
        mod_time = os.path.getmtime(filepath)
        
        print(f"   File size: {file_size:,} bytes")
        print(f"   Modified: {mod_time}")
        
        # Quick check of file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        file_conditions = file_data.get('conditions', [])
        conditions_with_desc = [c for c in file_conditions if c.get('description')]
        
        print(f"   Conditions in file: {len(file_conditions)}")
        print(f"   With descriptions: {len(conditions_with_desc)}")
        
        if conditions_with_desc:
            print(f"   ✅ File contains descriptions")
        else:
            print(f"   ❌ File has no descriptions")
    
    print(f"\n💡 Debugging steps:")
    print(f"   1. Check browser console for JavaScript errors")
    print(f"   2. Use browser developer tools to inspect search API responses")
    print(f"   3. Check if descriptions are being sent but not displayed")

if __name__ == "__main__":
    test_webapp_data()