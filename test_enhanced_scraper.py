#!/usr/bin/env python3
"""
Test script for the enhanced CEAF scraper with PDF processing and LLM integration.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import CEAFScraper
from llm_processor import LLMProcessor

def test_pdf_extraction():
    """Test PDF extraction functionality with a small sample."""
    print("🧪 Testing PDF extraction functionality...")
    
    try:
        # Initialize scraper with LLM processing
        scraper = CEAFScraper(use_llm=True)
        
        # Get the first few conditions for testing
        conditions = scraper.extract_clinical_conditions()
        
        if not conditions:
            print("❌ No conditions found. Check your internet connection.")
            return False
        
        print(f"📋 Found {len(conditions)} total conditions")
        
        # Test with first 2 conditions to avoid long processing time
        test_conditions = conditions[:2]
        
        for i, condition in enumerate(test_conditions):
            print(f"\n🔍 Testing condition {i+1}/2: {condition['name']}")
            
            # Find PDF for this condition
            pdf_url = scraper.find_condition_pdf(condition['url'], condition['name'])
            
            if pdf_url:
                print(f"📄 Found PDF: {pdf_url}")
                
                # Download and extract PDF text
                pdf_content = scraper.download_pdf(pdf_url)
                if pdf_content:
                    pdf_text = scraper.extract_pdf_text(pdf_content)
                    
                    if pdf_text.strip():
                        print(f"✅ Successfully extracted text ({len(pdf_text)} chars)")
                        
                        # Test LLM extraction if available
                        if scraper.llm_processor:
                            structured_data = scraper.llm_processor.extract_pdf_structured_data(
                                pdf_text, condition['name']
                            )
                            
                            print("📊 LLM Extraction Results:")
                            print(f"   CID-10: {len(structured_data.get('cid_10', []))} codes")
                            print(f"   Medications: {len(structured_data.get('medicamentos', []))} items")
                            print(f"   Personal docs: {len(structured_data.get('documentos_pessoais', []))} items")
                            print(f"   Medical docs: {len(structured_data.get('documentos_medicos', []))} items")
                            print(f"   Exams: {len(structured_data.get('exames', []))} items")
                            print(f"   Observations: {len(structured_data.get('observacoes', []))} items")
                        else:
                            print("⚠️  LLM processor not available")
                    else:
                        print("❌ Failed to extract text from PDF")
                else:
                    print("❌ Failed to download PDF")
            else:
                print("❌ No PDF found for this condition")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_full_workflow():
    """Test the complete workflow with PDF data extraction."""
    print("\n🔄 Testing full workflow with PDF data extraction...")
    
    try:
        scraper = CEAFScraper(use_llm=True)
        
        # Run with PDF data extraction for first condition only
        print("⏳ Running scraper with PDF data extraction (limited to 1 condition)...")
        
        # Get just one condition for testing
        all_conditions = scraper.extract_clinical_conditions()
        if not all_conditions:
            print("❌ No conditions found")
            return False
        
        # Manually process one condition with PDF data
        test_condition = all_conditions[0].copy()
        print(f"🎯 Testing with condition: {test_condition['name']}")
        
        # Extract PDF data for this condition
        pdf_url = scraper.find_condition_pdf(test_condition['url'], test_condition['name'])
        if pdf_url:
            test_condition['pdf_url'] = pdf_url
            pdf_content = scraper.download_pdf(pdf_url)
            if pdf_content:
                pdf_text = scraper.extract_pdf_text(pdf_content)
                test_condition['pdf_text'] = pdf_text
                test_condition['pdf_extracted'] = True
                
                # Extract structured data using LLM if available
                if scraper.llm_processor and pdf_text.strip():
                    structured_data = scraper.llm_processor.extract_pdf_structured_data(
                        pdf_text, test_condition['name']
                    )
                    test_condition.update(structured_data)
        
        # Save test results
        result = {
            'scraped_at': datetime.now().isoformat(),
            'total_conditions': 1,
            'conditions': [test_condition],
            'source_url': scraper.target_url,
            'test_mode': True
        }
        
        # Save to test file
        test_filename = f"test_enhanced_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_filepath = os.path.join('data', test_filename)
        
        os.makedirs('data', exist_ok=True)
        with open(test_filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Test data saved to: {test_filepath}")
        
        # Display results
        condition = result['conditions'][0]
        print(f"\n📊 Test Results for '{condition['name']}':")
        print(f"   PDF URL: {'✅' if condition.get('pdf_url') else '❌'}")
        
        # Fix f-string syntax by using separate variables
        pdf_text = condition.get('pdf_text', '')
        pdf_status = f"✅ ({len(pdf_text)} chars)" if pdf_text else "❌"
        print(f"   PDF Text: {pdf_status}")
        
        print(f"   CID-10 codes: {len(condition.get('cid_10', []))}")
        print(f"   Medications: {len(condition.get('medicamentos', []))}")
        print(f"   Personal documents: {len(condition.get('documentos_pessoais', []))}")
        print(f"   Medical documents: {len(condition.get('documentos_medicos', []))}")
        print(f"   Required exams: {len(condition.get('exames', []))}")
        print(f"   Observations: {len(condition.get('observacoes', []))}")
        
        # Show sample data if available
        if condition.get('medicamentos'):
            print(f"\n💊 Sample medications: {condition['medicamentos'][:3]}")
        if condition.get('cid_10'):
            print(f"🏷️  Sample CID-10: {condition['cid_10'][:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Enhanced CEAF Scraper Tests")
    print("=" * 50)
    
    # Test 1: PDF extraction functionality
    pdf_test_success = test_pdf_extraction()
    
    # Test 2: Full workflow
    workflow_test_success = test_full_workflow()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   PDF Extraction: {'✅ PASSED' if pdf_test_success else '❌ FAILED'}")
    print(f"   Full Workflow: {'✅ PASSED' if workflow_test_success else '❌ FAILED'}")
    
    if pdf_test_success and workflow_test_success:
        print("\n🎉 All tests passed! The enhanced scraper is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
    
    print("\n💡 Next steps:")
    print("   1. Run the full scraper with: python -m src.scraper")
    print("   2. Start the web application with: python run.py")
    print("   3. Test the new search functionality in the web interface")

if __name__ == "__main__":
    main()