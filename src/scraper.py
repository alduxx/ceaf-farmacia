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
import io
import PyPDF2
import pdfplumber
from llm_processor import LLMProcessor
from pdf_text_parser import parse_pdf_text


class CEAFScraper:
    """Scraper for CEAF clinical conditions and protocols."""
    
    def __init__(self, base_url: str = "https://www.saude.df.gov.br", use_llm: bool = True):
        self.base_url = base_url
        self.target_url = f"{base_url}/protocolos-clinicos-ter-resumos-e-formularios"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM processor if requested
        self.llm_processor = LLMProcessor() if use_llm else None
        
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
    
    def find_condition_pdfs(self, condition_url: str, condition_name: str) -> List[Dict[str, str]]:
        """Find ALL PDF URLs for a specific condition on its page that match the condition name."""
        soup = self.fetch_page(condition_url)
        if not soup:
            return []
        
        pdf_links = []
        
        # Find all PDF links on the page
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if '.pdf' in href.lower():
                pdf_url = urljoin(self.base_url, href)
                pdf_links.append({
                    'url': pdf_url,
                    'text': text,
                    'href': href
                })
        
        if not pdf_links:
            self.logger.warning(f"No PDF links found for {condition_name}")
            return []
        
        # Filter PDFs that match the condition name
        condition_words = set(condition_name.lower().split())
        matching_pdfs = []
        
        for pdf_link in pdf_links:
            pdf_text = pdf_link['text'].lower()
            pdf_href = pdf_link['href'].lower()
            
            # Check if condition words appear in PDF link text or URL
            matches = 0
            for word in condition_words:
                if word in pdf_text or word in pdf_href:
                    matches += 1
            
            score = matches / len(condition_words) if condition_words else 0
            
            # Include PDFs with at least 30% word match
            if score > 0.3:
                pdf_link['match_score'] = score
                matching_pdfs.append(pdf_link)
                self.logger.info(f"Found matching PDF for {condition_name}: {pdf_link['text']} (score: {score:.2f})")
        
        # If no good matches, include the first PDF as fallback
        if not matching_pdfs and pdf_links:
            self.logger.info(f"Using first PDF as fallback for {condition_name}")
            pdf_links[0]['match_score'] = 0.0
            matching_pdfs.append(pdf_links[0])
        
        # Sort by match score (highest first)
        matching_pdfs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matching_pdfs
    
    def find_condition_pdf(self, condition_url: str, condition_name: str) -> Optional[str]:
        """Find the PDF URL for a specific condition on its page (legacy method for compatibility)."""
        pdfs = self.find_condition_pdfs(condition_url, condition_name)
        return pdfs[0]['url'] if pdfs else None
    
    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """Download PDF content from URL."""
        try:
            self.logger.info(f"Downloading PDF from {pdf_url}")
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            if 'application/pdf' not in response.headers.get('Content-Type', ''):
                self.logger.warning(f"URL may not be a PDF: {pdf_url}")
            
            return response.content
        except Exception as e:
            self.logger.error(f"Failed to download PDF from {pdf_url}: {e}")
            return None
    
    def extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            # Try with pdfplumber first (better for tables and formatted text)
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                if text_parts:
                    return '\n\n'.join(text_parts)
            
        except Exception as e:
            self.logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text_parts = []
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                return '\n\n'.join(text_parts) if text_parts else ""
                
            except Exception as e2:
                self.logger.error(f"Both PDF extraction methods failed: {e2}")
                return ""
        
        return ""
    
    def create_custom_description(self, condition: Dict[str, any]) -> str:
        """Create custom description with medications and CID-10 codes."""
        description_parts = []
        
        # Add medications if available
        if condition.get('medicamentos'):
            medications = [med.replace('\uf0b7', '').strip() for med in condition['medicamentos']]
            medications = [med for med in medications if med]  # Remove empty strings
            if medications:
                description_parts.append(', '.join(medications))
        
        # Add CID-10 codes if available
        if condition.get('cid_10'):
            cid_codes = [code.strip() for code in condition['cid_10']]
            cid_codes = [code for code in cid_codes if code]  # Remove empty strings
            if cid_codes:
                description_parts.append(', '.join(cid_codes))
        
        return '\n'.join(description_parts) if description_parts else condition.get('description', '')
    
    def scrape_all_conditions(self, include_details: bool = False, include_pdf_data: bool = False) -> Dict[str, any]:
        """Scrape all clinical conditions and optionally their details."""
        self.logger.info("Starting CEAF conditions scraping...")
        
        # Get the list of conditions
        base_conditions = self.extract_clinical_conditions()
        all_conditions = []
        
        if include_details or include_pdf_data:
            self.logger.info("Extracting detailed information for each condition...")
            for i, base_condition in enumerate(base_conditions):
                self.logger.info(f"Processing condition {i+1}/{len(base_conditions)}: {base_condition['name']}")
                
                # Extract basic details first
                if include_details:
                    details = self.extract_condition_details(base_condition['url'])
                    base_condition.update(details)
                
                if include_pdf_data:
                    # Find ALL PDFs for this condition
                    pdf_links = self.find_condition_pdfs(base_condition['url'], base_condition['name'])
                    
                    if pdf_links:
                        # Process the first PDF and create the base condition
                        first_pdf = pdf_links[0]
                        condition_copy = base_condition.copy()
                        
                        self.logger.info(f"Processing first PDF: {first_pdf['text']}")
                        condition_copy['pdf_url'] = first_pdf['url']
                        condition_copy['pdf_name'] = first_pdf['text']
                        
                        pdf_content = self.download_pdf(first_pdf['url'])
                        if pdf_content:
                            pdf_text = self.extract_pdf_text(pdf_content)
                            condition_copy['pdf_text'] = pdf_text
                            condition_copy['pdf_extracted'] = True
                            
                            # Extract structured data using LLM if available, otherwise use text parser
                            if self.llm_processor and pdf_text.strip():
                                try:
                                    structured_data = self.llm_processor.extract_pdf_structured_data(
                                        pdf_text, condition_copy['name']
                                    )
                                    condition_copy.update(structured_data)
                                except Exception as e:
                                    self.logger.warning(f"LLM extraction failed for {condition_copy['name']}, using text parser: {e}")
                                    # Fallback to text parser
                                    structured_data = parse_pdf_text(pdf_text, condition_copy['name'])
                                    condition_copy.update(structured_data)
                            elif pdf_text.strip():
                                # Use text parser when LLM is not available
                                structured_data = parse_pdf_text(pdf_text, condition_copy['name'])
                                condition_copy.update(structured_data)
                        else:
                            condition_copy['pdf_extracted'] = False
                        
                        # Update description with custom format
                        condition_copy['description'] = self.create_custom_description(condition_copy)
                        all_conditions.append(condition_copy)
                        
                        # Process additional PDFs (if any) by duplicating the condition
                        for additional_pdf in pdf_links[1:]:
                            self.logger.info(f"Processing additional PDF: {additional_pdf['text']}")
                            
                            # Create a duplicate condition without the PDF-extracted data
                            duplicate_condition = base_condition.copy()
                            
                            # Keep basic details but remove PDF-specific data from the first PDF
                            pdf_specific_keys = ['cid_10', 'medicamentos', 'documentos_pessoais', 
                                               'documentos_medicos', 'exames', 'observacoes', 
                                               'extraction_method', 'pdf_text', 'pdf_url', 'pdf_name']
                            for key in pdf_specific_keys:
                                if key in duplicate_condition:
                                    del duplicate_condition[key]
                            
                            # Process the additional PDF
                            duplicate_condition['pdf_url'] = additional_pdf['url']
                            duplicate_condition['pdf_name'] = additional_pdf['text']
                            
                            pdf_content = self.download_pdf(additional_pdf['url'])
                            if pdf_content:
                                pdf_text = self.extract_pdf_text(pdf_content)
                                duplicate_condition['pdf_text'] = pdf_text
                                duplicate_condition['pdf_extracted'] = True
                                
                                # Extract structured data
                                if self.llm_processor and pdf_text.strip():
                                    try:
                                        structured_data = self.llm_processor.extract_pdf_structured_data(
                                            pdf_text, duplicate_condition['name']
                                        )
                                        duplicate_condition.update(structured_data)
                                    except Exception as e:
                                        self.logger.warning(f"LLM extraction failed for additional PDF, using text parser: {e}")
                                        structured_data = parse_pdf_text(pdf_text, duplicate_condition['name'])
                                        duplicate_condition.update(structured_data)
                                elif pdf_text.strip():
                                    structured_data = parse_pdf_text(pdf_text, duplicate_condition['name'])
                                    duplicate_condition.update(structured_data)
                            else:
                                duplicate_condition['pdf_extracted'] = False
                            
                            # Update description with custom format
                            duplicate_condition['description'] = self.create_custom_description(duplicate_condition)
                            all_conditions.append(duplicate_condition)
                            
                            # Brief pause between PDFs
                            time.sleep(1)
                    else:
                        # No PDFs found, add the condition as-is
                        base_condition['pdf_extracted'] = False
                        all_conditions.append(base_condition)
                else:
                    # Not processing PDFs, add the condition as-is
                    all_conditions.append(base_condition)
                
                # Be respectful to the server
                time.sleep(2)
        else:
            # No details or PDF processing, just return the base conditions
            all_conditions = base_conditions
        
        result = {
            'scraped_at': datetime.now().isoformat(),
            'total_conditions': len(all_conditions),
            'base_conditions_count': len(base_conditions),
            'conditions': all_conditions,
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