#!/usr/bin/env python3
"""
Debug script to troubleshoot scraping issues.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import requests
from bs4 import BeautifulSoup
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_scraping():
    """Debug the scraping process step by step."""
    
    url = "https://www.saude.df.gov.br/protocolos-clinicos-ter-resumos-e-formularios"
    
    print("="*60)
    print("DEBUGGING CEAF SCRAPER")
    print("="*60)
    
    # Step 1: Test basic connection
    print("\n1. Testing connection to website...")
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.content)} bytes")
        print(f"   Encoding: {response.encoding}")
        
        if response.status_code != 200:
            print(f"   ERROR: Failed to fetch page. Status: {response.status_code}")
            return
            
    except Exception as e:
        print(f"   ERROR: Connection failed: {e}")
        return
    
    # Step 2: Parse HTML
    print("\n2. Parsing HTML...")
    try:
        soup = BeautifulSoup(response.content, 'lxml')
        print(f"   Successfully parsed HTML")
        
        # Save raw HTML for inspection
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"   Raw HTML saved to debug_page.html")
        
    except Exception as e:
        print(f"   ERROR: HTML parsing failed: {e}")
        return
    
    # Step 3: Look for CEAF section
    print("\n3. Looking for CEAF section...")
    ceaf_keywords = [
        "Condições Clínicas atendidas no Componente Especializado",
        "CEAF",
        "Componente Especializado da Assistência Farmacêutica"
    ]
    
    ceaf_found = False
    for element in soup.find_all(text=True):
        element_text = element.strip()
        if any(keyword in element_text for keyword in ceaf_keywords):
            print(f"   FOUND CEAF marker: '{element_text}'")
            ceaf_found = True
            
            # Find the parent element
            parent = element.parent
            if parent:
                print(f"   Parent element: {parent.name}")
                print(f"   Parent class: {parent.get('class', 'No class')}")
    
    if not ceaf_found:
        print("   WARNING: CEAF section not found")
    
    # Step 4: Find all links
    print("\n4. Analyzing all links...")
    all_links = soup.find_all('a', href=True)
    print(f"   Total links found: {len(all_links)}")
    
    # Step 5: Look for start/end markers
    print("\n5. Looking for range markers...")
    acne_links = []
    uveites_links = []
    
    for i, link in enumerate(all_links):
        text = link.get_text(strip=True)
        
        if text and 'acne' in text.lower() and 'grave' in text.lower():
            acne_links.append((i, text, link.get('href', '')))
            print(f"   ACNE MARKER at position {i}: '{text}' -> {link.get('href', '')}")
        
        if text and 'uveítes' in text.lower():
            uveites_links.append((i, text, link.get('href', '')))
            print(f"   UVEITES MARKER at position {i}: '{text}' -> {link.get('href', '')}")
    
    if not acne_links:
        print("   ERROR: 'Acne Grave' not found!")
        return
    
    if not uveites_links:
        print("   ERROR: 'Uveítes' not found!")
        return
    
    # Step 6: Extract conditions in range
    print("\n6. Extracting conditions in range...")
    start_pos = acne_links[0][0]  # Position of first Acne Grave
    end_pos = uveites_links[0][0]  # Position of first Uveites
    
    print(f"   Range: positions {start_pos} to {end_pos}")
    
    conditions_in_range = []
    for i in range(start_pos, end_pos + 1):
        link = all_links[i]
        text = link.get_text(strip=True)
        href = link.get('href', '')
        
        if text and len(text) > 2:
            # Apply same filtering as in scraper
            if (not any(skip_word in text.lower() for skip_word in 
                       ['download', 'voltar', 'início', 'home', 'menu', 'buscar', 'pesquisar']) and
                not text.lower().startswith('http') and
                len(text) < 100):
                
                conditions_in_range.append({
                    'position': i,
                    'name': text,
                    'href': href
                })
    
    print(f"   Found {len(conditions_in_range)} conditions in range")
    
    # Step 7: Display results
    print("\n7. CONDITIONS FOUND:")
    print("-" * 40)
    for i, condition in enumerate(conditions_in_range):
        print(f"{i+1:2d}. {condition['name']}")
        if i == 0 or i == len(conditions_in_range) - 1:
            print(f"     URL: {condition['href']}")
            print(f"     Position: {condition['position']}")
    
    if len(conditions_in_range) > 10:
        print(f"\n    ... (showing first and last, total: {len(conditions_in_range)})")
    
    # Step 8: Save debug info
    print(f"\n8. Saving debug information...")
    debug_info = {
        'total_links': len(all_links),
        'acne_positions': acne_links,
        'uveites_positions': uveites_links,
        'range_start': start_pos,
        'range_end': end_pos,
        'conditions_found': len(conditions_in_range),
        'conditions': conditions_in_range
    }
    
    import json
    with open('debug_info.json', 'w', encoding='utf-8') as f:
        json.dump(debug_info, f, ensure_ascii=False, indent=2)
    
    print(f"   Debug info saved to debug_info.json")
    print(f"   Raw HTML saved to debug_page.html")
    
    print("\n" + "="*60)
    print(f"SUMMARY: Found {len(conditions_in_range)} conditions")
    print("="*60)

if __name__ == "__main__":
    debug_scraping()