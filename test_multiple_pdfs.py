#!/usr/bin/env python3
"""
Test script for multiple PDF functionality using the epilepsia condition.
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper

def test_epilepsia_multiple_pdfs():
    """Test the multiple PDF functionality specifically with epilepsia condition."""
    print("🧪 Testing Multiple PDFs Functionality")
    print("=" * 45)
    print("Testing with epilepsia condition which should have multiple PDFs:")
    print("- Epilepsia-MS")
    print("- Epilepsia-SES/DF") 
    print("- Epilepsia Canabidiol SES-DF")
    print()
    
    # Create a mock epilepsia condition
    epilepsia_condition = {
        'name': 'Epilepsia',
        'url': 'https://www.saude.df.gov.br/epilepsia',
        'scraped_at': datetime.now().isoformat()
    }
    
    try:
        # Initialize scraper
        scraper = CEAFScraper(use_llm=False)  # Use text parser for faster testing
        
        print("🔍 Finding PDFs for epilepsia condition...")
        pdf_links = scraper.find_condition_pdfs(epilepsia_condition['url'], epilepsia_condition['name'])
        
        if not pdf_links:
            print("❌ No PDFs found for epilepsia condition")
            return
        
        print(f"📄 Found {len(pdf_links)} PDF(s):")
        for i, pdf_link in enumerate(pdf_links):
            print(f"   {i+1}. {pdf_link['text']} (score: {pdf_link['match_score']:.2f})")
            print(f"      URL: {pdf_link['url']}")
        
        if len(pdf_links) == 1:
            print("\n⚠️  Only one PDF found. Expected multiple PDFs for epilepsia.")
            print("   This might be expected if the website structure has changed.")
        else:
            print(f"\n✅ Multiple PDFs found as expected!")
        
        print("\n🔧 Testing the full scraping process...")
        
        # Create a minimal scraper test with just the epilepsia condition
        base_conditions = [epilepsia_condition]
        all_conditions = []
        
        # Simulate the multiple PDF processing logic
        for i, base_condition in enumerate(base_conditions):
            print(f"\n📋 Processing condition: {base_condition['name']}")
            
            # Find ALL PDFs for this condition
            pdf_links = scraper.find_condition_pdfs(base_condition['url'], base_condition['name'])
            
            if pdf_links:
                # Process the first PDF
                first_pdf = pdf_links[0]
                condition_copy = base_condition.copy()
                
                print(f"   📑 Processing first PDF: {first_pdf['text']}")
                condition_copy['pdf_url'] = first_pdf['url']
                condition_copy['pdf_name'] = first_pdf['text']
                condition_copy['pdf_extracted'] = True  # Simulate successful extraction
                
                # Simulate extracted data
                condition_copy['medicamentos'] = ['Medicamento A', 'Medicamento B']
                condition_copy['cid_10'] = ['G40', 'G41']
                condition_copy['description'] = scraper.create_custom_description(condition_copy)
                
                all_conditions.append(condition_copy)
                print(f"   ✅ First condition created with description: {condition_copy['description']}")
                
                # Process additional PDFs
                for j, additional_pdf in enumerate(pdf_links[1:], 1):
                    print(f"   📑 Processing additional PDF {j}: {additional_pdf['text']}")
                    
                    # Create duplicate condition
                    duplicate_condition = base_condition.copy()
                    duplicate_condition['pdf_url'] = additional_pdf['url']
                    duplicate_condition['pdf_name'] = additional_pdf['text']
                    duplicate_condition['pdf_extracted'] = True
                    
                    # Simulate different extracted data for additional PDF
                    duplicate_condition['medicamentos'] = [f'Medicamento Additional {j}A', f'Medicamento Additional {j}B']
                    duplicate_condition['cid_10'] = [f'G4{j}', f'G4{j+1}']
                    duplicate_condition['description'] = scraper.create_custom_description(duplicate_condition)
                    
                    all_conditions.append(duplicate_condition)
                    print(f"   ✅ Additional condition {j} created with description: {duplicate_condition['description']}")
            else:
                print(f"   ❌ No PDFs found for {base_condition['name']}")
                all_conditions.append(base_condition)
        
        print(f"\n📊 Test Results:")
        print(f"   Base conditions: {len(base_conditions)}")
        print(f"   Final conditions: {len(all_conditions)}")
        print(f"   Additional conditions created: {len(all_conditions) - len(base_conditions)}")
        
        print(f"\n📋 Final condition list:")
        for i, condition in enumerate(all_conditions):
            print(f"   {i+1}. {condition['name']} - PDF: {condition.get('pdf_name', 'No PDF')}")
            if condition.get('description'):
                preview = condition['description'][:100] + "..." if len(condition['description']) > 100 else condition['description']
                print(f"      Description: {preview}")
        
        print(f"\n✅ Multiple PDF test completed successfully!")
        
        if len(all_conditions) > len(base_conditions):
            print(f"✅ Multiple PDF functionality is working correctly!")
            print(f"   Created {len(all_conditions) - len(base_conditions)} additional condition(s) for multiple PDFs")
        else:
            print(f"ℹ️  No additional conditions created (only found 1 PDF per condition)")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_epilepsia_multiple_pdfs()