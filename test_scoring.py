# test_scoring.py
from api.heroes import get_heroes, hero_name_map
from api.matchups import get_matchup_data
from logic.scoring import score_draft

heroes   = get_heroes()
names    = hero_name_map(heroes)
data     = get_matchup_data()

# Infernus vs Haze + Seven + Lash
result = score_draft(
    my_hero_id=1,
    enemy_ids=[13, 2, 31],
    counters=data["counters"],
)

print(f"Overall: {result['overall_win_rate']}% — {result['verdict']}")
for e in result["per_enemy"]:
    print(f"  vs {names.get(e['hero_id'], '?'):<20} {e['win_rate']}% — {e['verdict']}")