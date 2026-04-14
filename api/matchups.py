# api/matchups.py
import httpx
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL   = "https://api.deadlock-api.com/v1"
CACHE_FILE = Path("cache/matchups.json")
CACHE_TTL_HOURS = 6  # re-fetch if cache is older than this

def _is_cache_fresh() -> bool:
    if not CACHE_FILE.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    return age < timedelta(hours=CACHE_TTL_HOURS)

def _build_params(min_badge: int = 0, max_badge: int = 116) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "game_mode":          "normal",
        "min_unix_timestamp": int((now - timedelta(days=15)).timestamp()),
        "max_unix_timestamp": int(now.timestamp()),
        "min_average_badge":  min_badge,
        "max_average_badge":  max_badge,
        "same_lane_filter":   "true",
        "min_matches":        10,
    }

def get_matchup_data(force_refresh: bool = False, min_badge: int = 0, max_badge: int = 116) -> dict:
    """
    Returns {"counters": [...], "synergies": [...]}
    Cached to disk for CACHE_TTL_HOURS hours.
    """
    if not force_refresh and _is_cache_fresh():
        return json.loads(CACHE_FILE.read_text())

    params   = _build_params(min_badge, max_badge)
    counters  = httpx.get(f"{BASE_URL}/analytics/hero-counter-stats",  params=params, timeout=15).raise_for_status().json()
    synergies = httpx.get(f"{BASE_URL}/analytics/hero-synergy-stats",  params=params, timeout=15).raise_for_status().json()

    data = {"counters": counters, "synergies": synergies}
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data))
    return data