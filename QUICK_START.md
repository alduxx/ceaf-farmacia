# CEAF Farmácia - Quick Start Guide

## For Ubuntu Installation

You've already cloned the code and created the `.env` file. Here's what to do next:

### Option 1: Automated Installation (Recommended)
```bash
# Make the script executable and run it
chmod +x install.sh
bash install.sh
```

The script will:
- ✅ Check system requirements
- ✅ Install all dependencies
- ✅ Create virtual environment
- ✅ Set up directories
- ✅ Test the installation
- ✅ Optionally run initial data scraping

### Option 2: Manual Installation

#### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-dev build-essential -y
sudo apt install libssl-dev libffi-dev libpoppler-cpp-dev poppler-utils -y
```

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Create Directories
```bash
mkdir -p data logs cache/{scraped,processed,search}
```

#### 4. Test Installation
```bash
# Quick test
python test_enhanced_scraper.py

# Or test with real data (5 conditions)
python run_enhanced_scraper.py --limit 5
```

#### 5. Start Web Application
```bash
python run.py
```

Visit: http://localhost:5000

## After Installation

### First-Time Data Setup
```bash
# Quick test (5 conditions, ~1 minute)
python run_enhanced_scraper.py --limit 5

# Full data scraping (all 97 conditions, ~5-10 minutes)
python run_full_enhanced_scraper.py
```

### Start the Web Application
```bash
# Activate environment (if not already active)
source venv/bin/activate

# Start server
python run.py
```

### Features to Test
1. **Main page**: http://localhost:5000
2. **Search by condition**: Try "acne", "diabetes", "artrite"
3. **Search by medication**: Try "isotretinoína", "adalimumab"
4. **Search by CID-10**: Try "L70", "E10", "M05"
5. **Condition details**: Click on any condition to see full protocol information

## Troubleshooting

### Common Issues:

#### Python/Pip Issues
```bash
# If python3 command not found
sudo apt install python3 python3-pip

# If virtual environment fails
sudo apt install python3-venv
```

#### Permission Issues
```bash
chmod +x *.py
sudo chown -R $USER:$USER .
```

#### Dependencies Fail to Install
```bash
# Install build tools
sudo apt install build-essential python3-dev

# Clear cache and retry
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

#### Port 5000 Already in Use
```bash
# Kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9

# Or run on different port
python run.py --port 8000
```

### Check Installation
```bash
# Verify Python imports work
python -c "
import sys; sys.path.insert(0, 'src')
from scraper import CEAFScraper
print('✅ Installation OK!')
"
```

## Production Deployment

### Using Gunicorn
```bash
# Install production server
pip install gunicorn

# Run production server
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Reverse Proxy with Nginx (Optional)
```bash
# Install nginx
sudo apt install nginx

# Configure as reverse proxy to localhost:5000
```

## Need Help?

1. **Check logs**: `logs/farmacia.log`
2. **Test with minimal data**: `python run_enhanced_scraper.py --limit 1`
3. **Verify dependencies**: All packages in `requirements.txt` should install successfully
4. **System requirements**: Ubuntu 18.04+, Python 3.8+, 2GB RAM minimum

## Quick Commands Reference

```bash
# Activate environment
source venv/bin/activate

# Test scraping
python run_enhanced_scraper.py --limit 5

# Start web app
python run.py

# Full data scraping
python run_full_enhanced_scraper.py

# Check what data is available
python check_enhanced_data.py

# Demo features
python demo_enhanced_features.py
```