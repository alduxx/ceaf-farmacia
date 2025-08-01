#!/usr/bin/env python3
"""
Apply text parser to existing PDF data to extract structured information.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_text_parser import parse_pdf_text

def main():
    print("🔧 Applying Text Parser to Enhanced Data")
    print("=" * 45)
    
    # Find the latest enhanced data file
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.startswith('enhanced_ceaf_conditions_') and f.endswith('.json')]
    
    if not files:
        print("❌ No enhanced data files found")
        return
    
    latest_file = sorted(files)[-1]
    filepath = os.path.join(data_dir, latest_file)
    
    print(f"📂 Processing file: {latest_file}")
    
    # Load data
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conditions = data.get('conditions', [])
    print(f"📋 Found {len(conditions)} conditions")
    
    # Apply text parser to each condition with PDF text
    updated_count = 0
    for i, condition in enumerate(conditions):
        if condition.get('pdf_text'):
            print(f"🔍 Processing {i+1}/{len(conditions)}: {condition['name']}")
            
            # Parse the PDF text
            parsed_data = parse_pdf_text(condition['pdf_text'], condition['name'])
            
            # Update condition with parsed data
            condition.update(parsed_data)
            updated_count += 1
            
            print(f"   ✅ Extracted: {len(parsed_data['cid_10'])} CID-10, {len(parsed_data['medicamentos'])} medications")
    
    # Update timestamp
    data['processed_at'] = datetime.now().isoformat()
    data['text_parser_applied'] = True
    
    # Save updated data
    output_filename = f"enhanced_parsed_ceaf_conditions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_filepath = os.path.join(data_dir, output_filename)
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Processing completed!")
    print(f"📁 Updated data saved to: {output_filepath}")
    print(f"🔧 Applied text parser to {updated_count} conditions")
    
    # Show sample results
    if conditions and conditions[0].get('cid_10'):
        sample = conditions[0]
        print(f"\n📊 Sample results for '{sample['name']}':")
        print(f"   CID-10: {sample.get('cid_10', [])}")
        print(f"   Medications: {sample.get('medicamentos', [])[:2]}...")
        print(f"   Personal docs: {len(sample.get('documentos_pessoais', []))} items")
        print(f"   Medical docs: {len(sample.get('documentos_medicos', []))} items")
        print(f"   Exams: {len(sample.get('exames', []))} items")
        print(f"   Observations: {len(sample.get('observacoes', []))} items")

if __name__ == "__main__":
    main()