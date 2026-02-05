#!/bin/bash
# game_scraper/manage_scraper.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Kali Linux Game Scraper Manager      ${NC}"
echo -e "${BLUE}========================================${NC}"

case "$1" in
    start)
        echo -e "${GREEN}[+] Starting game scraper...${NC}"
        source game_scraper/bin/activate
        python3 game_scraper/main_scraper.py
        ;;
    
    setup)
        echo -e "${GREEN}[+] Setting up environment...${NC}"
        chmod +x setup_kali.sh
        ./setup_kali.sh
        ;;
    
    update)
        echo -e "${GREEN}[+] Updating scraper...${NC}"
        git pull origin master 2>/dev/null || echo "Git not configured, skipping"
        source game_scraper/bin/activate
        pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt found"
        ;;
    
    tor)
        echo -e "${GREEN}[+] Managing Tor service...${NC}"
        case "$2" in
            start)
                sudo systemctl start tor
                sudo systemctl enable tor
                echo "Tor started and enabled"
                ;;
            stop)
                sudo systemctl stop tor
                echo "Tor stopped"
                ;;
            restart)
                sudo systemctl restart tor
                echo "Tor restarted"
                ;;
            status)
                sudo systemctl status tor --no-pager -l
                ;;
            *)
                echo "Usage: $0 tor [start|stop|restart|status]"
                ;;
        esac
        ;;
    
    proxy)
        echo -e "${GREEN}[+] Updating proxy list...${NC}"
        python3 game_scraper/update_proxies.py
        ;;
    
    clean)
        echo -e "${YELLOW}[!] Cleaning output and cache...${NC}"
        rm -rf game_scraper/output/*.json
        rm -rf game_scraper/output/*.csv
        rm -rf game_scraper/logs/*.log
        rm -rf __pycache__
        rm -rf game_scraper/__pycache__
        echo "Cleanup complete"
        ;;
    
    stats)
        echo -e "${GREEN}[+] Showing scraping statistics...${NC}"
        if [ -f "game_scraper/output/latest_stats.json" ]; then
            python3 -c "
import json
with open('game_scraper/output/latest_stats.json') as f:
    stats = json.load(f)
print('Latest Scraping Statistics:')
print('=' * 40)
print(f'Total Games: {stats[\"total_games\"]}')
print(f'Date: {stats[\"scraped_at\"]}')
print('\\nBy Source:')
for source, count in stats[\"sources\"].items():
    print(f'  {source}: {count}')
print('=' * 40)
"
        else
            echo "No statistics found. Run the scraper first."
        fi
        ;;
    
    web)
        echo -e "${GREEN}[+] Starting web interface...${NC}"
        if [ -f "game_scraper/output/game_browser.html" ]; then
            echo "Opening web interface..."
            xdg-open "game_scraper/output/game_browser.html" 2>/dev/null || \
            echo "Open manually: game_scraper/output/game_browser.html"
        else
            echo "Web interface not found. Run the scraper first."
        fi
        ;;
    
    export)
        echo -e "${GREEN}[+] Exporting games...${NC}"
        source game_scraper/bin/activate
        python3 game_scraper/export_games.py "$2"
        ;;
    
    monitor)
        echo -e "${GREEN}[+] Monitoring scraper logs...${NC}"
        tail -f game_scraper/logs/scraper.log
        ;;
    
    help|*)
        echo -e "${YELLOW}Usage: $0 [command]${NC}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the main scraper"
        echo "  setup     - Initial setup and installation"
        echo "  update    - Update scraper and dependencies"
        echo "  tor       - Manage Tor service (start|stop|restart|status)"
        echo "  proxy     - Update proxy list"
        echo "  clean     - Clean output and cache"
        echo "  stats     - Show scraping statistics"
        echo "  web       - Open web interface"
        echo "  export    - Export games (json|csv|sql)"
        echo "  monitor   - Monitor scraper logs in real-time"
        echo "  help      - Show this help message"
        ;;
esac