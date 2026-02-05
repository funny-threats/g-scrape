# game_scraper/update_proxies.py

import requests
import concurrent.futures
from datetime import datetime

def fetch_proxies_from_source(url, proxy_type="http"):
    """Fetch proxies from a specific source"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = []
            lines = response.text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        proxies.append(f"{proxy_type}://{line}")
            return proxies
    except:
        pass
    return []

def test_proxy(proxy, test_url="http://httpbin.org/ip"):
    """Test if a proxy is working"""
    try:
        response = requests.get(
            test_url,
            proxies={"http": proxy, "https": proxy},
            timeout=5
        )
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def main():
    print("Updating proxy list...")
    
    # Sources for free proxies
    proxy_sources = [
        # HTTP/HTTPS proxies
        ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", "http"),
        ("https://www.proxy-list.download/api/v1/get?type=http", "http"),
        ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "http"),
        
        # SOCKS proxies
        ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all", "socks4"),
        ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all", "socks5"),
        ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt", "socks4"),
        ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "socks5"),
    ]
    
    all_proxies = []
    
    # Fetch proxies from all sources
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for url, proxy_type in proxy_sources:
            future = executor.submit(fetch_proxies_from_source, url, proxy_type)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            proxies = future.result()
            if proxies:
                all_proxies.extend(proxies)
    
    # Remove duplicates
    all_proxies = list(set(all_proxies))
    print(f"Found {len(all_proxies)} unique proxies")
    
    # Test proxies (sample testing for speed)
    print("Testing proxies (this may take a while)...")
    working_proxies = []
    
    # Test a sample of proxies (or all if not too many)
    test_sample = all_proxies[:100] if len(all_proxies) > 100 else all_proxies
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in test_sample}
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    working_proxies.append(proxy)
                    print(f"✓ Working proxy: {proxy}")
            except:
                pass
    
    # Save working proxies
    with open("game_scraper/data/proxies.txt", "w") as f:
        f.write(f"# Updated: {datetime.now().isoformat()}\n")
        f.write(f"# Total working proxies: {len(working_proxies)}\n\n")
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
    
    print(f"\nSaved {len(working_proxies)} working proxies to game_scraper/data/proxies.txt")
    
    # Also save all proxies for reference
    with open("game_scraper/data/all_proxies.txt", "w") as f:
        f.write(f"# All proxies found: {datetime.now().isoformat()}\n")
        f.write(f"# Total proxies: {len(all_proxies)}\n\n")
        for proxy in all_proxies:
            f.write(f"{proxy}\n")

if __name__ == "__main__":
    main()