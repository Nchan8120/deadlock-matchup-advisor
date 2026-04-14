# logic/scoring.py


HERO1_KEY   = "hero_id"
HERO2_KEY   = "enemy_hero_id"
WINS_KEY    = "wins"
MATCHES_KEY = "matches_played"

def _win_rate(row: dict) -> float:
    m = row.get(MATCHES_KEY, 0)
    w = row.get(WINS_KEY, 0)
    return (w / m * 100) if m > 0 else 50.0

def score_draft(my_hero_id: int, enemy_ids: list[int], counters: list[dict]) -> dict:
    """
    Given your hero and a list of enemy hero ids, return a matchup breakdown.
    """
    relevant = [
        r for r in counters
        if r.get(HERO1_KEY) == my_hero_id and r.get(HERO2_KEY) in enemy_ids
    ]

    if not relevant:
        return {"error": "No matchup data found for this combination."}

    per_enemy = []
    for row in relevant:
        wr = _win_rate(row)
        per_enemy.append({
            "hero_id":  row[HERO2_KEY],
            "win_rate": round(wr, 1),
            "matches":  row.get(MATCHES_KEY, 0),
            "verdict":  "Favorable" if wr > 52 else "Unfavorable" if wr < 48 else "Even",
        })

    overall = sum(e["win_rate"] for e in per_enemy) / len(per_enemy)
    worst   = min(per_enemy, key=lambda x: x["win_rate"])
    best    = max(per_enemy, key=lambda x: x["win_rate"])

    return {
        "overall_win_rate": round(overall, 1),
        "verdict":          "Favorable" if overall > 52 else "Unfavorable" if overall < 48 else "Even",
        "per_enemy":        per_enemy,
        "worst_matchup":    worst,
        "best_matchup":     best,
    }

def score_synergies(my_hero_id: int, ally_ids: list[int], synergies: list[dict]) -> list[dict]:
    """
    Given your hero and ally ids, return synergy win rates with those allies.
    """
    relevant = [
        r for r in synergies
        if r.get(HERO1_KEY) == my_hero_id and r.get(HERO2_KEY) in ally_ids
    ]
    return [
        {
            "hero_id":  r[HERO2_KEY],
            "win_rate": round(_win_rate(r), 1),
            "matches":  r.get(MATCHES_KEY, 0),
        }
        for r in relevant
    ]