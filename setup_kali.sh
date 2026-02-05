#!/bin/bash

# Install required packages for game scraping on Kali Linux
echo "[+] Setting up Kali Linux for game scraping..."
sudo apt update
sudo apt install -y python3-pip python3-venv tor torsocks proxychains4
sudo pip3 install --upgrade pip

# Create virtual environment
echo "[+] Creating Python virtual environment..."
python3 -m venv game_scraper
source game_scraper/bin/activate

# Install Python packages
echo "[+] Installing required Python packages..."
pip install requests beautifulsoup4 selenium scrapy playwright
pip install aiohttp asyncio lxml pandas numpy
pip install fake-useragent python-whois dnspython
pip install stem requests[socks] bs4 cloudscraper
pip install sqlalchemy datasets tqdm

# Install Playwright browsers
echo "[+] Installing Playwright browsers..."
playwright install chromium firefox

# Create project directory structure
echo "[+] Setting up project structure..."
mkdir -p game_scraper/{scrapers,data,proxies,logs,output}
mkdir -p game_scraper/scrapers/{modules,parsers,utils}

# Tor configuration for anonymity
echo "[+] Configuring Tor for anonymous scraping..."
sudo systemctl start tor
sudo systemctl enable tor

echo "[+] Setup complete! Run the main scraper with:"
echo "    source game_scraper/bin/activate"
echo "    python3 game_scraper/main_scraper.py"