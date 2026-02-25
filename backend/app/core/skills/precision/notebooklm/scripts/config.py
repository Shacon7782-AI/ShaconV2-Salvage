"""
Configuration for NotebookLM Skill
Centralizes constants, selectors, and paths
"""

from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"
LIBRARY_FILE = DATA_DIR / "library.json"

# NotebookLM Selectors
HOME_PAGE_SELECTORS = {
    "scroll_container": ".welcome-page-container",
    "list_view_btn": 'button[aria-label="List view"]', # Identified by subagent
    "grid_view_btn": 'button[aria-label="Grid view"]',
    "notebook_row": "tr.mat-mdc-row",
    "notebook_title": "td.mat-column-title span",
    "notebook_card": "mat-card.mat-mdc-card:not(.create-new-action-button)",
}

QUERY_INPUT_SELECTORS = [
    "textarea.query-box-input",  # Primary
    'textarea[aria-label="Feld für Anfragen"]',  # Fallback German
    'textarea[aria-label="Input for queries"]',  # Fallback English
]

RESPONSE_SELECTORS = [
    ".to-user-container .message-text-content",  # Primary
    "[data-message-author='bot']",
    "[data-message-author='assistant']",
]

INTERNAL_SELECTORS = {
    "source_sidebar": ".source-panel-content",
    "source_item": ".single-source-container",
    "content_area": ".scroll-area",
    "studio_tab": 'button:has-text("Studio")', # Common label
    "notes_container": ".panel-content-scrollable",
    "note_item": ".artifact-button-content",
}

# Browser Configuration
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',  # Patches navigator.webdriver
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--no-first-run',
    '--no-default-browser-check'
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Timeouts
LOGIN_TIMEOUT_MINUTES = 10
QUERY_TIMEOUT_SECONDS = 120
PAGE_LOAD_TIMEOUT = 30000
