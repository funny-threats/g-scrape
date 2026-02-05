#!/usr/bin/env python3
"""
Comprehensive Game Scraper for Kali Linux
Scrapes 10+ gaming websites thoroughly
"""

import os
import sys
import json
import time
import random
import asyncio
import aiohttp
import requests
import threading
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

# Third-party imports
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
import cloudscraper
import lxml.html
from lxml import etree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_scraper/logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Game:
    """Game data structure"""
    name: str
    url: str
    source: str
    embed_url: str = ""
    iframe_code: str = ""
    image_url: str = ""
    description: str = ""
    category: str = ""
    tags: List[str] = None
    play_count: int = 0
    rating: float = 0.0
    date_scraped: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.date_scraped:
            self.date_scraped = datetime.now().isoformat()

class ScraperType(Enum):
    """Types of scrapers available"""
    REQUESTS_BS4 = "requests+beautifulsoup4"
    SELENIUM = "selenium"
    CLOUDSCRAPER = "cloudscraper"
    PLAYWRIGHT = "playwright"
    AIOHTTP = "aiohttp"

class ProxyManager:
    """Manage proxy rotation for scraping"""
    
    def __init__(self):
        self.proxies = self._load_proxies()
        self.current_proxy_idx = 0
        self.tor_session = None
        
    def _load_proxies(self) -> List[str]:
        """Load proxies from various sources"""
        proxies = [
            # Free proxy servers (rotate these regularly)
            "http://45.77.56.114:3128",
            "http://138.197.157.44:8080",
            "http://165.227.103.244:8080",
            "http://159.65.69.186:9300",
            # Tor proxies
            "socks5://127.0.0.1:9050",
            "socks5h://127.0.0.1:9050",
            # Additional proxies would be loaded from file
        ]
        return proxies
    
    def get_random_proxy(self) -> Dict[str, str]:
        """Get a random proxy"""
        if not self.proxies:
            return {}
        
        proxy = random.choice(self.proxies)
        if proxy.startswith('socks'):
            return {
                'http': proxy,
                'https': proxy
            }
        return {'http': proxy, 'https': proxy}
    
    def get_tor_session(self):
        """Get a Tor session for anonymity"""
        if self.tor_session is None:
            session = requests.Session()
            session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
            self.tor_session = session
        return self.tor_session

