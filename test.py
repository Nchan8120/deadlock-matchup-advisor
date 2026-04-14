"""
test.py — Explore the Deadlock API: heroes + matchups
Run with: python test.py

Confirms the real shape of the JSON before you build anything on top of it.
Rate limit: 1 req/sec (handled by the sleep() calls below).
"""

import httpx
import json
import time
import sys
from datetime import datetime, timedelta, timezone

BASE_URL   = "https://api.deadlock-api.com/v1"
ASSETS_URL = "https://assets.deadlock-api.com/v2"

# ── helpers ───────────────────────────────────────────────────────────────────

def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def show(label: str, data):
    print(f"\n── {label}")
    print(json.dumps(data, indent=2))

def get(url: str, params: dict = None, fatal: bool = True):
    """GET with basic error reporting. fatal=False skips instead of exiting."""
    response = httpx.get(url, params=params, timeout=10)
    if response.status_code != 200:
        print(f"  ✗ HTTP {response.status_code} — {url}")
        print(f"    {response.text[:300]}")
        if fatal:
            sys.exit(1)
        return None
    return response.json()

# Timestamps: last 15 days up to now (matches what the site uses)
now     = datetime.now(timezone.utc)
two_weeks_ago = now - timedelta(days=15)
MAX_TS  = int(now.timestamp())
MIN_TS  = int(two_weeks_ago.timestamp())

# Shared query params used across all analytics endpoints
BASE_PARAMS = {
    "game_mode":          "normal",
    "min_unix_timestamp": MIN_TS,
    "max_unix_timestamp": MAX_TS,
    "min_average_badge":  0,
    "max_average_badge":  116,   # 0=Obscurus, 116=Eternus (all ranks)
}

print(f"\n  Date range: {two_weeks_ago.strftime('%Y-%m-%d')} → {now.strftime('%Y-%m-%d')}")

# ── 1. Hero list ──────────────────────────────────────────────────────────────

section("1. Hero list  (assets.deadlock-api.com/v2/heroes)")

heroes_raw = get(f"{ASSETS_URL}/heroes")
selectable = [h for h in heroes_raw if h.get("player_selectable") is True]

print(f"\n  Total in response: {len(heroes_raw)}  |  Playable: {len(selectable)}")
print("\n  Playable heroes (id + name):")
for h in sorted(selectable, key=lambda x: x.get("id", 0)):
    print(f"    id={h.get('id'):>4}   {h.get('name')}")

# Build a lookup dict we'll reuse below: id -> name
hero_names = {h["id"]: h["name"] for h in selectable}

time.sleep(1)

# ── 2. Hero stats (overall win rates) ────────────────────────────────────────

section("2. Hero stats  (/v1/analytics/hero-stats)")

stats = get(f"{BASE_URL}/analytics/hero-stats", params={**BASE_PARAMS, "min_hero_matches": 10})

print(f"\n  Total entries: {len(stats)}")
print("\n  First entry — full object:")
show("stats[0]", stats[0])
print(f"\n  ℹ️  Keys: {list(stats[0].keys())}")

# Show win rates for all heroes, sorted best → worst
print("\n  Win rates across all heroes:")
for row in sorted(stats, key=lambda x: x["wins"] / max(x["matches"], 1), reverse=True):
    wr   = row["wins"] / row["matches"] * 100
    name = hero_names.get(row["hero_id"], f"id={row['hero_id']}")
    print(f"    {name:<20}  {wr:>5.1f}%  ({row['matches']:,} matches)")

time.sleep(1)

# ── 3. Counter stats (matchups / counters) ────────────────────────────────────

section("3. Counter stats  (/v1/analytics/hero-counter-stats)")

counters = get(
    f"{BASE_URL}/analytics/hero-counter-stats",
    params={**BASE_PARAMS, "same_lane_filter": "true", "min_matches": 10},
)

print(f"\n  Total rows: {len(counters)}")
print("\n  First row — full object:")
show("counters[0]", counters[0])
print(f"\n  ℹ️  Keys: {list(counters[0].keys())}")

# Figure out which keys identify hero1 vs hero2
sample = counters[0]
print(f"\n  All keys and their values (to identify hero/wins fields):")
for k, v in sample.items():
    print(f"    {k}: {v}")

