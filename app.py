# app.py
import streamlit as st
from api.heroes import get_heroes, hero_name_map
from api.matchups import get_matchup_data
from logic.scoring import score_draft

st.set_page_config(page_title="Deadlock Matchup Advisor", page_icon="⚔️", layout="centered")
st.title("⚔️ Deadlock Matchup Advisor")

# ── Load data (cached by Streamlit so it doesn't re-fetch on every interaction)

@st.cache_data(ttl=3600)
def load_data():
    heroes = get_heroes()
    data   = get_matchup_data()
    return heroes, data

with st.spinner("Loading hero and matchup data..."):
    heroes, matchup_data = load_data()

names    = hero_name_map(heroes)
counters = matchup_data["counters"]

# Sorted hero name list for the dropdowns
hero_options = sorted(names.items(), key=lambda x: x[1])  # [(id, name), ...]
name_to_id   = {name: hid for hid, name in hero_options}
name_list    = [name for _, name in hero_options]

# ── Inputs

st.subheader("Your Hero")
my_hero_name = st.selectbox("Select your hero", name_list, label_visibility="collapsed")

st.subheader("Enemy Team")
enemy_names = st.multiselect(
    "Select up to 5 enemy heroes",
    [n for n in name_list if n != my_hero_name],
    max_selections=5,
    label_visibility="collapsed",
)

# ── Results

if not enemy_names:
    st.info("Select at least one enemy hero to see matchup analysis.")
    st.stop()

my_id     = name_to_id[my_hero_name]
enemy_ids = [name_to_id[n] for n in enemy_names]
result    = score_draft(my_id, enemy_ids, counters)

if "error" in result:
    st.warning(result["error"])
    st.stop()

st.divider()

# Overall score
verdict_color = {"Favorable": "🟢", "Even": "🟡", "Unfavorable": "🔴"}
icon = verdict_color[result["verdict"]]
st.metric(
    label=f"{icon} Overall win rate vs this draft",
    value=f"{result['overall_win_rate']}%",
)

# Per-enemy breakdown
st.subheader("Breakdown")
for e in sorted(result["per_enemy"], key=lambda x: x["win_rate"]):
    icon  = verdict_color[e["verdict"]]
    ename = names.get(e["hero_id"], f"Hero {e['hero_id']}")
    st.write(f"{icon} **vs {ename}** — {e['win_rate']}% ({e['matches']:,} matches)")

# Worst matchup callout
if len(enemy_names) > 1:
    worst_name = names.get(result["worst_matchup"]["hero_id"], "?")
    st.warning(f"⚠️ Biggest threat: **{worst_name}** ({result['worst_matchup']['win_rate']}% win rate)")