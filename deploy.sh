#!/bin/bash
# Deploy script for CEAF Farmacia application
# Run this script as root or with sudo privileges

set -e  # Exit on any error

# Configuration
APP_NAME="farmacia"
APP_USER="farmacia"
APP_DIR="/opt/farmacia"
REPO_URL="https://github.com/user/ceaf-farmacia.git"  # Replace with actual repo URL
DOMAIN="your-domain.com"  # Replace with actual domain

echo "🚀 Starting deployment of CEAF Farmacia application..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
echo "📦 Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor git curl

# Create application user
echo "👤 Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home "$APP_USER"
    echo "✅ User $APP_USER created"
else
    echo "ℹ️ User $APP_USER already exists"
fi

# Create application directory structure
echo "📁 Creating directory structure..."
mkdir -p "$APP_DIR"/{logs,data,cache,static}
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Clone or update application code
echo "📥 Downloading application code..."
if [ -d "$APP_DIR/.git" ]; then
    echo "ℹ️ Updating existing repository..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull
else
    echo "ℹ️ Cloning repository..."
    # If running from local directory, copy files instead of cloning
    if [ -f "./src/app.py" ]; then
        echo "📂 Copying local files..."
        cp -r . "$APP_DIR/"
        chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    else
        sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    fi
fi

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u "$APP_USER" venv/bin/pip install -r requirements.txt
sudo -u "$APP_USER" venv/bin/pip install gunicorn

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > "$APP_DIR/.env" << EOF
FLASK_ENV=production
FLASK_APP=src.app:app
PYTHONPATH=$APP_DIR/src
# Add your API keys here:
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
EOF
chown "$APP_USER:$APP_USER" "$APP_DIR/.env"

# Set up systemd service
echo "🔧 Configuring systemd service..."
cp "$APP_DIR/farmacia.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable farmacia

# Configure Nginx
echo "🌐 Configuring Nginx..."
# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Install our site configuration
cp "$APP_DIR/nginx.conf" "/etc/nginx/sites-available/$APP_NAME"

# Update domain in nginx config
sed -i "s/your-domain.com/$DOMAIN/g" "/etc/nginx/sites-available/$APP_NAME"

# Enable site
ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/$APP_NAME"

# Test Nginx configuration
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration error"
    exit 1
fi

# Set up log rotation
echo "📄 Setting up log rotation..."
cat > /etc/logrotate.d/farmacia << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload farmacia
    endscript
}
EOF

# Initialize application data
echo "📊 Initializing application data..."
cd "$APP_DIR"
sudo -u "$APP_USER" venv/bin/python -c "
import sys
sys.path.append('$APP_DIR/src')
from scraper import CEAFScraper
from llm_processor import LLMProcessor
import json
import os
from datetime import datetime

print('Scraping initial data...')
scraper = CEAFScraper()
data = scraper.scrape_all_conditions()
scraper.save_data(data)
print(f'Scraped {len(data.get(\"conditions\", []))} conditions')
"

# Start services
echo "🚀 Starting services..."
systemctl restart farmacia
systemctl restart nginx

# Check service status
echo "🔍 Checking service status..."
if systemctl is-active --quiet farmacia; then
    echo "✅ Farmacia service is running"
else
    echo "❌ Farmacia service failed to start"
    systemctl status farmacia
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "❌ Nginx service failed to start"
    systemctl status nginx
    exit 1
fi

# Final checks
echo "🧪 Running final checks..."
sleep 3

if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ Application is responding on port 5000"
else
    echo "❌ Application is not responding on port 5000"
fi

if curl -s http://localhost > /dev/null; then
    echo "✅ Nginx is serving the application on port 80"
else
    echo "❌ Nginx is not responding on port 80"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your API keys in $APP_DIR/.env"
echo "2. Update domain name in /etc/nginx/sites-available/$APP_NAME if needed"
echo "3. Set up SSL certificate (recommended: certbot)"
echo "4. Configure firewall to allow HTTP (80) and HTTPS (443)"
echo ""
echo "🔧 Management commands:"
echo "  Start service:   systemctl start farmacia"
echo "  Stop service:    systemctl stop farmacia"
echo "  Restart service: systemctl restart farmacia"
echo "  View logs:       journalctl -u farmacia -f"
echo "  Check status:    systemctl status farmacia"
echo ""
echo "🌐 Your application should be accessible at:"
echo "  http://$DOMAIN"
echo "  http://$(hostname -I | awk '{print $1}')"