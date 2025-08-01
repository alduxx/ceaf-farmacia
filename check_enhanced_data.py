#!/usr/bin/env python3
"""
Check if the enhanced data with PDF information is available.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import DataManager

def main():
    print("🔍 Checking Enhanced Data Status")
    print("=" * 40)
    
    # Load the latest scraped data
    scraped_data = DataManager.load_latest_scraped_data()
    
    if not scraped_data:
        print("❌ No scraped data found")
        return
    
    conditions = scraped_data.get('conditions', [])
    print(f"📊 Total conditions loaded: {len(conditions)}")
    
    # Check for enhanced features
    pdf_count = 0
    structured_count = 0
    
    for condition in conditions:
        if condition.get('pdf_extracted'):
            pdf_count += 1
        
        if any(condition.get(key) for key in ['cid_10', 'medicamentos', 'documentos_pessoais', 'documentos_medicos', 'exames', 'observacoes']):
            structured_count += 1
    
    print(f"📄 Conditions with PDF data: {pdf_count}")
    print(f"🔧 Conditions with structured data: {structured_count}")
    
    # Show sample condition details
    if conditions:
        sample = conditions[0]
        print(f"\n📋 Sample condition: {sample['name']}")
        print(f"   PDF URL: {'✅' if sample.get('pdf_url') else '❌'}")
        print(f"   PDF Text: {'✅' if sample.get('pdf_text') else '❌'}")
        print(f"   CID-10 codes: {len(sample.get('cid_10', []))}")
        print(f"   Medications: {len(sample.get('medicamentos', []))}")
        print(f"   Personal docs: {len(sample.get('documentos_pessoais', []))}")
        print(f"   Medical docs: {len(sample.get('documentos_medicos', []))}")
        print(f"   Exams: {len(sample.get('exames', []))}")
        print(f"   Observations: {len(sample.get('observacoes', []))}")
    
    print(f"\n💡 Data source: {scraped_data.get('scraped_at', 'Unknown')}")
    
    if pdf_count > 0:
        print("✅ Enhanced data is available!")
    else:
        print("⚠️  No enhanced PDF data found. Run the enhanced scraper:")
        print("   python run_enhanced_scraper.py --limit 5")

if __name__ == "__main__":
    main()