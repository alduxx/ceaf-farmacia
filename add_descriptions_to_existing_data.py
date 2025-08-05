#!/usr/bin/env python3
"""
Add custom descriptions to existing data files that don't have them.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper

def add_descriptions_to_data():
    """Add custom descriptions to existing data."""
    print("🔧 Adding Descriptions to Existing Data")
    print("=" * 45)
    
    # Find the latest data file
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not files:
        print("❌ No data files found")
        return
    
    latest_file = sorted(files)[-1]
    filepath = os.path.join(data_dir, latest_file)
    
    print(f"📂 Processing file: {latest_file}")
    
    # Load data
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conditions = data.get('conditions', [])
    print(f"📋 Found {len(conditions)} conditions")
    
    # Initialize scraper to use the description method
    scraper = CEAFScraper()
    
    # Process each condition
    updated_count = 0
    for i, condition in enumerate(conditions):
        # Check if description already exists and is meaningful
        existing_desc = condition.get('description', '')
        
        # Only add description if it doesn't exist or is empty
        if not existing_desc or existing_desc.strip() == '':
            # Create custom description
            new_description = scraper.create_custom_description(condition)
            
            if new_description and new_description != existing_desc:
                condition['description'] = new_description
                updated_count += 1
                print(f"   ✅ Added description to: {condition['name']}")
                print(f"      Description: {new_description[:100]}{'...' if len(new_description) > 100 else ''}")
            else:
                print(f"   ⚠️  No description data for: {condition['name']}")
        else:
            print(f"   ℹ️  Description already exists for: {condition['name']}")
    
    # Update metadata
    data['descriptions_added_at'] = datetime.now().isoformat()
    data['descriptions_updated_count'] = updated_count
    
    # Save updated data
    output_filename = f"enhanced_with_descriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_filepath = os.path.join(data_dir, output_filename)
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Processing completed!")
    print(f"📁 Updated data saved to: {output_filepath}")
    print(f"🔧 Added descriptions to {updated_count} conditions")
    
    # Show sample results
    conditions_with_descriptions = [c for c in conditions if c.get('description')]
    if conditions_with_descriptions:
        print(f"\n📊 Sample descriptions:")
        for i, condition in enumerate(conditions_with_descriptions[:3]):
            print(f"\n{i+1}. {condition['name']}:")
            desc = condition['description']
            lines = desc.split('\n') if desc else []
            for j, line in enumerate(lines):
                if line.strip():
                    print(f"   Line {j+1}: {line.strip()}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Start the web application: python run.py")
    print(f"   2. Test search functionality to see descriptions")
    print(f"   3. View condition detail pages")

if __name__ == "__main__":
    add_descriptions_to_data()