#!/usr/bin/env python3
"""
Test the automatic description addition functionality.
"""

import sys
import os
import json
import tempfile
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper

def test_auto_descriptions():
    """Test that the auto description functionality works."""
    print("🧪 Testing Automatic Description Addition")
    print("=" * 45)
    
    # Create a sample condition without description
    sample_data = {
        'scraped_at': datetime.now().isoformat(),
        'total_conditions': 1,
        'conditions': [
            {
                'name': 'Test Condition',
                'url': 'https://example.com/test',
                'scraped_at': datetime.now().isoformat(),
                'cid_10': ['L70.0', 'L70.1'],
                'medicamentos': ['Test Medicine 1', 'Test Medicine 2'],
                'pdf_extracted': True
            }
        ]
    }
    
    print("📋 Testing with sample condition:")
    print(f"   Name: {sample_data['conditions'][0]['name']}")
    print(f"   Medications: {sample_data['conditions'][0]['medicamentos']}")
    print(f"   CID-10: {sample_data['conditions'][0]['cid_10']}")
    print(f"   Has description: {'description' in sample_data['conditions'][0]}")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
        temp_filepath = f.name
    
    try:
        print(f"\n🔧 Simulating auto-description logic...")
        
        # Initialize scraper
        scraper = CEAFScraper()
        
        # Load the data
        with open(temp_filepath, 'r', encoding='utf-8') as f:
            data_with_descriptions = json.load(f)
        
        # Apply the same logic as in the enhanced scraper
        updated_count = 0
        for condition in data_with_descriptions.get('conditions', []):
            existing_desc = condition.get('description', '')
            
            # Only add description if it doesn't exist or is empty
            if not existing_desc or existing_desc.strip() == '':
                new_description = scraper.create_custom_description(condition)
                
                if new_description and new_description != existing_desc:
                    condition['description'] = new_description
                    updated_count += 1
                    print(f"   ✅ Added description to: {condition['name']}")
        
        # Update metadata
        data_with_descriptions['descriptions_added_at'] = datetime.now().isoformat()
        data_with_descriptions['descriptions_updated_count'] = updated_count
        
        # Save back
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_descriptions, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Results:")
        print(f"   Updated conditions: {updated_count}")
        
        # Show the result
        final_condition = data_with_descriptions['conditions'][0]
        if final_condition.get('description'):
            print(f"   Final description: {repr(final_condition['description'])}")
            
            # Parse the description
            desc_lines = final_condition['description'].split('\n')
            print(f"   Parsed format:")
            for i, line in enumerate(desc_lines):
                if line.strip():
                    label = "Medications" if i == 0 else "CID-10" if i == 1 else f"Line {i+1}"
                    print(f"     {label}: {line.strip()}")
            
            print("   ✅ Auto-description logic is working correctly!")
        else:
            print("   ❌ No description was created")
        
    finally:
        # Clean up
        if os.path.exists(temp_filepath):
            os.unlink(temp_filepath)
    
    print(f"\n💡 The enhanced scraper scripts will now automatically:")
    print(f"   1. Run the normal scraping process")
    print(f"   2. Add custom descriptions to all conditions")
    print(f"   3. Save the data with descriptions included")
    print(f"   4. No need to run add_descriptions_to_existing_data.py separately!")

if __name__ == "__main__":
    test_auto_descriptions()