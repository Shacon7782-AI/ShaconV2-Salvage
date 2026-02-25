"""
Parallel Crawler Engine for NotebookLM
Optimized for high-speed, non-blocking ingestion of all notebooks, sources, and notes.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Enforce UTF-8 for Windows shells
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from patchright.async_api import async_playwright
from browser_utils import BrowserFactory, StealthUtils
from config import HOME_PAGE_SELECTORS, INTERNAL_SELECTORS, PAGE_LOAD_TIMEOUT

CONCURRENCY_LIMIT = 3 # Avoid Google Drive/Auth rate limits

async def process_notebook(browser_context, target_title: str, notebook_data_list: list):
    """Processes a single notebook in a new tab."""
    page = await browser_context.new_page()
    print(f"  [START] Opening: {target_title}")
    
    try:
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Find and click the notebook
        notebook_selector = f"{HOME_PAGE_SELECTORS['notebook_row']}, {HOME_PAGE_SELECTORS['notebook_card']}"
        await page.wait_for_selector(notebook_selector, timeout=30000)
        
        items = await page.query_selector_all(notebook_selector)
        found = False
        for item in items:
            title_el = await item.query_selector(HOME_PAGE_SELECTORS["notebook_title"])
            title = (await title_el.inner_text()).strip() if title_el else (await item.inner_text()).split("\n")[0].strip()
            
            if title == target_title:
                await item.click()
                found = True
                break
        
        if not found:
            print(f"  [ERROR] Not found: {target_title}")
            return

        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(4) 
        
        notebook_data = {
            "name": target_title,
            "url": page.url,
            "ingested_at": datetime.now().isoformat(),
            "sources": [],
            "notes": []
        }
        
        # Extract Sources
        sources = await page.query_selector_all(INTERNAL_SELECTORS["source_item"])
        for source_el in sources:
            try:
                source_name = (await source_el.inner_text()).split("\n")[0].strip()
                await source_el.click()
                await asyncio.sleep(2)
                
                content_el = await page.query_selector(INTERNAL_SELECTORS["content_area"])
                content = (await content_el.inner_text()).strip() if content_el else "[Empty]"
                
                notebook_data["sources"].append({"title": source_name, "content": content})
            except Exception as e:
                print(f"    [WARN] Source error ({target_title}): {e}")
        
        notebook_data_list.append(notebook_data)
        print(f"  [OK] Finished: {target_title}")
        
    except Exception as e:
        print(f"  [FAIL] {target_title}: {e}")
    finally:
        await page.close()

async def parallel_crawl(output_file: str = "global_notebook_dump.json"):
    print("[INIT] Starting Parallel NotebookLM Crawl...")
    
    async with async_playwright() as p:
        context = await BrowserFactory.launch_persistent_context(p, headless=False)
        
        # 1. DISCOVERY
        page = await context.new_page()
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        notebook_selector = f"{HOME_PAGE_SELECTORS['notebook_row']}, {HOME_PAGE_SELECTORS['notebook_card']}"
        await page.wait_for_selector(notebook_selector, timeout=30000)
        
        items = await page.query_selector_all(notebook_selector)
        notebook_titles = []
        for item in items:
            is_create = await item.evaluate("node => node.classList.contains('create-new-action-button') || node.innerText.includes('Create new')")
            if is_create: continue
            title_el = await item.query_selector(HOME_PAGE_SELECTORS["notebook_title"])
            title = (await title_el.inner_text()).strip() if title_el else (await item.inner_text()).split("\n")[0].strip()
            if title: notebook_titles.append(title)
        
        await page.close()
        print(f"[OK] Discovered {len(notebook_titles)} notebooks.")
        
        # 2. PARALLEL PROCESSING (With Rate-Limiting & Session Rotation)
        BATCH_SIZE = 5
        COOL_DOWN = 15  # Seconds between batches to avoid NotebookLM freezes
        
        results = []
        
        for i in range(0, len(notebook_titles), BATCH_SIZE):
            batch = notebook_titles[i:i + BATCH_SIZE]
            print(f"[BATCH] Processing {i//BATCH_SIZE + 1} ({len(batch)} notebooks)...")
            
            semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
            async def sem_process(title):
                async with semaphore:
                    await process_notebook(context, title, results)
            
            tasks = [sem_process(title) for title in batch]
            await asyncio.gather(*tasks)
            
            if i + BATCH_SIZE < len(notebook_titles):
                print(f"[WAIT] Rate-limiting active. Cooling down for {COOL_DOWN}s...")
                await asyncio.sleep(COOL_DOWN)
                
                # Session Rotation Logic (Refreshing context after each batch)
                print("[ROTATE] Refreshing browser context...")
                await context.close()
                context = await BrowserFactory.launch_persistent_context(p, headless=False)
        
        # 3. SAVE
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"[DONE] Crawl complete. {len(results)} notebooks ingested.")
        await context.close()

if __name__ == "__main__":
    asyncio.run(parallel_crawl())
