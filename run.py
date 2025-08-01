#!/usr/bin/env python3
"""
Main entry point for CEAF Farmácia application.
"""

import os
import sys
import argparse
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='CEAF Farmácia Web Application')
    parser.add_argument('--host', default=os.getenv('HOST', '127.0.0.1'), 
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 5000)), 
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
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
        
        # Override debug mode if specified
        debug = args.debug or (os.getenv('FLASK_ENV') == 'development')
        
        logger.info(f"Starting web server on {args.host}:{args.port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the application
        app.run(host=args.host, port=args.port, debug=debug)
        
    except PermissionError as e:
        logger.error(f"Permission denied to bind to port {args.port}")
        logger.error("For privileged ports (< 1024), try one of these solutions:")
        logger.error("")
        logger.error("1. Use authbind (recommended):")
        logger.error("   sudo apt install authbind")
        logger.error("   sudo touch /etc/authbind/byport/80")
        logger.error("   sudo chmod 500 /etc/authbind/byport/80")
        logger.error("   sudo chown $USER /etc/authbind/byport/80")
        logger.error("   authbind --deep python run.py --host 0.0.0.0 --port 80")
        logger.error("")
        logger.error("2. Use setcap:")
        logger.error("   sudo setcap 'cap_net_bind_service=+ep' $(which python)")
        logger.error("   python run.py --host 0.0.0.0 --port 80")
        logger.error("")
        logger.error("3. Use sudo (not recommended for production):")
        logger.error("   sudo -E env PATH=$PATH python run.py --host 0.0.0.0 --port 80")
        logger.error("")
        logger.error("4. Use nginx reverse proxy (production recommended):")
        logger.error("   python run.py --host 127.0.0.1 --port 5000")
        logger.error("   # Configure nginx to proxy port 80 to 5000")
        logger.error("")
        logger.error("See PORT_80_SOLUTIONS.md for detailed instructions")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()