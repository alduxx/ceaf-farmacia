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
        
        print("\n💡 Next steps:")
        print("   1. Start the web application: python run.py")
        print("   2. Test enhanced search functionality")
        print("   3. Browse condition detail pages with full information")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()