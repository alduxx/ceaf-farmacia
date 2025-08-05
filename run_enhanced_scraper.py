#!/usr/bin/env python3
"""
Run the enhanced CEAF scraper with PDF processing and LLM integration.
This script will scrape all conditions and extract detailed information from PDFs.
"""

import sys
import os
import argparse
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper

def main():
    parser = argparse.ArgumentParser(description='Enhanced CEAF Scraper with PDF Processing')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Limit number of conditions to process for testing')
    parser.add_argument('--no-pdf', action='store_true', 
                       help='Skip PDF processing (faster, basic data only)')
    parser.add_argument('--no-llm', action='store_true', 
                       help='Skip LLM processing (no structured data extraction)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output filename (default: auto-generated)')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced CEAF Scraper")
    print("=" * 50)
    
    # Configuration
    use_llm = not args.no_llm
    include_pdf_data = not args.no_pdf
    
    print(f"📊 Configuration:")
    print(f"   PDF Processing: {'✅ Enabled' if include_pdf_data else '❌ Disabled'}")
    print(f"   LLM Processing: {'✅ Enabled' if use_llm else '❌ Disabled'}")
    if args.limit:
        print(f"   Condition Limit: {args.limit} (testing mode)")
    print()
    
    try:
        # Initialize scraper
        scraper = CEAFScraper(use_llm=use_llm)
        
        if include_pdf_data:
            print("⚠️  PDF processing enabled - this will take significantly longer!")
            print("   Each condition requires downloading and processing a PDF file.")
            print("   Consider using --limit for testing or --no-pdf for faster basic scraping.")
            
            # Ask for confirmation if processing all conditions
            if not args.limit:
                response = input("\n   Continue with full PDF processing? (y/N): ")
                if response.lower() != 'y':
                    print("   Cancelled by user.")
                    return
        
        print("\n⏳ Starting scraper...")
        
        # Run the scraper
        if args.limit:
            # Limited processing for testing
            print(f"🧪 Testing mode: processing first {args.limit} conditions")
            
            # Get all conditions first
            all_conditions = scraper.extract_clinical_conditions()
            limited_conditions = all_conditions[:args.limit]
            
            # Process each condition
            for i, condition in enumerate(limited_conditions):
                print(f"\n🔍 Processing condition {i+1}/{len(limited_conditions)}: {condition['name']}")
                
                if include_pdf_data:
                    pdf_url = scraper.find_condition_pdf(condition['url'], condition['name'])
                    if pdf_url:
                        condition['pdf_url'] = pdf_url
                        pdf_content = scraper.download_pdf(pdf_url)
                        if pdf_content:
                            pdf_text = scraper.extract_pdf_text(pdf_content)
                            condition['pdf_text'] = pdf_text
                            condition['pdf_extracted'] = True
                            
                            # Extract structured data using LLM if available
                            if scraper.llm_processor and pdf_text.strip():
                                structured_data = scraper.llm_processor.extract_pdf_structured_data(
                                    pdf_text, condition['name']
                                )
                                condition.update(structured_data)
                        else:
                            condition['pdf_extracted'] = False
                    else:
                        condition['pdf_extracted'] = False
                
                # Brief pause between conditions
                import time
                time.sleep(1)
            
            # Create result data
            data = {
                'scraped_at': datetime.now().isoformat(),
                'total_conditions': len(limited_conditions),
                'conditions': limited_conditions,
                'source_url': scraper.target_url,
                'limited_to': args.limit
            }
        else:
            # Full processing
            data = scraper.scrape_all_conditions(
                include_details=True,
                include_pdf_data=include_pdf_data
            )
        
        # Save the data
        if args.output:
            filename = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = "enhanced" if include_pdf_data else "basic"
            filename = f"{prefix}_ceaf_conditions_{timestamp}.json"
        
        filepath = scraper.save_data(data, filename)
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ Scraping completed successfully!")
        print(f"📁 Data saved to: {filepath}")
        print(f"📊 Total conditions: {data['total_conditions']}")
        if data.get('base_conditions_count'):
            print(f"📊 Base conditions: {data['base_conditions_count']}")
            additional_count = data['total_conditions'] - data['base_conditions_count']
            if additional_count > 0:
                print(f"📑 Additional conditions from multiple PDFs: {additional_count}")
        
        if include_pdf_data:
            pdf_success = sum(1 for c in data['conditions'] if c.get('pdf_extracted'))
            print(f"📄 PDF processing: {pdf_success}/{data['total_conditions']} successful")
            
            if use_llm:
                llm_success = sum(1 for c in data['conditions'] 
                                if c.get('extraction_method') == 'llm')
                print(f"🧠 LLM processing: {llm_success}/{data['total_conditions']} successful")
        
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
        print("   2. Test search functionality - descriptions will appear below condition names")
        print("   3. Check condition detail pages for enhanced information")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()