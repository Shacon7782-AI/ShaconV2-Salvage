import requests
import trafilatura
from selectolax.lexbor import LexborHTMLParser
from typing import Optional, Dict, Any
import urllib3

# Disable insecure warnings for self-signed or legacy sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZeroBloatScraper:
    """
    High-efficiency ingestion engine utilizing C-based parsers (Selectolax)
    and Trafilatura for robust main-content extraction.
    Ensures 0-RAM bloat and high-speed execution.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def scrape_url(self, url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
        try:
            # 1. Fetch content with session persistence
            response = self.session.get(url, timeout=timeout, verify=False)
            response.raise_for_status()
            html = response.text

            # 2. Extract metadata using Lexbor (Fastest C-Parser)
            parser = LexborHTMLParser(html)
            title_node = parser.css_first('title')
            title = title_node.text().strip() if title_node else "No Title"

            # 3. Extract main content using Trafilatura (Sophisticated noise removal)
            # Trafilatura handles boilerplate (nav, footer, ads) better than raw BS4/Selectolax
            content = trafilatura.extract(
                html, 
                include_comments=False, 
                include_tables=True,
                no_fallback=False
            )

            if not content:
                # Fallback to Selectolax raw text if Trafilatura fails
                content = parser.text(separator='\n', strip=True)

            # 4. Enforce Zero-Bloat constraints
            max_chars = 60000
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... [CONTENT TRUNCATED FOR RAM SAFETY]"

            return {
                "title": title,
                "url": url,
                "content": content,
                "source": "zero_bloat_ingestion_v2"
            }
        except Exception as e:
            print(f"[ZERO-BLOAT ERROR] Failed to ingest {url}: {e}")
            return None

# Global Singleton for connection pooling
scraper = ZeroBloatScraper()

def scrape_url(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """Legacy wrapper for backward compatibility."""
    return scraper.scrape_url(url, timeout)

if __name__ == "__main__":
    # Test block
    import sys
    import json
    if len(sys.argv) > 1:
        result = scrape_url(sys.argv[1])
        print(json.dumps(result if result else {}, indent=2))
