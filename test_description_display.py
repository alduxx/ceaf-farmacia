#!/usr/bin/env python3
"""
Test script to verify description display functionality.
This script will check if descriptions are properly formatted and available.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import DataManager

def test_description_display():
    """Test if descriptions are properly formatted and displayed."""
    print("🔍 Testing Description Display Functionality")
    print("=" * 50)
    
    # Load the latest data
    scraped_data = DataManager.load_latest_scraped_data()
    
    if not scraped_data:
        print("❌ No data found. Run the enhanced scraper first:")
        print("   python run_enhanced_scraper.py --limit 5")
        return
    
    conditions = scraped_data.get('conditions', [])
    print(f"📊 Total conditions: {len(conditions)}")
    
    # Find conditions with descriptions
    conditions_with_descriptions = [c for c in conditions if c.get('description')]
    print(f"📝 Conditions with descriptions: {len(conditions_with_descriptions)}")
    
    # Find conditions with custom format descriptions (our format)
    custom_format_conditions = []
    for condition in conditions_with_descriptions:
        desc = condition['description']
        if '\n' in desc and len(desc.split('\n')) >= 2:
            lines = desc.split('\n')
            # Check if it looks like our format (medications, CID-10)
            if lines[0].strip() and lines[1].strip():
                custom_format_conditions.append(condition)
    
    print(f"🎯 Conditions with custom format descriptions: {len(custom_format_conditions)}")
    
    if not conditions_with_descriptions:
        print("\n⚠️  No conditions with descriptions found.")
        print("   This might indicate that the enhanced scraper hasn't been run yet")
        print("   or that the description creation logic isn't working.")
        return
    
    print(f"\n📋 Sample descriptions:")
    print("=" * 50)
    
    # Show sample descriptions
    for i, condition in enumerate(conditions_with_descriptions[:5]):
        print(f"\n{i+1}. Condition: {condition['name']}")
        print(f"   Description: {repr(condition['description'])}")
        
        # Analyze the format
        desc = condition['description']
        lines = desc.split('\n') if desc else []
        print(f"   Lines: {len(lines)}")
        
        for j, line in enumerate(lines):
            if line.strip():
                print(f"   Line {j+1}: {line.strip()}")
        
        # Check if it has our enhanced data
        has_medications = bool(condition.get('medicamentos'))
        has_cid10 = bool(condition.get('cid_10'))
        print(f"   Has medications: {has_medications} ({len(condition.get('medicamentos', []))} items)")
        print(f"   Has CID-10: {has_cid10} ({len(condition.get('cid_10', []))} items)")
        
        if has_medications or has_cid10:
            print("   ✅ This condition has structured data")
        else:
            print("   ⚠️  This condition lacks structured data")
    
    # Test the JavaScript formatting logic (simulate)
    print(f"\n🧪 Testing JavaScript formatDescription logic:")
    print("=" * 50)
    
    def format_description_python(description):
        """Python version of the JavaScript formatDescription function."""
        if not description:
            return '<p class="text-muted small mb-0">Sem descrição disponível</p>'
        
        lines = [line.strip() for line in description.split('\n') if line.strip()]
        
        if len(lines) == 0:
            return '<p class="text-muted small mb-0">Sem descrição disponível</p>'
        
        if len(lines) == 1:
            line = lines[0]
            if len(line) > 120:
                return f'<p class="text-muted small mb-0">{line[:120]}...</p>'
            return f'<p class="text-muted small mb-0">{line}</p>'
        
        html = ''
        
        # First line - medications
        if lines[0]:
            medications = lines[0]
            if len(medications) > 60:
                medications = medications[:60] + '...'
            html += f'<p class="text-muted small mb-1"><i class="fas fa-pills me-1 text-success"></i><strong>Medicamentos:</strong> {medications}</p>'
        
        # Second line - CID-10
        if len(lines) > 1 and lines[1]:
            cid_codes = lines[1]
            html += f'<p class="text-muted small mb-0"><i class="fas fa-code me-1 text-info"></i><strong>CID-10:</strong> {cid_codes}</p>'
        
        return html
    
    # Test with sample conditions
    for i, condition in enumerate(custom_format_conditions[:3]):
        print(f"\n📄 Test {i+1}: {condition['name']}")
        desc = condition['description']
        formatted = format_description_python(desc)
        
        print(f"   Original: {repr(desc)}")
        print(f"   Formatted HTML: {formatted}")
        
        # Verify it contains expected elements
        has_medications_icon = 'fa-pills' in formatted
        has_cid_icon = 'fa-code' in formatted
        has_structured_format = '<strong>Medicamentos:</strong>' in formatted or '<strong>CID-10:</strong>' in formatted
        
        print(f"   Has medication icon: {has_medications_icon}")
        print(f"   Has CID-10 icon: {has_cid_icon}")
        print(f"   Has structured format: {has_structured_format}")
        
        if has_structured_format:
            print("   ✅ Formatting looks correct!")
        else:
            print("   ⚠️  Formatting needs attention")
    
    print(f"\n📊 Summary:")
    print(f"   Total conditions: {len(conditions)}")
    print(f"   With descriptions: {len(conditions_with_descriptions)}")
    print(f"   With custom format: {len(custom_format_conditions)}")
    
    if len(custom_format_conditions) > 0:
        percentage = (len(custom_format_conditions) / len(conditions)) * 100
        print(f"   Custom format coverage: {percentage:.1f}%")
        print("   ✅ Description functionality is working!")
    else:
        print("   ❌ No custom format descriptions found")
        print("   This indicates the enhanced scraper needs to be run with PDF processing")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Start the web application: python run.py")
    print(f"   2. Test search functionality to see descriptions in search results")
    print(f"   3. View condition detail pages to see enhanced descriptions")

if __name__ == "__main__":
    test_description_display()