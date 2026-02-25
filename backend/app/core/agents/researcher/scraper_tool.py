import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import re

def scrape_url(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Scrapes a URL and returns the title and full text content.
    Optimized for memory efficiency (no headless browser).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()
            
        title = soup.title.string if soup.title else ""
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text size to prevent memory spikes if site is massive
        # 50k characters is usually enough for a deep article but safe for RAM
        max_chars = 50000
        if len(text) > max_chars:
             text = text[:max_chars] + "\n... [TRUNCATED]"

        return {
            "title": title.strip() if title else "No Title",
            "url": url,
            "content": text,
            "source": "deep_scraper"
        }
    except Exception as e:
        print(f"[Scraper] Error scraping {url}: {e}")
        return None

if __name__ == "__main__":
    # Test block
    import sys
    import json
    if len(sys.argv) > 1:
        result = scrape_url(sys.argv[1])
        print(json.dumps(result if result else {}))
