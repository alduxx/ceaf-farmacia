"""
Flask web application for patient-friendly CEAF information.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

from scraper import CEAFScraper
from llm_processor import LLMProcessor
from cache import cache_manager


app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data storage
SCRAPED_DATA = {}
PROCESSED_DATA = {}
SEARCH_INDEX = {}


def perform_ai_search(query: str, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use AI to find matching conditions based on synonyms, abbreviations, and related terms."""
    try:
        processor = LLMProcessor()
        
        # Create a list of condition names for the AI
        condition_names = [c['name'] for c in conditions]
        
        prompt = f"""
        Você é um especialista em condições médicas do programa CEAF brasileiro. 
        
        Um paciente está procurando por: "{query}"
        
        Aqui está a lista completa de condições disponíveis no CEAF:
        {', '.join(condition_names)}
        
        Por favor, identifique quais condições da lista podem corresponder ao termo de busca "{query}".
        Considere:
        - Sinônimos médicos
        - Abreviações comuns (ex: TEA = Transtorno do Espectro Autista)
        - Nomes populares vs nomes técnicos
        - Termos relacionados
        - Grafias alternativas
        
        Responda APENAS com os nomes exatos das condições da lista que correspondem, separados por vírgulas.
        Se não houver correspondências, responda "NENHUMA".
        
        Exemplos:
        - Para "TEA" ou "autismo": "Comportamento Agressivo Como Transtorno Do Espectro Do Autismo"
        - Para "diabetes": "Diabetes Mellitus Tipo I, Diabetes Mellitus Tipo 2"
        - Para "artrite": "Artrite Reumatoide, Artrite Psoríaca, Artrite Reativa, Artrite Reumatoide Juvenil"
        """
        
        # Get AI response
        if processor.client:
            ai_response = processor._call_llm(prompt).strip()
            logger.info(f"AI search response for '{query}': {ai_response}")
            
            if ai_response.upper() == "NENHUMA":
                return []
            
            # Parse the AI response
            suggested_names = [name.strip() for name in ai_response.split(',')]
            
            # Find the actual condition objects
            matched_conditions = []
            for suggested_name in suggested_names:
                for condition in conditions:
                    if condition['name'].lower() == suggested_name.lower():
                        matched_conditions.append(condition)
                        break
            
            logger.info(f"AI search found {len(matched_conditions)} matches for '{query}'")
            return matched_conditions
        
        else:
            # Fallback: simple keyword matching with common abbreviations
            logger.info(f"AI not available, using fallback search for '{query}'")
            return fallback_smart_search(query, conditions)
            
    except Exception as e:
        logger.error(f"AI search failed for '{query}': {e}")
        return fallback_smart_search(query, conditions)