class AdvancedScraper:
    """Advanced scraper with multiple techniques"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.proxy_manager = ProxyManager()
        self.scraped_urls: Set[str] = set()
        self.max_workers = 5
        self.request_delay = (1, 3)  # Random delay between requests
        self.timeout = 30
        
    def get_headers(self) -> Dict[str, str]:
        """Generate random headers for requests"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def _delay(self):
        """Random delay between requests to avoid detection"""
        time.sleep(random.uniform(*self.request_delay))
    
    def scrape_with_requests(self, url: str, use_proxy: bool = True) -> Optional[str]:
        """Scrape using requests library"""
        try:
            self._delay()
            headers = self.get_headers()
            proxies = self.proxy_manager.get_random_proxy() if use_proxy else {}
            
            session = requests.Session() if use_proxy else requests
            response = session.get(
                url, 
                headers=headers, 
                proxies=proxies,
                timeout=self.timeout,
                verify=False  # Be cautious with this in production
            )
            response.raise_for_status()
            
            # Check if we got blocked
            if any(indicator in response.text.lower() for indicator in ['captcha', 'cloudflare', 'access denied']):
                logger.warning(f"Possible block detected on {url}")
                return None
                
            return response.text
            
        except Exception as e:
            logger.error(f"Requests scraping failed for {url}: {str(e)}")
            return None
    
    def scrape_with_selenium(self, url: str) -> Optional[str]:
        """Scrape using Selenium for JavaScript-heavy sites"""
        driver = None
        try:
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={self.ua.random}')
            
            # Add proxy if available
            proxy = self.proxy_manager.get_random_proxy()
            if proxy and 'http' in proxy:
                options.add_argument(f'--proxy-server={proxy["http"]}')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            return driver.page_source
            
        except Exception as e:
            logger.error(f"Selenium scraping failed for {url}: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def scrape_with_cloudscraper(self, url: str) -> Optional[str]:
        """Scrape sites protected by Cloudflare"""
        try:
            self._delay()
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=self.timeout)
            return response.text
        except Exception as e:
            logger.error(f"Cloudscraper failed for {url}: {str(e)}")
            return None
    
    async def scrape_with_aiohttp(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Asynchronous scraping with aiohttp"""
        try:
            headers = self.get_headers()
            async with session.get(url, headers=headers, timeout=self.timeout) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            logger.error(f"Async scraping failed for {url}: {str(e)}")
            return None

class WebsiteScraper:
    """Base class for website-specific scrapers"""
    
    def __init__(self, base_url: str, name: str):
        self.base_url = base_url
        self.name = name
        self.scraper = AdvancedScraper()
        self.games: List[Game] = []
        
    def extract_iframes(self, html: str) -> List[str]:
        """Extract iframe tags from HTML"""
        iframes = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find iframe tags
        for iframe in soup.find_all('iframe'):
            iframe_str = str(iframe)
            iframes.append(iframe_str)
        
        # Also look for embed tags
        for embed in soup.find_all('embed'):
            iframe_str = str(embed)
            iframes.append(iframe_str)
            
        return iframes
    
    def find_game_urls(self, html: str) -> List[str]:
        """Find game URLs in page"""
        soup = BeautifulSoup(html, 'html.parser')
        game_urls = []
        
        # Common patterns for game links
        patterns = [
            ('a', {'href': True, 'class': lambda x: x and any(word in str(x).lower() for word in ['game', 'play', 'btn'])}),
            ('a', {'href': lambda x: x and any(ext in x.lower() for ext in ['.html', '.htm', '/game', 'play'])}),
            ('div', {'class': 'game'}),
            ('div', {'data-game': True}),
        ]
        
        for tag_name, attrs in patterns:
            elements = soup.find_all(tag_name, attrs)
            for element in elements:
                if tag_name == 'a' and 'href' in element.attrs:
                    url = urljoin(self.base_url, element['href'])
                    if url not in game_urls:
                        game_urls.append(url)
        
        return game_urls
    
    def scrape(self) -> List[Game]:
        """Main scraping method to be overridden by subclasses"""
        raise NotImplementedError

# ============== WEBSITE-SPECIFIC SCRAPERS ==============

class PokiScraper(WebsiteScraper):
    """Scraper for Poki.com"""
    
    def __init__(self):
        super().__init__("https://poki.com", "Poki")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Get main page
            html = self.scraper.scrape_with_cloudscraper(self.base_url)
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find game containers
            game_elements = soup.find_all('div', {'class': 'game'})
            game_elements.extend(soup.find_all('a', {'class': 'game-item'}))
            game_elements.extend(soup.find_all('div', {'data-testid': 'game-card'}))
            
            for element in game_elements[:100]:  # Limit to 100 games
                try:
                    # Extract game info
                    game = Game(
                        name="",
                        url="",
                        source=self.name
                    )
                    
                    # Find name
                    name_elem = element.find(['h3', 'h2', 'div', 'a'], 
                                            {'class': lambda x: x and any(word in str(x).lower() for word in ['title', 'name', 'game-name'])})
                    if name_elem:
                        game.name = name_elem.get_text(strip=True)
                    
                    # Find URL
                    link_elem = element.find('a', href=True)
                    if link_elem:
                        game.url = urljoin(self.base_url, link_elem['href'])
                    
                    # Find image
                    img_elem = element.find('img', src=True)
                    if img_elem:
                        game.image_url = urljoin(self.base_url, img_elem['src'])
                    
                    if game.name and game.url:
                        # Get game page to find embed
                        game_html = self.scraper.scrape_with_requests(game.url)
                        if game_html:
                            iframes = self.extract_iframes(game_html)
                            if iframes:
                                game.iframe_code = iframes[0]
                            else:
                                # Try to construct embed URL
                                game_slug = game.url.rstrip('/').split('/')[-1]
                                embed_url = f"https://poki.com/embed/{game_slug}"
                                game.iframe_code = f'<iframe src="{embed_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        
                        self.games.append(game)
                        logger.info(f"Found game: {game.name}")
                        
                except Exception as e:
                    logger.error(f"Error processing game element: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class CoolmathScraper(WebsiteScraper):
    """Scraper for CoolmathGames.com"""
    
    def __init__(self):
        super().__init__("https://www.coolmathgames.com", "Coolmath Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Get all games page
            url = f"{self.base_url}/0-all-games"
            html = self.scraper.scrape_with_requests(url)
            
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Coolmath has a specific structure
            game_links = soup.find_all('a', {'class': 'game-card'})
            game_links.extend(soup.find_all('a', {'href': lambda x: x and '/0-' in x}))
            
            for link in game_links[:80]:
                try:
                    if 'href' not in link.attrs:
                        continue
                    
                    game_url = urljoin(self.base_url, link['href'])
                    
                    # Extract name
                    name_elem = link.find(['span', 'div', 'h3'], 
                                         {'class': lambda x: x and any(word in str(x).lower() for word in ['title', 'name'])})
                    name = name_elem.get_text(strip=True) if name_elem else link.get_text(strip=True)
                    
                    if not name or len(name) < 2:
                        continue
                    
                    game = Game(
                        name=name[:200],  # Limit name length
                        url=game_url,
                        source=self.name
                    )
                    
                    # Get image
                    img_elem = link.find('img', src=True)
                    if img_elem:
                        game.image_url = urljoin(self.base_url, img_elem['src'])
                    
                    # Get game page for embed
                    game_html = self.scraper.scrape_with_requests(game_url)
                    if game_html:
                        # Coolmath often uses specific iframe patterns
                        soup_game = BeautifulSoup(game_html, 'html.parser')
                        
                        # Look for iframes
                        iframes = soup_game.find_all('iframe', src=True)
                        for iframe in iframes:
                            if 'game' in iframe['src'].lower() or 'play' in iframe['src'].lower():
                                game.iframe_code = str(iframe)
                                break
                        
                        # If no iframe found, construct one
                        if not game.iframe_code:
                            # Extract game ID from URL
                            game_id = game_url.split('/')[-1].replace('0-', '')
                            embed_url = f"https://www.coolmathgames.com/sites/default/files/GamePlayer/{game_id}/index.html"
                            game.iframe_code = f'<iframe src="{embed_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                    
                    self.games.append(game)
                    logger.info(f"Found Coolmath game: {game.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing Coolmath game: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class KongregateScraper(WebsiteScraper):
    """Scraper for Kongregate.com"""
    
    def __init__(self):
        super().__init__("https://www.kongregate.com", "Kongregate")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Kongregate has an API for games
            api_url = "https://www.kongregate.com/games.json"
            
            for page in range(1, 6):  # Get 5 pages
                params = {
                    'page': page,
                    'per_page': 50
                }
                
                response = requests.get(api_url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    for game_data in data.get('games', []):
                        try:
                            game = Game(
                                name=game_data.get('title', ''),
                                url=urljoin(self.base_url, game_data.get('url', '')),
                                source=self.name,
                                image_url=game_data.get('thumb_url', ''),
                                description=game_data.get('description', '')[:500],
                                rating=float(game_data.get('rating', 0)),
                                play_count=int(game_data.get('plays_count', 0))
                            )
                            
                            # Get embed code
                            game_slug = game.url.rstrip('/').split('/')[-1]
                            embed_url = f"https://www.kongregate.com/games/{game_slug}/embed"
                            game.iframe_code = f'<iframe src="{embed_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                            
                            self.games.append(game)
                            logger.info(f"Found Kongregate game: {game.name}")
                            
                        except Exception as e:
                            logger.error(f"Error parsing Kongregate game: {str(e)}")
                            continue
                
                time.sleep(2)  # Delay between API calls
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class GamePixScraper(WebsiteScraper):
    """Scraper for GamePix.com"""
    
    def __init__(self):
        super().__init__("https://www.gamepix.com", "GamePix")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # GamePix has a games API
            api_url = "https://api.gamepix.com/games"
            headers = {
                'User-Agent': self.scraper.ua.random,
                'Accept': 'application/json'
            }
            
            for offset in range(0, 200, 50):  # Get 200 games
                params = {
                    'offset': offset,
                    'limit': 50
                }
                
                response = requests.get(api_url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    for game_data in data.get('games', []):
                        try:
                            game = Game(
                                name=game_data.get('title', ''),
                                url=game_data.get('url', ''),
                                source=self.name,
                                image_url=game_data.get('thumbnail', ''),
                                description=game_data.get('description', '')[:500],
                                category=game_data.get('category', '')
                            )
                            
                            # GamePix provides direct embed code
                            if 'embed_url' in game_data:
                                game.iframe_code = f'<iframe src="{game_data["embed_url"]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                            
                            self.games.append(game)
                            logger.info(f"Found GamePix game: {game.name}")
                            
                        except Exception as e:
                            logger.error(f"Error parsing GamePix game: {str(e)}")
                            continue
                
                time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class CrazyGamesScraper(WebsiteScraper):
    """Scraper for CrazyGames.com"""
    
    def __init__(self):
        super().__init__("https://www.crazygames.com", "CrazyGames")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # CrazyGames has a sitemap with all games
            sitemap_url = "https://www.crazygames.com/sitemap.xml"
            
            response = requests.get(sitemap_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                
                # Extract game URLs from sitemap
                game_urls = []
                for url in soup.find_all('url'):
                    loc = url.find('loc')
                    if loc and '/game/' in loc.text:
                        game_urls.append(loc.text)
                
                # Process each game URL
                for game_url in game_urls[:100]:
                    try:
                        # Get game page
                        game_html = self.scraper.scrape_with_requests(game_url)
                        if not game_html:
                            continue
                        
                        soup_game = BeautifulSoup(game_html, 'html.parser')
                        
                        # Extract game info
                        name_elem = soup_game.find('h1')
                        name = name_elem.get_text(strip=True) if name_elem else ''
                        
                        if not name:
                            continue
                        
                        game = Game(
                            name=name,
                            url=game_url,
                            source=self.name
                        )
                        
                        # Find image
                        img_elem = soup_game.find('meta', property='og:image')
                        if img_elem and img_elem.get('content'):
                            game.image_url = img_elem['content']
                        
                        # Find iframe/embed
                        iframe_elem = soup_game.find('iframe', id='game-iframe')
                        if iframe_elem:
                            game.iframe_code = str(iframe_elem)
                        else:
                            # Look for embed script
                            script_elem = soup_game.find('script', string=lambda x: x and 'embed' in x.lower())
                            if script_elem:
                                # Extract embed URL from script
                                import re
                                embed_pattern = r'"(https?://[^"]+\.(?:html|swf|unity3d))"'
                                matches = re.findall(embed_pattern, script_elem.string)
                                if matches:
                                    game.iframe_code = f'<iframe src="{matches[0]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        
                        self.games.append(game)
                        logger.info(f"Found CrazyGames game: {game.name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing CrazyGames URL {game_url}: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class Y8Scraper(WebsiteScraper):
    """Scraper for Y8.com"""
    
    def __init__(self):
        super().__init__("https://www.y8.com", "Y8 Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Y8 has RSS feed with games
            rss_url = "https://www.y8.com/games/rss"
            
            response = requests.get(rss_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                
                for item in soup.find_all('item')[:80]:
                    try:
                        title = item.find('title')
                        link = item.find('link')
                        
                        if not title or not link:
                            continue
                        
                        game = Game(
                            name=title.get_text(strip=True),
                            url=link.get_text(strip=True),
                            source=self.name
                        )
                        
                        # Get description
                        desc = item.find('description')
                        if desc:
                            game.description = desc.get_text(strip=True)[:500]
                        
                        # Get game page for embed
                        game_html = self.scraper.scrape_with_requests(game.url)
                        if game_html:
                            soup_game = BeautifulSoup(game_html, 'html.parser')
                            
                            # Y8 has specific iframe structure
                            iframe = soup_game.find('iframe', {'id': 'game_iframe'})
                            if iframe:
                                game.iframe_code = str(iframe)
                            else:
                                # Try to find game ID and construct iframe
                                import re
                                game_id_match = re.search(r'/games/([^/]+)', game.url)
                                if game_id_match:
                                    game_id = game_id_match.group(1)
                                    embed_url = f"https://www.y8.com/embed/{game_id}"
                                    game.iframe_code = f'<iframe src="{embed_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                        
                        self.games.append(game)
                        logger.info(f"Found Y8 game: {game.name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing Y8 game: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class ArmorGamesScraper(WebsiteScraper):
    """Scraper for ArmorGames.com"""
    
    def __init__(self):
        super().__init__("https://armorgames.com", "Armor Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Armor Games has a browse API
            for page in range(1, 6):
                url = f"{self.base_url}/browse/ajax?page={page}"
                
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    game_items = soup.find_all('div', class_='game-item')
                    
                    for item in game_items[:60]:
                        try:
                            link_elem = item.find('a', href=True)
                            if not link_elem:
                                continue
                            
                            game_url = urljoin(self.base_url, link_elem['href'])
                            
                            name_elem = item.find('h3') or item.find('div', class_='title')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            if not name:
                                continue
                            
                            game = Game(
                                name=name,
                                url=game_url,
                                source=self.name
                            )
                            
                            # Get image
                            img_elem = item.find('img', src=True)
                            if img_elem:
                                game.image_url = urljoin(self.base_url, img_elem['src'])
                            
                            self.games.append(game)
                            logger.info(f"Found Armor Games game: {game.name}")
                            
                        except Exception as e:
                            logger.error(f"Error processing Armor Games item: {str(e)}")
                            continue
                
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class NitromeScraper(WebsiteScraper):
    """Scraper for Nitrome.com"""
    
    def __init__(self):
        super().__init__("https://www.nitrome.com", "Nitrome")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Nitrome has a games page
            url = f"{self.base_url}/games"
            
            html = self.scraper.scrape_with_requests(url)
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Nitrome has a specific structure
            game_links = soup.find_all('a', href=lambda x: x and '/games/' in x)
            
            for link in game_links[:50]:
                try:
                    game_url = urljoin(self.base_url, link['href'])
                    
                    # Extract name from URL or link
                    name = link.get_text(strip=True)
                    if not name or len(name) < 2:
                        # Try to get from URL
                        name = game_url.split('/')[-1].replace('-', ' ').title()
                    
                    game = Game(
                        name=name,
                        url=game_url,
                        source=self.name
                    )
                    
                    # Get image
                    img_elem = link.find('img', src=True)
                    if img_elem:
                        game.image_url = urljoin(self.base_url, img_elem['src'])
                    
                    self.games.append(game)
                    logger.info(f"Found Nitrome game: {game.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing Nitrome game: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class UnblockedGamesScraper(WebsiteScraper):
    """Scraper for Google Sites unblocked games"""
    
    def __init__(self):
        super().__init__("https://sites.google.com", "Unblocked Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        # List of unblocked games sites
        unblocked_sites = [
            "https://sites.google.com/view/tyronesgameshack",
            "https://sites.google.com/site/unblockedgames66ez",
            "https://sites.google.com/view/classroom6x",
            "https://sites.google.com/view/unblockedgameswtf",
            "https://sites.google.com/view/unblocked-games-76"
        ]
        
        for site_url in unblocked_sites:
            try:
                logger.info(f"Scraping unblocked site: {site_url}")
                html = self.scraper.scrape_with_requests(site_url)
                
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for game links
                links = soup.find_all('a', href=True)
                
                for link in links[:50]:  # Limit per site
                    href = link['href']
                    text = link.get_text(strip=True)
                    
                    # Filter for game-like links
                    if len(text) > 2 and ('game' in text.lower() or 'play' in text.lower() or len(text.split()) < 4):
                        # Check if it's a game URL
                        if not href.startswith(('http', '//')):
                            href = urljoin(site_url, href)
                        
                        # Skip non-game links
                        if any(x in href.lower() for x in ['mailto:', 'javascript:', '#', '?']):
                            continue
                        
                        game = Game(
                            name=text[:100],
                            url=href,
                            source=f"Unblocked ({site_url})"
                        )
                        
                        # Try to find iframe on the linked page
                        try:
                            game_html = self.scraper.scrape_with_requests(href)
                            if game_html:
                                iframes = self.extract_iframes(game_html)
                                if iframes:
                                    game.iframe_code = iframes[0]
                        except:
                            pass
                        
                        self.games.append(game)
                        logger.info(f"Found unblocked game: {game.name}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping unblocked site {site_url}: {str(e)}")
                continue
        
        return self.games

class GitHubGamesScraper(WebsiteScraper):
    """Scraper for GitHub-hosted games"""
    
    def __init__(self):
        super().__init__("https://github.com", "GitHub Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # GitHub topics with games
            game_topics = [
                "https://github.com/topics/html5-game",
                "https://github.com/topics/javascript-game",
                "https://github.com/topics/game-development",
                "https://github.com/topics/phaser-game"
            ]
            
            for topic_url in game_topics:
                try:
                    html = self.scraper.scrape_with_requests(topic_url)
                    if not html:
                        continue
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find repository links
                    repo_links = soup.find_all('a', {'data-hydro-click': True, 'href': lambda x: x and '/topics/' not in x})
                    
                    for link in repo_links[:30]:
                        repo_url = urljoin(self.base_url, link['href'])
                        repo_name = link.get_text(strip=True)
                        
                        # Skip if not a valid repo name
                        if '/' not in repo_name or len(repo_name) < 3:
                            continue
                        
                        # Check if repo has game demo
                        demo_url = f"https://{repo_name.split('/')[0].lower()}.github.io/{repo_name.split('/')[1]}"
                        
                        # Try to access demo
                        try:
                            response = requests.head(demo_url, timeout=5, allow_redirects=True)
                            if response.status_code == 200:
                                game = Game(
                                    name=repo_name,
                                    url=repo_url,
                                    source="GitHub",
                                    embed_url=demo_url,
                                    iframe_code=f'<iframe src="{demo_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                                )
                                self.games.append(game)
                                logger.info(f"Found GitHub game: {repo_name}")
                        except:
                            pass
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping GitHub topic {topic_url}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class HTML5GamesScraper(WebsiteScraper):
    """Scraper for HTML5GameDevs and similar sites"""
    
    def __init__(self):
        super().__init__("https://html5gamedevs.com", "HTML5 Games")
    
    def scrape(self) -> List[Game]:
        logger.info(f"Scraping {self.name}...")
        
        try:
            # Also check other HTML5 game portals
            html5_sites = [
                "https://html5games.com",
                "https://www.html5gaming.com",
                "https://gamejolt.com",
                "https://itch.io/games/html5"
            ]
            
            for site_url in html5_sites:
                try:
                    logger.info(f"Scraping HTML5 site: {site_url}")
                    html = self.scraper.scrape_with_requests(site_url)
                    
                    if not html:
                        continue
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for game elements
                    game_elements = []
                    
                    # Common patterns
                    patterns = [
                        soup.find_all('div', class_=lambda x: x and 'game' in x.lower()),
                        soup.find_all('article', class_=lambda x: x and 'game' in x.lower()),
                        soup.find_all('a', class_=lambda x: x and 'game' in x.lower()),
                    ]
                    
                    for pattern_result in patterns:
                        game_elements.extend(pattern_result)
                    
                    for element in game_elements[:40]:
                        try:
                            # Find link
                            link_elem = element.find('a', href=True)
                            if not link_elem:
                                continue
                            
                            game_url = urljoin(site_url, link_elem['href'])
                            
                            # Find name
                            name_elem = element.find(['h2', 'h3', 'h4', 'div', 'span'], 
                                                   class_=lambda x: x and any(word in str(x).lower() for word in ['title', 'name', 'game-title']))
                            name = name_elem.get_text(strip=True) if name_elem else link_elem.get_text(strip=True)
                            
                            if not name or len(name) < 2:
                                continue
                            
                            game = Game(
                                name=name[:150],
                                url=game_url,
                                source=f"HTML5 ({site_url})"
                            )
                            
                            # Find image
                            img_elem = element.find('img', src=True)
                            if img_elem:
                                game.image_url = urljoin(site_url, img_elem['src'])
                            
                            self.games.append(game)
                            logger.info(f"Found HTML5 game: {game.name}")
                            
                        except Exception as e:
                            logger.error(f"Error processing HTML5 game element: {str(e)}")
                            continue
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping HTML5 site {site_url}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {str(e)}")
        
        return self.games

class MainGameScraper:
    """Main orchestrator for all scrapers"""
    
    def __init__(self):
        self.scrapers = [
            PokiScraper(),
            CoolmathScraper(),
            KongregateScraper(),
            GamePixScraper(),
            CrazyGamesScraper(),
            Y8Scraper(),
            ArmorGamesScraper(),
            NitromeScraper(),
            UnblockedGamesScraper(),
            GitHubGamesScraper(),
            HTML5GamesScraper()
        ]
        self.all_games = []
        self.scraping_stats = {}
    
    def run_scrapers_parallel(self):
        """Run all scrapers in parallel"""
        logger.info(f"Starting parallel scraping of {len(self.scrapers)} websites...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for scraper in self.scrapers:
                future = executor.submit(self.run_single_scraper, scraper)
                futures.append((scraper, future))
            
            for scraper, future in futures:
                try:
                    games = future.result(timeout=600)  # 10 minute timeout per scraper
                    self.all_games.extend(games)
                    self.scraping_stats[scraper.name] = len(games)
                    logger.info(f"{scraper.name}: Found {len(games)} games")
                except Exception as e:
                    logger.error(f"Scraper {scraper.name} failed: {str(e)}")
                    self.scraping_stats[scraper.name] = 0
    
    def run_single_scraper(self, scraper: WebsiteScraper):
        """Run a single scraper"""
        return scraper.scrape()
    
    def deduplicate_games(self):
        """Remove duplicate games based on name and URL"""
        logger.info("Deduplicating games...")
        
        seen = set()
        unique_games = []
        
        for game in self.all_games:
            # Create a unique identifier
            game_id = f"{game.name.lower()}_{game.url}"
            if game_id not in seen:
                seen.add(game_id)
                unique_games.append(game)
        
        logger.info(f"Removed {len(self.all_games) - len(unique_games)} duplicates")
        self.all_games = unique_games
    
    def save_results(self):
        """Save all games to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_scraper/output/games_{timestamp}.json"
        
        # Convert games to dictionaries
        games_dict = [asdict(game) for game in self.all_games]
        
        # Save to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'total_games': len(games_dict),
                    'scraped_at': datetime.now().isoformat(),
                    'sources': self.scraping_stats
                },
                'games': games_dict
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(games_dict)} games to {filename}")
        
        # Also save a summary CSV
        import csv
        csv_filename = f"game_scraper/output/games_summary_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'url', 'source', 'has_embed'])
            writer.writeheader()
            for game in games_dict:
                writer.writerow({
                    'name': game['name'],
                    'url': game['url'],
                    'source': game['source'],
                    'has_embed': bool(game['iframe_code'])
                })
        
        return filename
    
    def print_stats(self):
        """Print scraping statistics"""
        logger.info("=" * 60)
        logger.info("SCRAPING STATISTICS")
        logger.info("=" * 60)
        
        total_games = len(self.all_games)
        games_with_embed = sum(1 for g in self.all_games if g.iframe_code)
        
        logger.info(f"Total games found: {total_games}")
        logger.info(f"Games with embed code: {games_with_embed} ({games_with_embed/total_games*100:.1f}%)")
        
        logger.info("\nBy source:")
        for source, count in self.scraping_stats.items():
            logger.info(f"  {source}: {count} games")
        
        # Top 10 games
        logger.info("\nSample games collected:")
        for i, game in enumerate(self.all_games[:10], 1):
            logger.info(f"  {i}. {game.name} ({game.source})")
        
        logger.info("=" * 60)

