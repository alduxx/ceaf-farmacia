#!/usr/bin/env python3
"""
Standalone script to scrape CEAF data.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()

from logging_config import initialize_application_logging
initialize_application_logging()

import logging
import argparse
from scraper import CEAFScraper
from llm_processor import LLMProcessor
from cache import cache_manager

logger = logging.getLogger(__name__)


def main():
    """Main scraping function."""
    parser = argparse.ArgumentParser(description="Scrape CEAF clinical conditions data")
    parser.add_argument(
        "--process", 
        action="store_true", 
        help="Process scraped data with LLM"
    )
    parser.add_argument(
        "--cache", 
        action="store_true", 
        help="Use caching to avoid re-scraping"
    )
    parser.add_argument(
        "--details", 
        action="store_true", 
        help="Scrape detailed information for each condition"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output file path (optional)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("Starting CEAF data scraping...")
        
        # Initialize scraper
        scraper = CEAFScraper()
        
        # Check cache first if enabled
        scraped_data = None
        if args.cache:
            logger.info("Checking cache for existing data...")
            scraped_data = cache_manager.get_scraped_data(scraper.target_url)
            
            if scraped_data:
                logger.info("Found cached scraped data")
            else:
                logger.info("No cached data found, will scrape fresh data")
        
        # Scrape data if not cached
        if not scraped_data:
            logger.info("Scraping data from government website...")
            scraped_data = scraper.scrape_all_conditions(include_details=args.details)
            
            # Cache the scraped data
            if args.cache:
                cache_manager.set_scraped_data(scraper.target_url, scraped_data)
        
        # Save scraped data
        output_file = args.output
        filepath = scraper.save_data(scraped_data, output_file)
        logger.info(f"Scraped data saved to: {filepath}")
        
        # Process data with LLM if requested
        if args.process:
            logger.info("Processing data with LLM...")
            
            # Check for processed data in cache
            data_hash = cache_manager.generate_data_hash(scraped_data['conditions'])
            processed_data = None
            
            if args.cache:
                processed_data = cache_manager.get_processed_data(data_hash)
                
            if not processed_data:
                processor = LLMProcessor()
                processed_data = processor.process_condition_list(scraped_data['conditions'])
                
                # Cache processed data
                if args.cache:
                    cache_manager.set_processed_data(data_hash, processed_data)
            else:
                logger.info("Found cached processed data")
            
            # Save processed data
            processed_file = filepath.replace('ceaf_conditions_', 'processed_conditions_')
            with open(processed_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Processed data saved to: {processed_file}")
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"SCRAPING COMPLETED SUCCESSFULLY")
        print(f"{'='*50}")
        print(f"Total conditions found: {scraped_data.get('total_conditions', 0)}")
        print(f"Data saved to: {filepath}")
        
        if args.process:
            categories = processed_data.get('categories', {})
            print(f"Categories identified: {len(categories)}")
            print(f"Processed data saved to: {processed_file}")
        
        if args.cache:
            stats = cache_manager.get_cache_stats()
            print(f"Cache entries: {stats['file_cache_entries']}")
            print(f"Cache size: {stats['total_cache_size_mb']:.2f} MB")
        
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\nScraping interrupted by user.")
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()