# Try to compute win rates — detect the hero id fields
hero1_key = next((k for k in sample if k in ("hero_id1", "hero_id", "hero1_id")), None)
hero2_key = next((k for k in sample if k in ("hero_id2", "counter_hero_id", "hero2_id")), None)
wins_key  = next((k for k in sample if "win" in k.lower()), None)
match_key = next((k for k in sample if k == "matches" or k == "total_matches"), None)

if all([hero1_key, hero2_key, wins_key, match_key]):
    print(f"\n  ✓ Detected fields: hero1={hero1_key}, hero2={hero2_key}, wins={wins_key}, matches={match_key}")

    # Find the 5 worst counters against Infernus (id=1)
    INFERNUS_ID = 1
    infernus_rows = [r for r in counters if r.get(hero1_key) == INFERNUS_ID]
    if infernus_rows:
        print(f"\n  Matchups for Infernus ({len(infernus_rows)} rows):")
        with_wr = []
        for r in infernus_rows:
            m  = r.get(match_key, 1)
            w  = r.get(wins_key, 0)
            wr = (w / m * 100) if m > 0 else 0
            with_wr.append({**r, "_wr": round(wr, 1)})

        print("\n  Best matchups for Infernus (he wins):")
        for r in sorted(with_wr, key=lambda x: x["_wr"], reverse=True)[:5]:
            opp = hero_names.get(r.get(hero2_key), f"id={r.get(hero2_key)}")
            print(f"    vs {opp:<20}  {r['_wr']:>5.1f}%  ({r.get(match_key)} matches)")

        print("\n  Worst matchups for Infernus (he loses):")
        for r in sorted(with_wr, key=lambda x: x["_wr"])[:5]:
            opp = hero_names.get(r.get(hero2_key), f"id={r.get(hero2_key)}")
            print(f"    vs {opp:<20}  {r['_wr']:>5.1f}%  ({r.get(match_key)} matches)")
    else:
        print(f"\n  ⚠️  No rows found with {hero1_key}==1. Try printing counters[0] keys to find the right field.")
else:
    print(f"\n  ⚠️  Couldn't auto-detect fields. Detected: hero1={hero1_key}, hero2={hero2_key}, wins={wins_key}, matches={match_key}")
    print("  Inspect the key/value dump above to find the right field names.")

time.sleep(1)

# ── 4. Synergy stats (ally combos) ───────────────────────────────────────────

section("4. Synergy stats  (/v1/analytics/hero-synergy-stats)")

synergies = get(
    f"{BASE_URL}/analytics/hero-synergy-stats",
    params={**BASE_PARAMS, "same_lane_filter": "true", "min_matches": 10},
    fatal=False,
)

if synergies is None:
    print("  ⚠️  Synergies endpoint unavailable — skipping.")
else:
    print(f"\n  Total rows: {len(synergies)}")
    print("\n  First row — full object:")
    show("synergies[0]", synergies[0])
    print(f"\n  ℹ️  Keys: {list(synergies[0].keys())}")

# ── 5. Badge level filter test ───────────────────────────────────────────────

section("5. Same counter stats filtered to high rank  (min_average_badge=90)")

high_rank_params = {
    **BASE_PARAMS,
    "min_average_badge": 90,   # ~Ritualist and above
    "same_lane_filter":  "true",
    "min_matches":       10,
}

counters_hr = get(f"{BASE_URL}/analytics/hero-counter-stats", params=high_rank_params, fatal=False)

if counters_hr is None:
    print("  ⚠️  High-rank filter returned no data — skipping.")
else:
    print(f"\n  Rows at badge>=90: {len(counters_hr)}")
    if counters_hr:
        show("counters_hr[0]", counters_hr[0])

# ── done ─────────────────────────────────────────────────────────────────────

section("Done ✓")
print("""
What to carry into your project:
  1. Hero name field:    'name'  (assets API)
  2. Matchups endpoint:  /v1/analytics/hero-counter-stats
  3. Synergy endpoint:   /v1/analytics/hero-synergy-stats
  4. Filter by rank:     min_average_badge / max_average_badge (0–116)
  5. Filter by date:     min_unix_timestamp / max_unix_timestamp
  6. Key params:         game_mode=normal, same_lane_filter=true
  7. Note the hero1/hero2 field names from section 3 output above —
     you'll need those in scoring.py to filter rows by hero.
""")