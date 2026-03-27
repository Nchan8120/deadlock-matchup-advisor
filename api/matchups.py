# api/matchups.py
import httpx

BASE_URL = "https://api.deadlock-api.com"

def get_hero_matchups(hero_id: int, min_badge: int = None) -> list[dict]:
    """
    Returns win rates for hero_id against every other hero.
    min_badge filters to a rank tier (optional).
    """
    params = {}
    if min_badge:
        params["min_badge_level"] = min_badge
    
    response = httpx.get(
        f"{BASE_URL}/v1/analytics/hero/{hero_id}/matchups",
        params=params
    )
    response.raise_for_status()
    return response.json()