def fallback_smart_search(query: str, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhanced fallback search with popular terms, abbreviations, and fuzzy matching."""
    
    try:
        from fuzzywuzzy import fuzz, process
        FUZZY_AVAILABLE = True
    except ImportError:
        FUZZY_AVAILABLE = False
        logger.warning("fuzzywuzzy not available, using basic search only")
    
    # Comprehensive Brazilian Portuguese medical terms dictionary
    medical_terms = {
        # Popular/colloquial terms -> medical terms
        'espinhas': ['acne'],
        'cravos': ['acne'],
        'espinha': ['acne'],
        'açúcar alto': ['diabetes'],
        'açúcar no sangue': ['diabetes'],
        'diabete': ['diabetes'],
        'diabetis': ['diabetes'],
        'doença do açúcar': ['diabetes'],
        'pressão alta': ['hipertensão'],
        'coração': ['cardíaco', 'transplante cardíaco'],
        'rim': ['renal', 'transplante renal'],
        'fígado': ['hepático', 'transplante hepático', 'hepatite'],
        'pulmão': ['pulmonar'],
        'respiração': ['pulmonar', 'asma'],
        'chiado': ['asma'],
        'falta de ar': ['asma', 'pulmonar'],
        'esquecimento': ['alzheimer'],
        'memória': ['alzheimer'],
        'tremor': ['parkinson'],
        'tremores': ['parkinson'],
        'dor nas juntas': ['artrite'],
        'dor articular': ['artrite'],
        'junta inchada': ['artrite'],
        'mancha na pele': ['psoríase', 'dermatite'],
        'coceira': ['dermatite', 'urticária'],
        'alergia na pele': ['dermatite', 'urticária'],
        'convulsão': ['epilepsia'],
        'ataque': ['epilepsia'],
        'intestino': ['crohn', 'retocolite'],
        'barriga': ['crohn'],
        'diarréia': ['crohn', 'retocolite'],
        'depressão': ['depressão', 'bipolar'],
        'tristeza': ['depressão'],
        'mania': ['bipolar'],
        'humor': ['bipolar'],
        'crescimento': ['hormônio do crescimento', 'turner'],
        'baixinho': ['hormônio do crescimento'],
        'nanismo': ['hormônio do crescimento'],
        'visão': ['glaucoma'],
        'olho': ['glaucoma', 'uveítes'],
        'cegueira': ['glaucoma'],
        'osso': ['osteoporose', 'paget'],
        'fratura': ['osteoporose'],
        'sangue': ['anemia', 'falciforme', 'hemofilia'],
        'anemia': ['anemia', 'falciforme'],
        'cansaço': ['anemia'],
        'fraqueza': ['anemia', 'miastenia'],
        'músculos': ['miastenia', 'distrofia', 'atrofia'],
        
        # Abbreviations
        'tea': ['transtorno do espectro', 'autismo', 'comportamento agressivo'],
        'tdah': ['deficit de atenção', 'hiperatividade'],
        'dm': ['diabetes mellitus'],
        'dm1': ['diabetes mellitus tipo i'],
        'dm2': ['diabetes mellitus tipo 2'],
        'dpoc': ['doença pulmonar obstrutiva'],
        'hiv': ['hiv', 'aids'],
        'hap': ['hipertensão arterial pulmonar'],
        'fc': ['fibrose cística'],
        'em': ['esclerose múltipla'],
        'ela': ['esclerose lateral amiotrófica'],
        'ar': ['artrite reumatoide'],
        'les': ['lúpus eritematoso sistêmico'],
        'mg': ['miastenia gravis'],
        'dii': ['doença inflamatória intestinal', 'crohn'],
        'tab': ['transtorno afetivo bipolar'],
        'toc': ['transtorno obsessivo'],
        
        # Common misspellings and variations
        'alzaimer': ['alzheimer'],
        'alzaemer': ['alzheimer'],
        'alzeimer': ['alzheimer'],
        'alzheimer': ['alzheimer'],  # Include correct spelling too
        'alzaeimer': ['alzheimer'],
        'alzeaimer': ['alzheimer'],
        'alzaymer': ['alzheimer'],
        'alzeimer': ['alzheimer'],
        'alzaemer': ['alzheimer'],
        'alzeamer': ['alzheimer'],
        'parkison': ['parkinson'],
        'parquinson': ['parkinson'],
        'diabetis': ['diabetes'],
        'diabetess': ['diabetes'],
        'artrit': ['artrite'],
        'artritis': ['artrite'],
        'lupuz': ['lúpus'],
        'lupous': ['lúpus'],
        'esclerose': ['esclerose múltipla', 'esclerose lateral', 'esclerose sistêmica'],
        'fibrosis': ['fibrose'],
        'fibrozis': ['fibrose'],
        'glaucoma': ['glaucoma'],
        'glaocoma': ['glaucoma'],
        'osteoporose': ['osteoporose'],
        'ostioporose': ['osteoporose'],
        'psoriase': ['psoríase'],
        'psoriasis': ['psoríase'],
        'hepatit': ['hepatite'],
        'hepatitis': ['hepatite'],
        'transplant': ['transplante'],
        'epilepsia': ['epilepsia'],
        'epilepsia': ['epilepsia'],
        'epilepsy': ['epilepsia'],
        'asma': ['asma'],
        'azma': ['asma'],
        'esquizofrenia': ['esquizofrenia', 'transtorno esquizoafetivo'],
        'esquisofrenia': ['esquizofrenia'],
        'bipolar': ['transtorno afetivo bipolar'],
        'bi-polar': ['transtorno afetivo bipolar'],
        'autismo': ['transtorno do espectro', 'comportamento agressivo'],
        'autista': ['transtorno do espectro', 'comportamento agressivo']
    }
    
    query_lower = query.lower()
    matches = []
    
    # 1. Exact match in medical terms dictionary
    if query_lower in medical_terms:
        search_terms = medical_terms[query_lower]
        for term in search_terms:
            for condition in conditions:
                if term in condition['name'].lower():
                    matches.append(condition)
    
    # 2. Fuzzy matching for misspellings (if available)
    if FUZZY_AVAILABLE and not matches:
        # Create a list of all medical terms for fuzzy matching
        all_medical_terms = list(medical_terms.keys())
        
        # Try multiple fuzzy matching algorithms
        fuzzy_methods = [
            (fuzz.ratio, 65, "ratio"),
            (fuzz.partial_ratio, 70, "partial_ratio"),
            (fuzz.token_sort_ratio, 60, "token_sort")
        ]
        
        for scorer, threshold, method_name in fuzzy_methods:
            if matches:  # Stop if we found matches
                break
                
            fuzzy_matches = process.extractBests(query_lower, all_medical_terms, 
                                               scorer=scorer, score_cutoff=threshold, limit=3)
            
            for match_term, score in fuzzy_matches:
                logger.info(f"Fuzzy match ({method_name}): '{query_lower}' -> '{match_term}' (score: {score})")
                search_terms = medical_terms[match_term]
                for term in search_terms:
                    for condition in conditions:
                        if term in condition['name'].lower():
                            matches.append(condition)
    
    # 3. Fuzzy matching directly with condition names
    if FUZZY_AVAILABLE and len(matches) < 2:
        condition_names = [c['name'] for c in conditions]
        fuzzy_condition_matches = process.extractBests(query_lower, condition_names, 
                                                     scorer=fuzz.partial_ratio, 
                                                     score_cutoff=60, limit=5)
        
        for match_name, score in fuzzy_condition_matches:
            logger.info(f"Direct condition fuzzy match: '{query_lower}' -> '{match_name}' (score: {score})")
            for condition in conditions:
                if condition['name'] == match_name:
                    matches.append(condition)
                    break
    
    # 4. Fallback: word-based and substring matching
    if not matches:
        for condition in conditions:
            condition_lower = condition['name'].lower()
            
            # Direct substring match
            if query_lower in condition_lower:
                matches.append(condition)
                continue
            
            # Split query and condition into words for better matching
            query_words = query_lower.split()
            condition_words = condition_lower.split()
            
            # Check if any query word appears in condition words
            match_found = False
            for query_word in query_words:
                if len(query_word) > 2:  # Skip very short words
                    for condition_word in condition_words:
                        # More precise matching - word boundaries
                        if (query_word in condition_word and len(query_word) >= len(condition_word) * 0.6) or \
                           (condition_word in query_word and len(condition_word) >= len(query_word) * 0.6):
                            matches.append(condition)
                            match_found = True
                            break
                    if match_found:
                        break
    
    # Remove duplicates
    unique_matches = []
    seen_names = set()
    for match in matches:
        if match['name'] not in seen_names:
            unique_matches.append(match)
            seen_names.add(match['name'])
    
    # Log the search process
    logger.info(f"Enhanced search for '{query}': found {len(unique_matches)} matches")
    if unique_matches:
        for i, match in enumerate(unique_matches[:3]):  # Log first 3 matches
            logger.info(f"  {i+1}. {match['name']}")
    
    return unique_matches


class DataManager:
    """Manage scraped and processed data loading/saving."""
    
    @staticmethod
    def load_latest_scraped_data() -> Dict[str, Any]:
        """Load the most recent scraped data."""
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return {}
        
        files = [f for f in os.listdir(data_dir) if f.startswith('ceaf_conditions_') and f.endswith('.json')]
        if not files:
            return {}
        
        latest_file = sorted(files)[-1]
        filepath = os.path.join(data_dir, latest_file)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded scraped data from {filepath}")
                return data
        except Exception as e:
            logger.error(f"Failed to load scraped data: {e}")
            return {}
    
    @staticmethod
    def load_latest_processed_data() -> Dict[str, Any]:
        """Load the most recent processed data."""
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return {}
        
        files = [f for f in os.listdir(data_dir) if f.startswith('processed_conditions_') and f.endswith('.json')]
        if not files:
            return {}
        
        latest_file = sorted(files)[-1]
        filepath = os.path.join(data_dir, latest_file)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded processed data from {filepath}")
                return data
        except Exception as e:
            logger.error(f"Failed to load processed data: {e}")
            return {}
    
    @staticmethod
    def build_search_index(conditions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build a search index for conditions."""
        index = {}
        
        for condition in conditions:
            name = condition.get('name', '').lower()
            words = re.findall(r'\w+', name)
            
            for word in words:
                if len(word) > 2:  # Skip very short words
                    if word not in index:
                        index[word] = []
                    if condition['name'] not in index[word]:
                        index[word].append(condition['name'])
        
        return index


def initialize_data():
    """Initialize application data on startup."""
    global SCRAPED_DATA, PROCESSED_DATA, SEARCH_INDEX
    
    logger.info("Initializing application data...")
    
    # Load scraped data
    SCRAPED_DATA = DataManager.load_latest_scraped_data()
    
    # Load processed data
    PROCESSED_DATA = DataManager.load_latest_processed_data()
    
    # If no processed data exists, try to process scraped data
    if not PROCESSED_DATA and SCRAPED_DATA:
        logger.info("No processed data found, processing scraped data...")
        try:
            processor = LLMProcessor()
            PROCESSED_DATA = processor.process_condition_list(SCRAPED_DATA.get('conditions', []))
        except Exception as e:
            logger.error(f"Failed to process data: {e}")
    
    # Build search index
    if SCRAPED_DATA:
        SEARCH_INDEX = DataManager.build_search_index(SCRAPED_DATA.get('conditions', []))
        logger.info(f"Built search index with {len(SEARCH_INDEX)} terms")


@app.route('/')
def index():
    """Main page showing condition categories and search."""
    stats = {
        'total_conditions': len(SCRAPED_DATA.get('conditions', [])),
        'categories_count': len(PROCESSED_DATA.get('categories', {})),
        'last_updated': SCRAPED_DATA.get('scraped_at', 'Unknown')
    }
    
    categories = PROCESSED_DATA.get('categories', {})
    common_conditions = PROCESSED_DATA.get('common_conditions', [])
    
    return render_template('index.html', 
                         stats=stats,
                         categories=categories,
                         common_conditions=common_conditions)


@app.route('/search')
def search():
    """Search for conditions based on query with AI enhancement."""
    query = request.args.get('q', '').lower().strip()
    
    if not query:
        return jsonify({'results': [], 'message': 'Por favor, digite um termo de busca'})
    
    # Check cache first for AI-enhanced searches
    cached_results = cache_manager.get_search_results(query)
    if cached_results is not None:
        logger.info(f"Found cached search results for '{query}'")
        return jsonify({
            'results': cached_results[:20],
            'total': len(cached_results),
            'query': query,
            'source': 'cache'
        })
    
    results = []
    query_words = re.findall(r'\w+', query)
    
    # 1. Direct search in the index (fast)
    for word in query_words:
        if word in SEARCH_INDEX:
            for condition_name in SEARCH_INDEX[word]:
                # Find the full condition data
                for condition in SCRAPED_DATA.get('conditions', []):
                    if condition['name'] == condition_name:
                        results.append(condition)
                        break
    
    # 2. Partial matching (fallback)
    if not results:
        for condition in SCRAPED_DATA.get('conditions', []):
            if query in condition['name'].lower():
                results.append(condition)
    
    # 3. AI-enhanced search for better matches
    if not results or len(results) < 3:
        logger.info(f"Using AI-enhanced search for query: '{query}'")
        ai_results = perform_ai_search(query, SCRAPED_DATA.get('conditions', []))
        
        # Merge AI results with existing results
        for ai_result in ai_results:
            if ai_result not in results:
                results.append(ai_result)
    
    # Remove duplicates
    unique_results = []
    seen_names = set()
    for result in results:
        if result['name'] not in seen_names:
            unique_results.append(result)
            seen_names.add(result['name'])
    
    # Cache the results for future use
    cache_manager.set_search_results(query, unique_results)
    
    return jsonify({
        'results': unique_results[:20],  # Limit to 20 results
        'total': len(unique_results),
        'query': query,
        'source': 'ai_enhanced' if len(unique_results) > len(results) else 'standard'
    })


@app.route('/condition/<condition_name>')
def condition_detail(condition_name):
    """Show detailed information about a specific condition."""
    condition = None
    
    # Find the condition in scraped data
    for c in SCRAPED_DATA.get('conditions', []):
        if c['name'] == condition_name:
            condition = c
            break
    
    if not condition:
        return render_template('condition_not_found.html', condition_name=condition_name)
    
    # Try to get processed explanation
    explanation = None
    try:
        processor = LLMProcessor()
        explanation_data = processor.explain_condition(condition)
        explanation = explanation_data.get('patient_friendly_explanation', '')
    except Exception as e:
        logger.error(f"Failed to generate explanation for {condition_name}: {e}")
    
    return render_template('condition_detail.html', 
                         condition=condition,
                         explanation=explanation)


@app.route('/api/conditions')
def api_conditions():
    """API endpoint to get all conditions."""
    return jsonify(SCRAPED_DATA.get('conditions', []))


@app.route('/api/categories')
def api_categories():
    """API endpoint to get condition categories."""
    return jsonify(PROCESSED_DATA.get('categories', {}))


@app.route('/api/refresh')
def api_refresh():
    """API endpoint to refresh data by re-scraping."""
    try:
        logger.info("Starting data refresh...")
        
        # Re-scrape data
        scraper = CEAFScraper()
        new_scraped_data = scraper.scrape_all_conditions()
        scraper.save_data(new_scraped_data)
        
        # Re-process data
        processor = LLMProcessor()
        new_processed_data = processor.process_condition_list(new_scraped_data['conditions'])
        
        # Save processed data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_file = f"data/processed_conditions_{timestamp}.json"
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(new_processed_data, f, ensure_ascii=False, indent=2)
        
        # Update global data
        global SCRAPED_DATA, PROCESSED_DATA, SEARCH_INDEX
        SCRAPED_DATA = new_scraped_data
        PROCESSED_DATA = new_processed_data
        SEARCH_INDEX = DataManager.build_search_index(SCRAPED_DATA.get('conditions', []))
        
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso',
            'total_conditions': len(SCRAPED_DATA.get('conditions', [])),
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Data refresh failed: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar dados: {str(e)}'
        }), 500


@app.route('/about')
def about():
    """About page explaining the application."""
    return render_template('about.html')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Initialize data on startup
    initialize_data()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)