def main():
    """Main execution function"""
    print("=" * 60)
    print("KALI LINUX ADVANCED GAME SCRAPER")
    print("Scraping 10+ gaming websites thoroughly")
    print("=" * 60)
    
    # Check if running as root (common in Kali)
    if os.geteuid() == 0:
        print("[!] Warning: Running as root. Consider running as regular user.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Start Tor service
    print("[+] Starting Tor service for anonymity...")
    os.system("sudo systemctl start tor 2>/dev/null")
    
    # Create main scraper
    scraper = MainGameScraper()
    
    try:
        # Run all scrapers
        print("[+] Starting comprehensive game scraping...")
        scraper.run_scrapers_parallel()
        
        # Process results
        print("[+] Processing results...")
        scraper.deduplicate_games()
        
        # Save results
        print("[+] Saving results...")
        output_file = scraper.save_results()
        
        # Print statistics
        scraper.print_stats()
        
        print(f"\n[✅] Scraping complete!")
        print(f"[📁] Results saved to: {output_file}")
        print(f"[🎮] Total unique games: {len(scraper.all_games)}")
        
        # Offer to create a web interface
        create_web = input("\nCreate a web interface to browse games? (y/n): ")
        if create_web.lower() == 'y':
            create_web_interface(scraper.all_games)
        
    except KeyboardInterrupt:
        print("\n[!] Scraping interrupted by user")
        # Save what we have so far
        if scraper.all_games:
            scraper.save_results()
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        import traceback
        traceback.print_exc()

def create_web_interface(games):
    """Create a simple web interface to browse games"""
    print("[+] Creating web interface...")
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Game Collection Browser</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
            }
            .container { 
                max-width: 1400px; 
                margin: 0 auto; 
                padding: 20px; 
            }
            header {
                background: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
                text-align: center;
            }
            h1 { 
                color: #2d3748; 
                margin-bottom: 0.5rem;
                font-size: 2.5rem;
            }
            .stats {
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-top: 1rem;
                flex-wrap: wrap;
            }
            .stat-box {
                background: #4c51bf;
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 10px;
                font-weight: bold;
            }
            .filters {
                background: rgba(255, 255, 255, 0.95);
                padding: 1.5rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                align-items: center;
            }
            .search-box {
                flex: 1;
                min-width: 300px;
            }
            input, select {
                padding: 0.75rem;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 1rem;
                width: 100%;
                transition: border-color 0.3s;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #4c51bf;
            }
            .games-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1.5rem;
                margin-bottom: 3rem;
            }
            .game-card {
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
            }
            .game-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0,0,0,0.15);
            }
            .game-image {
                height: 180px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 3rem;
                position: relative;
                overflow: hidden;
            }
            .game-image img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .game-info {
                padding: 1.5rem;
            }
            .game-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #2d3748;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .game-source {
                color: #4c51bf;
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 1rem;
                display: inline-block;
                background: #edf2f7;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
            }
            .game-description {
                color: #718096;
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 1rem;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .game-actions {
                display: flex;
                gap: 0.5rem;
            }
            .btn {
                padding: 0.5rem 1rem;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
                text-align: center;
                flex: 1;
            }
            .btn-play {
                background: #4c51bf;
                color: white;
            }
            .btn-play:hover {
                background: #434190;
            }
            .btn-view {
                background: #edf2f7;
                color: #4a5568;
            }
            .btn-view:hover {
                background: #e2e8f0;
            }
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }
            .modal-content {
                background: white;
                border-radius: 15px;
                width: 90%;
                max-width: 1000px;
                max-height: 90vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            .modal-header {
                padding: 1.5rem;
                background: #4c51bf;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .modal-title {
                font-size: 1.5rem;
                font-weight: 600;
            }
            .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 2rem;
                cursor: pointer;
                line-height: 1;
            }
            .game-frame {
                flex: 1;
                min-height: 500px;
                border: none;
            }
            .loading {
                text-align: center;
                padding: 2rem;
                color: #718096;
            }
            .pagination {
                display: flex;
                justify-content: center;
                gap: 0.5rem;
                margin-top: 2rem;
            }
            .page-btn {
                padding: 0.5rem 1rem;
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .page-btn:hover {
                background: #edf2f7;
            }
            .page-btn.active {
                background: #4c51bf;
                color: white;
                border-color: #4c51bf;
            }
            footer {
                text-align: center;
                padding: 2rem;
                color: white;
                margin-top: 2rem;
            }
            @media (max-width: 768px) {
                .games-grid {
                    grid-template-columns: 1fr;
                }
                .filters {
                    flex-direction: column;
                }
                .search-box {
                    min-width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🎮 Game Collection Browser</h1>
                <p>Browse thousands of games scraped from multiple sources</p>
                <div class="stats" id="stats">
                    <!-- Stats will be populated by JavaScript -->
                </div>
            </header>
            
            <div class="filters">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search games...">
                </div>
                <select id="sourceFilter">
                    <option value="">All Sources</option>
                    <!-- Sources will be populated by JavaScript -->
                </select>
                <select id="sortSelect">
                    <option value="name">Sort by Name (A-Z)</option>
                    <option value="name-desc">Sort by Name (Z-A)</option>
                    <option value="source">Sort by Source</option>
                </select>
            </div>
            
            <div class="games-grid" id="gamesGrid">
                <!-- Games will be populated by JavaScript -->
            </div>
            
            <div class="pagination" id="pagination">
                <!-- Pagination will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- Game Modal -->
        <div class="modal" id="gameModal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title" id="modalTitle">Game Title</div>
                    <button class="close-btn" id="closeModal">&times;</button>
                </div>
                <iframe class="game-frame" id="gameFrame" sandbox="allow-same-origin allow-scripts allow-popups allow-forms" allowfullscreen></iframe>
            </div>
        </div>
        
        <footer>
            <p>Scraped using Kali Linux Advanced Game Scraper | Total games: <span id="totalGames">0</span></p>
        </footer>
        
        <script>
            // Games data will be injected here
            const gamesData = %GAMES_DATA%;
            
            // Initialize the application
            document.addEventListener('DOMContentLoaded', function() {
                const app = new GameBrowser(gamesData);
                app.init();
            });
            
            class GameBrowser {
                constructor(games) {
                    this.games = games;
                    this.filteredGames = [...games];
                    this.currentPage = 1;
                    this.gamesPerPage = 12;
                    this.currentSource = '';
                    this.currentSort = 'name';
                    this.currentSearch = '';
                }
                
                init() {
                    this.renderStats();
                    this.populateSources();
                    this.renderGames();
                    this.setupEventListeners();
                }
                
                renderStats() {
                    const statsElement = document.getElementById('stats');
                    const totalGames = this.games.length;
                    const gamesWithEmbed = this.games.filter(g => g.iframe_code).length;
                    const sourcesCount = new Set(this.games.map(g => g.source)).size;
                    
                    statsElement.innerHTML = `
                        <div class="stat-box">Total Games: ${totalGames}</div>
                        <div class="stat-box">With Embed: ${gamesWithEmbed}</div>
                        <div class="stat-box">Sources: ${sourcesCount}</div>
                    `;
                    
                    document.getElementById('totalGames').textContent = totalGames;
                }
                
                populateSources() {
                    const sourceFilter = document.getElementById('sourceFilter');
                    const sources = [...new Set(this.games.map(g => g.source))].sort();
                    
                    sources.forEach(source => {
                        const option = document.createElement('option');
                        option.value = source;
                        option.textContent = source;
                        sourceFilter.appendChild(option);
                    });
                }
                
                filterAndSortGames() {
                    // Apply search filter
                    let filtered = this.games;
                    
                    if (this.currentSearch) {
                        const searchTerm = this.currentSearch.toLowerCase();
                        filtered = filtered.filter(game => 
                            game.name.toLowerCase().includes(searchTerm) ||
                            game.source.toLowerCase().includes(searchTerm) ||
                            (game.description && game.description.toLowerCase().includes(searchTerm))
                        );
                    }
                    
                    // Apply source filter
                    if (this.currentSource) {
                        filtered = filtered.filter(game => game.source === this.currentSource);
                    }
                    
                    // Apply sorting
                    filtered.sort((a, b) => {
                        switch(this.currentSort) {
                            case 'name':
                                return a.name.localeCompare(b.name);
                            case 'name-desc':
                                return b.name.localeCompare(a.name);
                            case 'source':
                                return a.source.localeCompare(b.source) || a.name.localeCompare(b.name);
                            default:
                                return 0;
                        }
                    });
                    
                    this.filteredGames = filtered;
                    this.currentPage = 1;
                }
                
                renderGames() {
                    this.filterAndSortGames();
                    
                    const gamesGrid = document.getElementById('gamesGrid');
                    const pagination = document.getElementById('pagination');
                    
                    // Calculate pagination
                    const totalPages = Math.ceil(this.filteredGames.length / this.gamesPerPage);
                    const startIndex = (this.currentPage - 1) * this.gamesPerPage;
                    const endIndex = startIndex + this.gamesPerPage;
                    const gamesToShow = this.filteredGames.slice(startIndex, endIndex);
                    
                    // Clear grid
                    gamesGrid.innerHTML = '';
                    
                    // Render games
                    gamesToShow.forEach(game => {
                        const gameCard = this.createGameCard(game);
                        gamesGrid.appendChild(gameCard);
                    });
                    
                    // Render pagination
                    this.renderPagination(pagination, totalPages);
                    
                    // Update stats
                    this.renderStats();
                }
                
                createGameCard(game) {
                    const card = document.createElement('div');
                    card.className = 'game-card';
                    
                    // Truncate description if too long
                    let description = game.description || 'No description available';
                    if (description.length > 150) {
                        description = description.substring(0, 150) + '...';
                    }
                    
                    card.innerHTML = `
                        <div class="game-image">
                            ${game.image_url ? 
                                `<img src="${game.image_url}" alt="${game.name}" onerror="this.style.display='none'">` : 
                                '🎮'}
                        </div>
                        <div class="game-info">
                            <div class="game-title" title="${game.name}">${game.name}</div>
                            <div class="game-source">${game.source}</div>
                            <div class="game-description">${description}</div>
                            <div class="game-actions">
                                ${game.iframe_code ? 
                                    `<button class="btn btn-play" data-game-url="${game.url}" data-game-name="${game.name}">Play Now</button>` :
                                    `<a href="${game.url}" target="_blank" class="btn btn-view">View Game</a>`
                                }
                            </div>
                        </div>
                    `;
                    
                    // Add event listener for play button
                    const playBtn = card.querySelector('.btn-play');
                    if (playBtn) {
                        playBtn.addEventListener('click', () => this.openGameModal(game));
                    }
                    
                    return card;
                }
                
                renderPagination(container, totalPages) {
                    container.innerHTML = '';
                    
                    if (totalPages <= 1) return;
                    
                    // Previous button
                    const prevBtn = document.createElement('button');
                    prevBtn.className = 'page-btn';
                    prevBtn.innerHTML = '&laquo;';
                    prevBtn.disabled = this.currentPage === 1;
                    prevBtn.addEventListener('click', () => {
                        if (this.currentPage > 1) {
                            this.currentPage--;
                            this.renderGames();
                        }
                    });
                    container.appendChild(prevBtn);
                    
                    // Page buttons
                    const maxButtons = 5;
                    let startPage = Math.max(1, this.currentPage - Math.floor(maxButtons / 2));
                    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
                    
                    if (endPage - startPage + 1 < maxButtons) {
                        startPage = Math.max(1, endPage - maxButtons + 1);
                    }
                    
                    for (let i = startPage; i <= endPage; i++) {
                        const pageBtn = document.createElement('button');
                        pageBtn.className = `page-btn ${i === this.currentPage ? 'active' : ''}`;
                        pageBtn.textContent = i;
                        pageBtn.addEventListener('click', () => {
                            this.currentPage = i;
                            this.renderGames();
                        });
                        container.appendChild(pageBtn);
                    }
                    
                    // Next button
                    const nextBtn = document.createElement('button');
                    nextBtn.className = 'page-btn';
                    nextBtn.innerHTML = '&raquo;';
                    nextBtn.disabled = this.currentPage === totalPages;
                    nextBtn.addEventListener('click', () => {
                        if (this.currentPage < totalPages) {
                            this.currentPage++;
                            this.renderGames();
                        }
                    });
                    container.appendChild(nextBtn);
                }
                
                openGameModal(game) {
                    const modal = document.getElementById('gameModal');
                    const modalTitle = document.getElementById('modalTitle');
                    const gameFrame = document.getElementById('gameFrame');
                    
                    modalTitle.textContent = game.name;
                    
                    // Extract src from iframe code or use game URL
                    let gameUrl = game.url;
                    if (game.iframe_code) {
                        const match = game.iframe_code.match(/src="([^"]+)"/);
                        if (match) {
                            gameUrl = match[1];
                        }
                    }
                    
                    gameFrame.src = gameUrl;
                    modal.style.display = 'flex';
                }
                
                setupEventListeners() {
                    // Search input
                    document.getElementById('searchInput').addEventListener('input', (e) => {
                        this.currentSearch = e.target.value;
                        this.renderGames();
                    });
                    
                    // Source filter
                    document.getElementById('sourceFilter').addEventListener('change', (e) => {
                        this.currentSource = e.target.value;
                        this.renderGames();
                    });
                    
                    // Sort select
                    document.getElementById('sortSelect').addEventListener('change', (e) => {
                        this.currentSort = e.target.value;
                        this.renderGames();
                    });
                    
                    // Close modal
                    document.getElementById('closeModal').addEventListener('click', () => {
                        const modal = document.getElementById('gameModal');
                        const gameFrame = document.getElementById('gameFrame');
                        modal.style.display = 'none';
                        gameFrame.src = '';
                    });
                    
                    // Close modal when clicking outside
                    document.getElementById('gameModal').addEventListener('click', (e) => {
                        if (e.target === document.getElementById('gameModal')) {
                            const modal = document.getElementById('gameModal');
                            const gameFrame = document.getElementById('gameFrame');
                            modal.style.display = 'none';
                            gameFrame.src = '';
                        }
                    });
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Convert games to JSON for JavaScript
    games_json = json.dumps([asdict(game) for game in games], ensure_ascii=False)
    
    # Replace placeholder with actual games data
    html_content = html_content.replace('%GAMES_DATA%', games_json)
    
    # Save HTML file
    with open('game_scraper/output/game_browser.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[🌐] Web interface created: game_scraper/output/game_browser.html")
    print(f"[🔗] Open it in your browser to browse {len(games)} games!")

if __name__ == "__main__":
    main()