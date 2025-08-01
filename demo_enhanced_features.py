#!/usr/bin/env python3
"""
Demo script showing the enhanced CEAF Farmácia features.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import DataManager

def main():
    print("🎯 CEAF Farmácia Enhanced Features Demo")
    print("=" * 45)
    
    # Load the latest data
    scraped_data = DataManager.load_latest_scraped_data()
    
    if not scraped_data:
        print("❌ No data found. Run the enhanced scraper first:")
        print("   python run_enhanced_scraper.py --limit 5")
        return
    
    conditions = scraped_data.get('conditions', [])
    print(f"📊 Total conditions: {len(conditions)}")
    
    # Find conditions with structured data
    enhanced_conditions = [c for c in conditions if c.get('cid_10') or c.get('medicamentos')]
    print(f"🔧 Enhanced conditions: {len(enhanced_conditions)}")
    
    if not enhanced_conditions:
        print("⚠️  No enhanced data found. Apply text parser:")
        print("   python apply_text_parser.py")
        return
    
    # Demo each enhanced condition
    for i, condition in enumerate(enhanced_conditions):
        print(f"\n🏥 Condition {i+1}: {condition['name']}")
        print("=" * (15 + len(condition['name'])))
        
        # CID-10 codes
        if condition.get('cid_10'):
            print(f"🏷️  CID-10 Codes: {', '.join(condition['cid_10'])}")
        
        # Medications
        if condition.get('medicamentos'):
            print(f"💊 Medications ({len(condition['medicamentos'])}):")
            for med in condition['medicamentos'][:3]:  # Show first 3
                clean_med = med.replace('\uf0b7', '•').strip()  # Clean bullet points
                print(f"   • {clean_med}")
            if len(condition['medicamentos']) > 3:
                print(f"   ... and {len(condition['medicamentos']) - 3} more")
        
        # Personal documents
        if condition.get('documentos_pessoais'):
            print(f"📄 Personal Documents ({len(condition['documentos_pessoais'])}):")
            for doc in condition['documentos_pessoais']:
                clean_doc = doc.replace('\uf0b7', '•').strip()
                print(f"   • {clean_doc}")
        
        # Medical documents
        if condition.get('documentos_medicos'):
            print(f"👩‍⚕️ Medical Documents ({len(condition['documentos_medicos'])}):")
            for doc in condition['documentos_medicos'][:2]:  # Show first 2
                clean_doc = doc.replace('\uf0b7', '•').strip()
                print(f"   • {clean_doc}")
            if len(condition['documentos_medicos']) > 2:
                print(f"   ... and {len(condition['documentos_medicos']) - 2} more")
        
        # Required exams
        if condition.get('exames'):
            print(f"🔬 Required Exams ({len(condition['exames'])}):")
            for exam in condition['exames'][:2]:  # Show first 2
                clean_exam = exam.replace('\uf0b7', '•').strip()
                print(f"   • {clean_exam}")
            if len(condition['exames']) > 2:
                print(f"   ... and {len(condition['exames']) - 2} more")
        
        # Observations
        if condition.get('observacoes'):
            print(f"⚠️  Important Notes ({len(condition['observacoes'])}):")
            for obs in condition['observacoes'][:1]:  # Show first one
                clean_obs = obs.replace('\uf0b7', '•').strip()
                print(f"   • {clean_obs}")
            if len(condition['observacoes']) > 1:
                print(f"   ... and {len(condition['observacoes']) - 1} more")
        
        # PDF info
        if condition.get('pdf_url'):
            print(f"📎 PDF: Available ({len(condition.get('pdf_text', ''))} chars)")
    
    print(f"\n🎉 Demo completed!")
    print(f"🔗 View in web interface: http://127.0.0.1:5000")
    print(f"💡 Try searching by:")
    print(f"   • Condition name: 'acne'")
    print(f"   • Medication: 'isotretinoína'")
    print(f"   • CID-10 code: 'L70'")

if __name__ == "__main__":
    main()