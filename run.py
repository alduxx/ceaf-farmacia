#!/usr/bin/env python3
"""
Main entry point for CEAF Farmácia application.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize logging first
from logging_config import initialize_application_logging
initialize_application_logging()

import logging
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        logger.info("Starting CEAF Farmácia application...")
        
        # Import Flask app
        from app import app, initialize_data
        from logging_config import setup_flask_logging
        
        # Set up Flask logging
        setup_flask_logging(app)
        
        # Initialize data
        logger.info("Initializing application data...")
        initialize_data()
        
        # Get configuration
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        logger.info(f"Starting web server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the application
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()