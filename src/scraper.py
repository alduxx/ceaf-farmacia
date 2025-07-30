"""
Web scraper for CEAF clinical conditions from DF government website.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime


class CEAFScraper:
    """Scraper for CEAF clinical conditions and protocols."""
    
    def __init__(self, base_url: str = "https://www.saude.df.gov.br"):
        self.base_url = base_url
        self.target_url = f"{base_url}/protocolos-clinicos-ter-resumos-e-formularios"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retry logic."""
        for attempt in range(retries):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.content, 'lxml')
                return soup
                
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def extract_clinical_conditions(self) -> List[Dict[str, str]]:
        """Extract the list of clinical conditions from the main page."""
        soup = self.fetch_page(self.target_url)
        if not soup:
            return []
        
        conditions = []
        
        # Look for the CEAF section specifically
        # Find the section header first
        ceaf_section_found = False
        ceaf_header_keywords = [
            "Condições Clínicas atendidas no Componente Especializado",
            "CEAF",
            "Componente Especializado da Assistência Farmacêutica"
        ]
        
        # Find all text elements that might contain the CEAF section header
        for element in soup.find_all(text=True):
            if any(keyword in element for keyword in ceaf_header_keywords):
                ceaf_section_found = True
                self.logger.info(f"Found CEAF section marker: {element.strip()}")
                break
        
        if not ceaf_section_found:
            self.logger.warning("Could not find CEAF section header, using fallback method")
        
        # Get all links from the page
        all_links = soup.find_all('a', href=True)
        
        # Find the range between "Acne Grave" and "Uveítes" 
        start_collecting = False
        acne_found = False
        
        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Start collecting when we find "Acne Grave"
            if not acne_found and text and 'acne' in text.lower() and 'grave' in text.lower():
                acne_found = True
                start_collecting = True
                self.logger.info(f"Found start marker: {text}")
            
            # Stop collecting when we find "Uveítes"
            if start_collecting and text and 'uveítes' in text.lower():
                # Include this last condition
                if text and len(text) > 2:
                    full_url = urljoin(self.base_url, href)
                    conditions.append({
                        'name': text,
                        'url': full_url,
                        'scraped_at': datetime.now().isoformat()
                    })
                self.logger.info(f"Found end marker: {text}")
                break
            
            # Collect conditions in the range
            if start_collecting and text and len(text) > 2:
                # Additional filtering to ensure we're getting medical conditions
                # Skip navigation links, downloads, etc.
                if (not any(skip_word in text.lower() for skip_word in 
                           ['download', 'voltar', 'início', 'home', 'menu', 'buscar', 'pesquisar']) and
                    not text.lower().startswith('http') and
                    len(text) < 100):  # Medical condition names shouldn't be too long
                    
                    full_url = urljoin(self.base_url, href)
                    conditions.append({
                        'name': text,
                        'url': full_url,
                        'scraped_at': datetime.now().isoformat()
                    })
        
        # If we didn't find the range, try a fallback approach
        if not conditions and acne_found:
            self.logger.warning("Range method failed, trying pattern-based fallback")
            for link in all_links:
                text = link.get_text(strip=True)
                href = link.get('href', '').lower()
                
                # Look for links that seem like medical conditions
                if (text and len(text) > 3 and len(text) < 100 and
                    # Must contain medical/protocol keywords in URL
                    any(keyword in href for keyword in ['protocolo', 'pcdt', 'diretriz']) and
                    # Skip obvious navigation elements
                    not any(skip_word in text.lower() for skip_word in 
                           ['download', 'voltar', 'início', 'home', 'menu', 'buscar'])):
                    
                    full_url = urljoin(self.base_url, href)
                    conditions.append({
                        'name': text,
                        'url': full_url,
                        'scraped_at': datetime.now().isoformat()
                    })
        
        # Remove duplicates based on name
        unique_conditions = []
        seen_names = set()
        for condition in conditions:
            if condition['name'] not in seen_names:
                unique_conditions.append(condition)
                seen_names.add(condition['name'])
        
        self.logger.info(f"Found {len(unique_conditions)} unique clinical conditions")
        
        # Log first few conditions for debugging
        if unique_conditions:
            self.logger.info("First few conditions found:")
            for i, condition in enumerate(unique_conditions[:5]):
                self.logger.info(f"  {i+1}. {condition['name']}")
        
        return unique_conditions
    
    def extract_condition_details(self, condition_url: str) -> Dict[str, any]:
        """Extract detailed information from a specific condition page."""
        soup = self.fetch_page(condition_url)
        if not soup:
            return {}
        
        details = {
            'url': condition_url,
            'title': '',
            'description': '',
            'protocols': [],
            'requirements': [],
            'documents': []
        }
        
        # Extract title
        title_selectors = ['h1', 'h2', '.page-title', '.entry-title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                details['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract main content
        content_selectors = ['.content', '.entry-content', '.post-content', 'main', 'article']
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Extract text content
                paragraphs = content_elem.find_all(['p', 'div', 'li'])
                description_parts = []
                for p in paragraphs[:5]:  # Limit to first 5 paragraphs
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        description_parts.append(text)
                
                details['description'] = ' '.join(description_parts)
                break
        
        # Extract downloadable documents
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx']):
                details['documents'].append({
                    'name': text,
                    'url': urljoin(self.base_url, href)
                })
        
        return details
    
    def scrape_all_conditions(self, include_details: bool = False) -> Dict[str, any]:
        """Scrape all clinical conditions and optionally their details."""
        self.logger.info("Starting CEAF conditions scraping...")
        
        # Get the list of conditions
        conditions = self.extract_clinical_conditions()
        
        if include_details:
            self.logger.info("Extracting detailed information for each condition...")
            for i, condition in enumerate(conditions):
                self.logger.info(f"Processing condition {i+1}/{len(conditions)}: {condition['name']}")
                
                details = self.extract_condition_details(condition['url'])
                condition.update(details)
                
                # Be respectful to the server
                time.sleep(1)
        
        result = {
            'scraped_at': datetime.now().isoformat(),
            'total_conditions': len(conditions),
            'conditions': conditions,
            'source_url': self.target_url
        }
        
        return result
    
    def save_data(self, data: Dict[str, any], filename: str = None) -> str:
        """Save scraped data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ceaf_conditions_{timestamp}.json"
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Data saved to {filepath}")
        return filepath


def main():
    """Main function to run the scraper."""
    scraper = CEAFScraper()
    
    # Scrape basic condition list
    data = scraper.scrape_all_conditions(include_details=False)
    
    # Save the data
    filepath = scraper.save_data(data)
    
    print(f"Scraping completed!")
    print(f"Found {data['total_conditions']} clinical conditions")
    print(f"Data saved to: {filepath}")
    
    # Display first few conditions
    print("\nFirst 5 conditions found:")
    for i, condition in enumerate(data['conditions'][:5]):
        print(f"{i+1}. {condition['name']}")


if __name__ == "__main__":
    main()