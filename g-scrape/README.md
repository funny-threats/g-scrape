# Kali Linux Advanced Game Scraper

A comprehensive, multi-threaded game scraper for Kali Linux that scrapes 10+ gaming websites thoroughly to collect game embeds and metadata.

## Features

- **Multi-source scraping**: Scrapes from Poki, Coolmath, Kongregate, GamePix, CrazyGames, Y8, ArmorGames, Nitrome, unblocked games sites, GitHub, and HTML5 portals
- **Advanced techniques**: Uses Requests, Selenium, Cloudscraper, Playwright, and aiohttp
- **Anti-detection**: Rotating user agents, proxy support, Tor integration, random delays
- **Parallel processing**: Scrapes multiple sites simultaneously
- **Thorough extraction**: Extracts game names, URLs, images, descriptions, ratings, and embed codes
- **Web interface**: Built-in browser to view and play collected games
- **Database export**: Export to JSON, CSV, or SQLite

## Quick Start

### 1. Setup
```bash
# Make scripts executable
chmod +x setup_kali.sh manage_scraper.sh

# Run setup
./manage_scraper.sh setup