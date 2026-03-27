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

BASE_URL = "https://api.deadlock-api.com/v1"
ASSETS_URL = "https://assets.deadlock-api.com/v2"

# ── helpers ───────────────────────────────────────────────────────────────────

def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def show(label: str, data):
    print(f"\n── {label}")
    print(json.dumps(data, indent=2))

def get(url: str, params: dict = None) -> dict | list:
    """GET with basic error reporting."""
    response = httpx.get(url, params=params, timeout=10)
    if response.status_code != 200:
        print(f"  ✗ HTTP {response.status_code} — {url}")
        print(f"    {response.text[:300]}")
        sys.exit(1)
    return response.json()

# ── 1. Hero list ──────────────────────────────────────────────────────────────

section("1. Hero list  (assets.deadlock-api.com/v2/heroes)")

heroes_raw = get(f"{ASSETS_URL}/heroes")

print(f"\n  Total heroes returned: {len(heroes_raw)}")
print("\n  First hero — full object (so you know every field name):")
show("heroes_raw[0]", heroes_raw[0])

# Print a compact name → id table for all heroes
print("\n  All heroes (id + name):")
for h in sorted(heroes_raw, key=lambda x: x.get("id", 0)):
    hero_id   = h.get("id")
    # The API uses different field names for the display name — check all common ones
    hero_name = (
        h.get("name")
        or h.get("hero_name")
        or h.get("display_name")
        or h.get("localized_name")
        or "<unknown field — check keys above>"
    )
    print(f"    id={hero_id:>4}   {hero_name}")

# Grab the first hero's id to use in later tests
first_hero = heroes_raw[0]
first_hero_id = first_hero.get("id")
all_keys = list(first_hero.keys())
print(f"\n  ℹ️  Keys on each hero object: {all_keys}")
print(f"  ℹ️  Using hero id={first_hero_id} for the matchup tests below")

time.sleep(1)  # respect rate limit

# ── 2. Overall hero analytics (win/pick rates) ────────────────────────────────

section("2. Hero analytics  (win rate, pick rate for all heroes)")

stats = get(f"{BASE_URL}/analytics/hero-stats")

print(f"\n  Total entries: {len(stats)}")
print("\n  First entry — full object:")
show("stats[0]", stats[0])
print(f"\n  ℹ️  Keys: {list(stats[0].keys())}")

time.sleep(1)

# ── 3. Matchups for a specific hero ──────────────────────────────────────────

section(f"3. Matchups for hero id={first_hero_id}")

matchups = get(f"{BASE_URL}/analytics/hero/{first_hero_id}/matchups")

print(f"\n  Total matchup rows returned: {len(matchups)}")
print("\n  First row — full object:")
show("matchups[0]", matchups[0])
print(f"\n  ℹ️  Keys: {list(matchups[0].keys())}")

# Compute win rates if the expected fields exist
sample = matchups[0]
wins_key    = next((k for k in sample if "win" in k.lower()), None)
matches_key = next((k for k in sample if "match" in k.lower()), None)

if wins_key and matches_key:
    print(f"\n  Detected wins field: '{wins_key}', matches field: '{matches_key}'")
    print("\n  Top 5 best matchups (highest win rate against opponent):")
    with_wr = []
    for row in matchups:
        w = row.get(wins_key, 0)
        m = row.get(matches_key, 1)
        wr = (w / m * 100) if m > 0 else 0
        with_wr.append({**row, "_win_rate": round(wr, 1)})
    top5 = sorted(with_wr, key=lambda x: x["_win_rate"], reverse=True)[:5]
    for entry in top5:
        print(f"    vs hero_id={entry.get('hero_id2') or entry.get('enemy_hero_id') or '?'}  →  {entry['_win_rate']}%  ({entry.get(matches_key)} matches)")
else:
    print("\n  ⚠️  Couldn't auto-detect wins/matches fields — inspect the keys above manually.")

time.sleep(1)

# ── 4. Matchups filtered by rank ─────────────────────────────────────────────

section(f"4. Same matchups but filtered to a rank tier (min_badge_level=90)")

# Badge levels: ~0=Obscurus ... ~116=Eternus
# 90 ≈ Ritualist range — adjust as you see fit
matchups_ranked = get(
    f"{BASE_URL}/analytics/hero/{first_hero_id}/matchups",
    params={"min_badge_level": 90}
)

print(f"\n  Rows returned with min_badge_level=90: {len(matchups_ranked)}")
if matchups_ranked:
    show("matchups_ranked[0]", matchups_ranked[0])

time.sleep(1)

# ── 5. Hero synergies (same-team combos) ─────────────────────────────────────

section(f"5. Synergies for hero id={first_hero_id}  (ally combos)")

try:
    synergies = get(f"{BASE_URL}/analytics/hero/{first_hero_id}/synergies")
    print(f"\n  Total synergy rows: {len(synergies)}")
    if synergies:
        show("synergies[0]", synergies[0])
        print(f"\n  ℹ️  Keys: {list(synergies[0].keys())}")
except SystemExit:
    print("  ⚠️  Synergies endpoint not available or returned an error — skip for now.")

# ── done ─────────────────────────────────────────────────────────────────────

section("Done ✓")
print("""
Next steps:
  1. Review the field names printed above and update api/heroes.py +
     api/matchups.py to use the exact keys you see.
  2. Check whether hero name lives in 'name', 'display_name', etc.
  3. Note which field identifies the opponent hero in matchup rows
     (likely 'hero_id2' or 'enemy_hero_id') — needed in scoring.py.
  4. Decide your default rank filter (min_badge_level) for the app.
""")