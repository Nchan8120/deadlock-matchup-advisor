# api/heroes.py
import httpx
import json
from pathlib import Path

ASSETS_URL = "https://assets.deadlock-api.com/v2"
CACHE_FILE = Path("cache/heroes.json")

def get_heroes(force_refresh: bool = False) -> list[dict]:
    if CACHE_FILE.exists() and not force_refresh:
        return json.loads(CACHE_FILE.read_text())

    heroes = httpx.get(f"{ASSETS_URL}/heroes", timeout=10).raise_for_status().json()
    playable = [h for h in heroes if h.get("player_selectable") is True]

    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(playable, indent=2))
    return playable

def hero_name_map(heroes: list[dict]) -> dict[int, str]:
    """Returns {id: name} for quick lookups."""
    return {h["id"]: h["name"] for h in heroes}