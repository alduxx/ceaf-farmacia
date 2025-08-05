#!/usr/bin/env python3
"""
Run the enhanced scraper for all conditions with proper text parsing.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper
from datetime import datetime

def main():
    print("🚀 Running Full Enhanced CEAF Scraper")
    print("=" * 45)
    print("⚠️  This will process all 97 conditions with PDF extraction.")
    print("   Estimated time: 3-5 minutes")
    print("   Each condition requires downloading and processing a PDF file.")
    
    response = input("\n   Continue with full processing? (y/N): ")
    if response.lower() != 'y':
        print("   Cancelled by user.")
        return
    
    try:
        # Initialize scraper with LLM enabled (will fallback to text parser)
        scraper = CEAFScraper(use_llm=True)
        
        print("\n⏳ Starting full scraper with PDF data extraction...")
        print("   This may take several minutes...")
        
        # Run the full scraper
        data = scraper.scrape_all_conditions(
            include_details=True,
            include_pdf_data=True
        )
        
        # Save the data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_enhanced_ceaf_conditions_{timestamp}.json"
        filepath = scraper.save_data(data, filename)
        
        # Summary
        print("\n" + "=" * 45)
        print("✅ Full scraping completed successfully!")
        print(f"📁 Data saved to: {filepath}")
        print(f"📊 Total conditions: {data['total_conditions']}")
        if data.get('base_conditions_count'):
            print(f"📊 Base conditions: {data['base_conditions_count']}")
            additional_count = data['total_conditions'] - data['base_conditions_count']
            if additional_count > 0:
                print(f"📑 Additional conditions from multiple PDFs: {additional_count}")
        
        pdf_success = sum(1 for c in data['conditions'] if c.get('pdf_extracted'))
        print(f"📄 PDF processing: {pdf_success}/{data['total_conditions']} successful")
        
        structured_success = sum(1 for c in data['conditions'] 
                               if c.get('extraction_method') == 'text_parser')
        print(f"🔧 Text parsing: {structured_success}/{data['total_conditions']} successful")
        
        # Show sample of extracted data types
        sample_with_data = [c for c in data['conditions'] if c.get('cid_10') or c.get('medicamentos')]
        if sample_with_data:
            print(f"🎯 Conditions with structured data: {len(sample_with_data)}")
            
            sample = sample_with_data[0]
            print(f"\n📋 Sample: {sample['name']}")
            print(f"   CID-10: {len(sample.get('cid_10', []))} codes")
            print(f"   Medications: {len(sample.get('medicamentos', []))} items")
            print(f"   Documents: {len(sample.get('documentos_pessoais', []))} + {len(sample.get('documentos_medicos', []))} items")
            print(f"   Exams: {len(sample.get('exames', []))} items")
        
        # Automatically add descriptions to the scraped data
        print("\n🔧 Adding custom descriptions to scraped data...")
        try:
            # Import here to avoid circular imports
            import json
            
            # Load the data we just saved
            with open(filepath, 'r', encoding='utf-8') as f:
                data_with_descriptions = json.load(f)
            
            # Add descriptions to conditions that don't have them
            updated_count = 0
            for condition in data_with_descriptions.get('conditions', []):
                existing_desc = condition.get('description', '')
                
                # Only add description if it doesn't exist or is empty
                if not existing_desc or existing_desc.strip() == '':
                    new_description = scraper.create_custom_description(condition)
                    
                    if new_description and new_description != existing_desc:
                        condition['description'] = new_description
                        updated_count += 1
            
            # Update metadata
            data_with_descriptions['descriptions_added_at'] = datetime.now().isoformat()
            data_with_descriptions['descriptions_updated_count'] = updated_count
            
            # Save the updated data back to the same file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_with_descriptions, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Added descriptions to {updated_count} conditions")
            
            # Show sample description if any were added
            if updated_count > 0:
                conditions_with_descriptions = [c for c in data_with_descriptions['conditions'] if c.get('description')]
                if conditions_with_descriptions:
                    sample = conditions_with_descriptions[0]
                    print(f"📋 Sample description for '{sample['name']}':")
                    desc_lines = sample['description'].split('\n')
                    for i, line in enumerate(desc_lines):
                        if line.strip():
                            label = "Medications" if i == 0 else "CID-10" if i == 1 else f"Line {i+1}"
                            print(f"   {label}: {line.strip()}")
            
        except Exception as desc_error:
            print(f"⚠️  Failed to add descriptions: {desc_error}")
            print("   You can add them manually later with: python add_descriptions_to_existing_data.py")
        
        print("\n💡 Next steps:")
        print("   1. Start the web application: python run.py")
        print("   2. Test enhanced search functionality - descriptions will appear below condition names")
        print("   3. Browse condition detail pages with full information")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()