#!/usr/bin/env python3
"""
Demo script for multiple PDF functionality with real data extraction.
This will test with just the epilepsia condition to demonstrate the feature.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper

def main():
    print("🎯 Multiple PDFs Demo - Real Data Extraction")
    print("=" * 50)
    print("This demo will scrape the epilepsia condition and show")
    print("how multiple PDFs are handled with real data extraction.")
    print()
    
    try:
        # Initialize scraper (using text parser for reliability)
        scraper = CEAFScraper(use_llm=False)
        
        # Create epilepsia condition entry
        epilepsia_condition = {
            'name': 'Epilepsia',
            'url': 'https://www.saude.df.gov.br/epilepsia',
            'scraped_at': datetime.now().isoformat()
        }
        
        print("🔍 Step 1: Finding all PDFs for epilepsia...")
        pdf_links = scraper.find_condition_pdfs(epilepsia_condition['url'], 'Epilepsia')
        
        print(f"📄 Found {len(pdf_links)} PDFs:")
        for i, pdf in enumerate(pdf_links):
            print(f"   {i+1}. {pdf['text']}")
        print()
        
        if len(pdf_links) <= 1:
            print("⚠️  Only one or no PDFs found. This demo works best with multiple PDFs.")
            print("   The functionality will still work but won't show duplication.")
        
        print("🔧 Step 2: Processing PDFs with real data extraction...")
        print("   This may take a few moments as PDFs are downloaded and processed...")
        print()
        
        # Simulate the scraper logic for this one condition
        base_conditions = [epilepsia_condition]
        all_conditions = []
        
        for base_condition in base_conditions:
            print(f"📋 Processing: {base_condition['name']}")
            
            # Extract basic details
            details = scraper.extract_condition_details(base_condition['url'])
            base_condition.update(details)
            
            if pdf_links:
                # Process the first PDF
                first_pdf = pdf_links[0]
                condition_copy = base_condition.copy()
                
                print(f"   📑 Processing first PDF: {first_pdf['text']}")
                condition_copy['pdf_url'] = first_pdf['url']
                condition_copy['pdf_name'] = first_pdf['text']
                
                # Download and extract first PDF
                pdf_content = scraper.download_pdf(first_pdf['url'])
                if pdf_content:
                    pdf_text = scraper.extract_pdf_text(pdf_content)
                    condition_copy['pdf_text'] = pdf_text
                    condition_copy['pdf_extracted'] = True
                    
                    # Extract structured data using text parser
                    if pdf_text.strip():
                        from pdf_text_parser import parse_pdf_text
                        structured_data = parse_pdf_text(pdf_text, condition_copy['name'])
                        condition_copy.update(structured_data)
                        
                        print(f"   ✅ Extracted {len(condition_copy.get('medicamentos', []))} medications")
                        print(f"   ✅ Extracted {len(condition_copy.get('cid_10', []))} CID-10 codes")
                else:
                    condition_copy['pdf_extracted'] = False
                
                # Create custom description
                condition_copy['description'] = scraper.create_custom_description(condition_copy)
                all_conditions.append(condition_copy)
                
                # Process additional PDFs
                for j, additional_pdf in enumerate(pdf_links[1:], 1):
                    print(f"   📑 Processing additional PDF {j}: {additional_pdf['text']}")
                    
                    # Create duplicate condition
                    duplicate_condition = base_condition.copy()
                    
                    # Remove PDF-specific data from first processing
                    pdf_specific_keys = ['cid_10', 'medicamentos', 'documentos_pessoais', 
                                       'documentos_medicos', 'exames', 'observacoes', 
                                       'extraction_method', 'pdf_text', 'pdf_url', 'pdf_name']
                    for key in pdf_specific_keys:
                        if key in duplicate_condition:
                            del duplicate_condition[key]
                    
                    # Process additional PDF
                    duplicate_condition['pdf_url'] = additional_pdf['url']
                    duplicate_condition['pdf_name'] = additional_pdf['text']
                    
                    pdf_content = scraper.download_pdf(additional_pdf['url'])
                    if pdf_content:
                        pdf_text = scraper.extract_pdf_text(pdf_content)
                        duplicate_condition['pdf_text'] = pdf_text
                        duplicate_condition['pdf_extracted'] = True
                        
                        # Extract structured data
                        if pdf_text.strip():
                            from pdf_text_parser import parse_pdf_text
                            structured_data = parse_pdf_text(pdf_text, duplicate_condition['name'])
                            duplicate_condition.update(structured_data)
                            
                            print(f"   ✅ Additional PDF: {len(duplicate_condition.get('medicamentos', []))} medications")
                            print(f"   ✅ Additional PDF: {len(duplicate_condition.get('cid_10', []))} CID-10 codes")
                    else:
                        duplicate_condition['pdf_extracted'] = False
                    
                    # Create custom description
                    duplicate_condition['description'] = scraper.create_custom_description(duplicate_condition)
                    all_conditions.append(duplicate_condition)
            else:
                print("   ❌ No PDFs found")
                all_conditions.append(base_condition)
        
        # Results
        print("\n" + "=" * 50)
        print("📊 Demo Results")
        print("=" * 50)
        print(f"Base conditions: {len(base_conditions)}")
        print(f"Final conditions: {len(all_conditions)}")
        print(f"Additional conditions from multiple PDFs: {len(all_conditions) - len(base_conditions)}")
        print()
        
        # Show detailed results
        for i, condition in enumerate(all_conditions):
            print(f"🏥 Condition {i+1}: {condition['name']}")
            print(f"   📄 PDF: {condition.get('pdf_name', 'No PDF')}")
            print(f"   💊 Medications: {len(condition.get('medicamentos', []))}")
            print(f"   🏷️  CID-10: {len(condition.get('cid_10', []))}")
            
            if condition.get('medicamentos'):
                print(f"   📋 Sample medications: {condition['medicamentos'][:2]}")
            if condition.get('cid_10'):
                print(f"   📋 CID-10 codes: {condition['cid_10']}")
            
            if condition.get('description'):
                desc_preview = condition['description'][:150] + "..." if len(condition['description']) > 150 else condition['description']
                print(f"   📝 Description: {desc_preview}")
            print()
        
        # Save results for inspection
        result_data = {
            'demo_run_at': datetime.now().isoformat(),
            'conditions': all_conditions,
            'total_conditions': len(all_conditions),
            'base_conditions_count': len(base_conditions)
        }
        
        os.makedirs('data', exist_ok=True)
        output_file = f"data/multiple_pdfs_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Demo results saved to: {output_file}")
        print()
        print("✅ Multiple PDF demo completed successfully!")
        
        if len(all_conditions) > len(base_conditions):
            print("🎉 Multiple PDF functionality is working!")
            print(f"   Successfully created {len(all_conditions) - len(base_conditions)} additional condition entries")
            print("   Each PDF was processed separately with its own extracted data")
        
        print("\n💡 Note: The enhanced scraper scripts now automatically add descriptions!")
        print("   No need to run add_descriptions_to_existing_data.py separately")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()