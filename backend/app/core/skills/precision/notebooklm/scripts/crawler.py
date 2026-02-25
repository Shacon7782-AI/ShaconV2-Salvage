"""
Crawler Engine for NotebookLM
Performs mass-ingestion of all notebooks, sources, and notes.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Enforce UTF-8 for Windows shells
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from patchright.sync_api import sync_playwright
from browser_utils import BrowserFactory, StealthUtils
from config import HOME_PAGE_SELECTORS, INTERNAL_SELECTORS, PAGE_LOAD_TIMEOUT

def crawl_notebook_library(output_file: str = "global_notebook_dump.json"):
    print("[INIT] Starting Global NotebookLM Crawl...")
    
    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=False)
        page = context.new_page()
        
        try:
            # 1. DISCOVERY PHASE
            print("[PHASE 1] Discovering Library...")
            page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for either row or card
            print("  [WAIT] Waiting for notebooks to load...")
            notebook_selector = f"{HOME_PAGE_SELECTORS['notebook_row']}, {HOME_PAGE_SELECTORS['notebook_card']}"
            page.wait_for_selector(notebook_selector, timeout=30000)
            
            # Identify all titles first to avoid stale elements
            notebook_items = page.query_selector_all(notebook_selector)
            notebook_titles = []
            
            for item in notebook_items:
                is_create_btn = item.evaluate("node => node.classList.contains('create-new-action-button') || node.innerText.includes('Create new')")
                if is_create_btn: continue
                
                title_el = item.query_selector(HOME_PAGE_SELECTORS["notebook_title"])
                title = title_el.inner_text().strip() if title_el else item.inner_text().split("\n")[0].strip()
                if title:
                    notebook_titles.append(title)

            print(f"  [OK] Found {len(notebook_titles)} valid notebooks in queue")
            
            # 2. EXTRACTION PHASE
            results = []
            for i, target_title in enumerate(notebook_titles):
                print(f"\n[PHASE 2] Processing ({i+1}/{len(notebook_titles)}): {target_title}")
                
                # Re-navigate to home to ensure fresh state
                page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
                page.wait_for_selector(notebook_selector, timeout=30000)
                
                # Find the element matching the title
                found = False
                current_items = page.query_selector_all(notebook_selector)
                for item in current_items:
                    title_el = item.query_selector(HOME_PAGE_SELECTORS["notebook_title"])
                    title = title_el.inner_text().strip() if title_el else item.inner_text().split("\n")[0].strip()
                    
                    if title == target_title:
                        print(f"  [OK] Found and entering: {title}")
                        item.click()
                        found = True
                        break
                
                if not found:
                    print(f"  [ERROR] Could not find notebook '{target_title}' on home page. Skipping.")
                    continue

                # Inside the notebook
                page.wait_for_load_state("domcontentloaded")
                time.sleep(4) # Allow internal load
                
                notebook_data = {
                    "name": target_title,
                    "url": page.url,
                    "ingested_at": datetime.now().isoformat(),
                    "sources": [],
                    "notes": []
                }
                
                # Extract Sources
                print("  [SOURCE] Extracting sources...")
                sources = page.query_selector_all(INTERNAL_SELECTORS["source_item"])
                for s_idx, source_el in enumerate(sources):
                    try:
                        source_name = source_el.inner_text().split("\n")[0].strip()
                        print(f"    - Reading Source: {source_name}")
                        
                        source_el.click()
                        time.sleep(2)
                        
                        content_el = page.query_selector(INTERNAL_SELECTORS["content_area"])
                        content = content_el.inner_text().strip() if content_el else "[Empty or Media]"
                        
                        notebook_data["sources"].append({
                            "title": source_name,
                            "content": content
                        })
                    except Exception as e:
                        print(f"    [WARN] Source extraction error: {e}")
                
                # Extract Notes
                print("  [NOTE] Extracting saved notes...")
                try:
                    studio_tab = page.query_selector(INTERNAL_SELECTORS["studio_tab"])
                    if studio_tab: studio_tab.click()
                    time.sleep(1)
                    
                    notes = page.query_selector_all(INTERNAL_SELECTORS["note_item"])
                    for n_idx, note_el in enumerate(notes):
                        note_title = note_el.inner_text().strip()
                        print(f"    - Reading Note: {note_title}")
                        notebook_data["notes"].append({"title": note_title})
                except Exception as e:
                    print(f"  [WARN] Notes extraction error: {e}")
                
                results.append(notebook_data)
                
            # Final Save
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n[DONE] Global Ingestion Complete. Data saved to {output_file}")
            
        except Exception as e:
            print(f"[ERROR] Fatal Crawl Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            context.close()

if __name__ == "__main__":
    crawl_notebook_library()
