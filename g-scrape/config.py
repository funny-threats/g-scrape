# game_scraper/config.py

CONFIG = {
    "scraping": {
        "max_workers": 5,
        "request_timeout": 30,
        "delay_range": [1, 3],  # Random delay between requests in seconds
        "retry_attempts": 3,
        "user_agents_file": "game_scraper/data/user_agents.txt",
        "proxies_file": "game_scraper/data/proxies.txt",
        "tor_enabled": True,
        "tor_port": 9050,
        "use_selenium": True,
        "use_cloudscraper": True,
        "max_games_per_source": 200,
    },
    
    "websites": {
        # Primary gaming websites
        "poki": {
            "enabled": True,
            "url": "https://poki.com",
            "type": "cloudscraper",
            "max_pages": 10,
            "concurrent_requests": 3,
        },
        "coolmath": {
            "enabled": True,
            "url": "https://www.coolmathgames.com",
            "type": "requests",
            "max_pages": 20,
        },
        "kongregate": {
            "enabled": True,
            "url": "https://www.kongregate.com",
            "type": "api",
            "api_url": "https://www.kongregate.com/games.json",
            "pages": 10,
            "games_per_page": 50,
        },
        "gamepix": {
            "enabled": True,
            "url": "https://www.gamepix.com",
            "type": "api",
            "api_url": "https://api.gamepix.com/games",
            "max_games": 500,
        },
        "crazygames": {
            "enabled": True,
            "url": "https://www.crazygames.com",
            "type": "selenium",
            "use_sitemap": True,
            "sitemap_url": "https://www.crazygames.com/sitemap.xml",
        },
        "y8": {
            "enabled": True,
            "url": "https://www.y8.com",
            "type": "rss",
            "rss_url": "https://www.y8.com/games/rss",
            "max_games": 300,
        },
        "armorgames": {
            "enabled": True,
            "url": "https://armorgames.com",
            "type": "requests",
            "ajax_pagination": True,
            "pages": 15,
        },
        "nitrome": {
            "enabled": True,
            "url": "https://www.nitrome.com",
            "type": "requests",
            "max_games": 100,
        },
        # Unblocked games websites
        "unblocked": {
            "enabled": True,
            "sites": [
                "https://sites.google.com/view/tyronesgameshack",
                "https://sites.google.com/site/unblockedgames66ez",
                "https://sites.google.com/view/classroom6x",
                "https://sites.google.com/view/unblockedgameswtf",
                "https://sites.google.com/view/unblocked-games-76",
                "https://sites.google.com/view/unblocked-games-24h",
                "https://sites.google.com/view/unblocked-games-911",
            ],
            "type": "requests",
            "max_games_per_site": 50,
        },
        # HTML5 game portals
        "html5_portals": {
            "enabled": True,
            "sites": [
                "https://html5games.com",
                "https://www.html5gaming.com",
                "https://gamejolt.com",
                "https://itch.io/games/html5",
                "https://www.gamedistribution.com",
                "https://www.gamezoo.com",
            ],
            "type": "mixed",
            "max_games_per_site": 100,
        },
        # GitHub game repositories
        "github": {
            "enabled": True,
            "topics": [
                "html5-game",
                "javascript-game",
                "game-development",
                "phaser-game",
                "threejs-game",
                "webgl-game",
            ],
            "type": "api",
            "max_repos": 200,
        },
        # Additional sources
        "additional_sources": {
            "enabled": True,
            "sites": [
                "https://www.miniclip.com/games/en/",
                "https://www.agame.com",
                "https://www.games.co.uk",
                "https://www.addictinggames.com",
                "https://www.primarygames.com",
                "https://www.friv.com",
                "https://www.kizi.com",
            ],
            "type": "mixed",
            "max_games_per_site": 150,
        },
    },
    
    "output": {
        "json_file": "game_scraper/output/games_collection.json",
        "csv_file": "game_scraper/output/games_summary.csv",
        "sqlite_db": "game_scraper/output/games.db",
        "web_interface": True,
        "compress_output": True,
        "backup_older_versions": True,
        "max_backups": 10,
    },
    
    "database": {
        "enabled": True,
        "type": "sqlite",
        "filename": "game_scraper/output/games.db",
        "tables": {
            "games": "games",
            "sources": "sources",
            "categories": "categories",
            "scraping_log": "scraping_log",
        },
    },
    
    "monitoring": {
        "log_level": "INFO",
        "log_file": "game_scraper/logs/scraping.log",
        "error_log_file": "game_scraper/logs/errors.log",
        "performance_log": "game_scraper/logs/performance.log",
        "send_telemetry": False,
        "save_screenshots": False,
        "debug_mode": False,
    },
    
    "security": {
        "respect_robots_txt": True,
        "rate_limiting": True,
        "max_requests_per_minute": 60,
        "rotate_user_agents": True,
        "rotate_proxies": True,
        "use_tor": True,
        "verify_ssl": False,  # Set to True in production
        "timeout_handling": True,
    },
}