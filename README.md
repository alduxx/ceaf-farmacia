# CEAF Farmacia - Patient-Friendly Medication Information

A Python application that improves the experience for patients who need high-cost medications by scraping government data and providing a user-friendly interface through LLM processing.

## Overview

This application scrapes the official Brazilian government website for clinical protocols and presents the information about clinical conditions served by CEAF (Specialized Component of Pharmaceutical Assistance) in a more accessible format for patients.

## Features

- **Automated Data Extraction**: Scrapes updated information from the government website
- **LLM Processing**: Uses AI to organize and simplify medical information
- **User-Friendly Interface**: Easy-to-navigate web interface for patient consultations
- **Search Functionality**: Allows patients to search for their specific conditions
- **Cached Data**: Reduces load on government servers with intelligent caching

## Target Website

https://www.saude.df.gov.br/protocolos-clinicos-ter-resumos-e-formularios

Focus: "Condições Clínicas atendidas no Componente Especializado da Assistência Farmacêutica (CEAF)"

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd farmacia

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the scraper
python src/scraper.py

# Start the web interface
python src/app.py
```

## Project Structure

```
farmacia/
├── src/
│   ├── scraper.py          # Web scraping functionality
│   ├── llm_processor.py    # LLM integration for data processing
│   ├── app.py             # Web interface application
│   └── cache.py           # Data caching mechanism
├── data/                  # Cached scraped data
├── templates/             # HTML templates for web interface
├── static/               # CSS, JS, and other static files
├── requirements.txt      # Python dependencies
├── README.md
└── CLAUDE.md
```

## Development

This project prioritizes:
- Patient usability and accessibility
- Robust error handling for web scraping
- Efficient caching to minimize government server requests
- Clear documentation and code structure

## License

This project is intended for educational and public service purposes to help patients access medication information more easily.