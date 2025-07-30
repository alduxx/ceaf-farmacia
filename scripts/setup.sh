#!/bin/bash

# CEAF Farmácia Setup Script
# This script sets up the development environment

set -e  # Exit on any error

echo "=========================================="
echo "CEAF Farmácia - Setup Script"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data logs cache templates static/css static/js

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
else
    echo ".env file already exists"
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x run.py
chmod +x scripts/scrape_data.py
chmod +x scripts/setup.sh

# Test imports
echo "Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from scraper import CEAFScraper
    from llm_processor import LLMProcessor
    from app import app
    from cache import CacheManager
    print('✓ All core modules imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration (API keys, etc.)"
echo "2. Run './scripts/scrape_data.py --cache --process' to get initial data"
echo "3. Run './run.py' to start the web application"
echo ""
echo "For development:"
echo "  source venv/bin/activate  # Activate virtual environment"
echo "  ./run.py                  # Start application"
echo ""
echo "For scraping data:"
echo "  ./scripts/scrape_data.py --help  # See scraping options"
echo ""
echo "Documentation: see README.md"
echo "=========================================="