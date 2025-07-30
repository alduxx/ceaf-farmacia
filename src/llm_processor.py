"""
LLM integration for processing and simplifying CEAF clinical conditions data.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic not available. Install with: pip install anthropic")


class LLMProcessor:
    """Process CEAF data using Large Language Models to make it more patient-friendly."""
    
    def __init__(self, provider: str = "anthropic"):
        self.provider = provider.lower()
        self.logger = logging.getLogger(__name__)
        
        # Initialize the selected LLM client
        if self.provider == "openai" and OPENAI_AVAILABLE:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.client = openai.OpenAI()
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.logger.warning(f"LLM provider '{provider}' not available or not configured")
            self.client = None
    
    def process_condition_list(self, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process the list of clinical conditions to make them more patient-friendly."""
        if not self.client:
            return self._fallback_processing(conditions)
        
        # Create a summary of all conditions
        condition_names = [c['name'] for c in conditions]
        
        prompt = f"""
        You are helping patients understand medical conditions covered by Brazil's CEAF (Specialized Component of Pharmaceutical Assistance) program.
        
        Here is a list of {len(condition_names)} clinical conditions covered by the program:
        {', '.join(condition_names)}
        
        Please:
        1. Organize these conditions into logical categories (e.g., Autoimmune, Neurological, Endocrine, etc.)
        2. For each category, provide a brief, patient-friendly explanation
        3. Identify the most common conditions that patients might be looking for
        4. Create simple, non-medical language explanations for complex terms
        
        Format your response as JSON with the following structure:
        {{
            "categories": {{
                "category_name": {{
                    "description": "Patient-friendly description",
                    "conditions": ["condition1", "condition2"]
                }}
            }},
            "common_conditions": ["list of most common conditions"],
            "glossary": {{
                "technical_term": "simple_explanation"
            }}
        }}
        """
        
        try:
            response = self._call_llm(prompt)
            
            # Try to parse JSON response
            try:
                processed_data = json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response
                processed_data = {
                    "raw_response": response,
                    "categories": {},
                    "common_conditions": condition_names[:10],  # First 10 as fallback
                    "glossary": {}
                }
            
            processed_data.update({
                "processed_at": datetime.now().isoformat(),
                "total_conditions": len(conditions),
                "original_conditions": conditions
            })
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"LLM processing failed: {e}")
            return self._fallback_processing(conditions)
    
    def explain_condition(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a patient-friendly explanation for a specific condition."""
        if not self.client:
            return self._fallback_condition_explanation(condition)
        
        condition_name = condition.get('name', '')
        condition_description = condition.get('description', '')
        
        prompt = f"""
        You are helping a patient understand a medical condition covered by Brazil's CEAF program.
        
        Condition: {condition_name}
        Technical Description: {condition_description}
        
        Please provide a patient-friendly explanation that includes:
        1. What this condition is in simple terms
        2. Common symptoms patients might experience
        3. Why this condition qualifies for specialized medication assistance
        4. What patients should know about treatment access
        5. Encouraging, supportive tone while being informative
        
        Write in Portuguese (Brazilian) and use simple, accessible language.
        Avoid medical jargon and explain any necessary technical terms.
        """
        
        try:
            explanation = self._call_llm(prompt)
            
            return {
                "condition": condition_name,
                "patient_friendly_explanation": explanation,
                "processed_at": datetime.now().isoformat(),
                "original_data": condition
            }
            
        except Exception as e:
            self.logger.error(f"Failed to explain condition {condition_name}: {e}")
            return self._fallback_condition_explanation(condition)
    
    def create_search_keywords(self, conditions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate search keywords for each condition to improve findability."""
        if not self.client:
            return self._fallback_search_keywords(conditions)
        
        keywords_map = {}
        
        for condition in conditions:
            condition_name = condition.get('name', '')
            
            prompt = f"""
            Generate search keywords for the medical condition: {condition_name}
            
            Provide keywords that patients might use when searching, including:
            - Common names and alternative names
            - Symptoms they might describe
            - Related terms in Portuguese
            - Simplified versions of the condition name
            
            Return only a comma-separated list of keywords, no explanations.
            """
            
            try:
                response = self._call_llm(prompt)
                keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
                keywords_map[condition_name] = keywords
                
            except Exception as e:
                self.logger.error(f"Failed to generate keywords for {condition_name}: {e}")
                keywords_map[condition_name] = [condition_name.lower()]
        
        return keywords_map
    
    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the given prompt."""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            return response.choices[0].message.content
            
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _fallback_processing(self, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback processing when LLM is not available."""
        self.logger.info("Using fallback processing (no LLM)")
        
        # Basic categorization based on keywords
        categories = {
            "autoimmune": {"description": "Condições onde o sistema imunológico ataca o próprio corpo", "conditions": []},
            "neurological": {"description": "Condições que afetam o sistema nervoso", "conditions": []},
            "endocrine": {"description": "Condições relacionadas aos hormônios", "conditions": []},
            "other": {"description": "Outras condições clínicas", "conditions": []}
        }
        
        autoimmune_keywords = ["artrite", "lupus", "esclerose", "psorias"]
        neuro_keywords = ["epilepsia", "parkinson", "alzheimer", "esclerose"]
        endo_keywords = ["diabetes", "tireoid", "hormonal"]
        
        for condition in conditions:
            name_lower = condition['name'].lower()
            categorized = False
            
            if any(kw in name_lower for kw in autoimmune_keywords):
                categories["autoimmune"]["conditions"].append(condition['name'])
                categorized = True
            elif any(kw in name_lower for kw in neuro_keywords):
                categories["neurological"]["conditions"].append(condition['name'])
                categorized = True
            elif any(kw in name_lower for kw in endo_keywords):
                categories["endocrine"]["conditions"].append(condition['name'])
                categorized = True
            
            if not categorized:
                categories["other"]["conditions"].append(condition['name'])
        
        return {
            "categories": categories,
            "common_conditions": [c['name'] for c in conditions[:10]],
            "glossary": {
                "CEAF": "Componente Especializado da Assistência Farmacêutica - programa para medicamentos de alto custo",
                "Protocolo Clínico": "Documento que define critérios para tratamento de uma condição"
            },
            "processed_at": datetime.now().isoformat(),
            "total_conditions": len(conditions),
            "processing_method": "fallback"
        }
    
    def _fallback_condition_explanation(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback explanation when LLM is not available."""
        return {
            "condition": condition.get('name', ''),
            "patient_friendly_explanation": f"Esta é uma condição médica coberta pelo programa CEAF. Para mais informações específicas, consulte um profissional de saúde ou acesse: {condition.get('url', '')}",
            "processed_at": datetime.now().isoformat(),
            "processing_method": "fallback",
            "original_data": condition
        }
    
    def _fallback_search_keywords(self, conditions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Fallback keyword generation when LLM is not available."""
        keywords_map = {}
        for condition in conditions:
            name = condition.get('name', '')
            # Simple keyword generation: split name and add lowercase version
            keywords = [name.lower(), name]
            if ' ' in name:
                keywords.extend(name.lower().split())
            keywords_map[name] = list(set(keywords))  # Remove duplicates
        return keywords_map


def main():
    """Test the LLM processor with sample data."""
    # Load sample data
    data_files = [f for f in os.listdir('data') if f.startswith('ceaf_conditions_') and f.endswith('.json')]
    
    if not data_files:
        print("No scraped data found. Run scraper.py first.")
        return
    
    latest_file = sorted(data_files)[-1]
    with open(os.path.join('data', latest_file), 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Initialize processor
    processor = LLMProcessor()
    
    # Process the conditions
    processed_data = processor.process_condition_list(scraped_data['conditions'])
    
    # Save processed data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/processed_conditions_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processing completed!")
    print(f"Processed data saved to: {output_file}")
    print(f"Categories found: {list(processed_data.get('categories', {}).keys())}")


if __name__ == "__main__":
    main()