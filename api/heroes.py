# api/heroes.py
import httpx
import json
from pathlib import Path

BASE_URL = "https://api.deadlock-api.com"
ASSETS_URL = "https://assets.deadlock-api.com"
CACHE_PATH = Path("cache/heroes.json")

def get_heroes(force_refresh=False) -> list[dict]:
    """Fetch all heroes, using a local cache to avoid repeat calls."""
    if CACHE_PATH.exists() and not force_refresh:
        return json.loads(CACHE_PATH.read_text())
    
    response = httpx.get(f"{ASSETS_URL}/v2/heroes")
    response.raise_for_status()
    heroes = response.json()
    
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(heroes, indent=2))
    return heroes