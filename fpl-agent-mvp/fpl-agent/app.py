import streamlit as st
import pandas as pd
from fpl import load_team, FPLError
from engine import projections, best_lineup, recommend_transfers, POSITIONS
from safety import Policy, evaluate

st.set_page_config(page_title='FPL Research Agent', layout='wide')
st.title('FPL Research Agent — Team 1052748')
st.caption('Read-only research prototype. No login, transfer submission, or chip activation.')
with st.sidebar:
    team_id = st.number_input('Public team ID', min_value=1, value=1052748, step=1)
    horizon = st.slider('Projection horizon (gameweeks)', 1, 8, 5)
    st.warning('Emergency stop: ENGAGED. Execution disabled by design.')
    if st.button('Refresh public data'):
        st.cache_data.clear()

@st.cache_data(ttl=3600, show_spinner='Loading publicly accessible FPL data…')
def fetch(team_id):
    return load_team(team_id)

try:
    bootstrap, fixtures, entry, picks, picks_gw = fetch(team_id)
except (FPLError, KeyError, TypeError) as exc:
    st.error(f'Public data could not be loaded: {exc}')
    st.info('Check your team ID and try again later. No squad data has been invented.')
    st.stop()

all_players, next_gw = projections(bootstrap, fixtures, horizon)
st.subheader(entry.get('name', 'Your team'))
st.write(f'Projection begins at GW {next_gw}. Model is a heuristic baseline, not a trained forecast.')
if not picks:
    st.warning('No public gameweek picks are available yet. Current squad cannot be verified.')
    st.stop()

picks_by_id = {p['element']: p for p in picks['picks']}
squad = []
for player_id, pick in picks_by_id.items():
    p = dict(all_players[player_id])
    # Public picks endpoint may not expose current selling prices. Never substitute now_cost.
    p['selling_price'] = pick.get('selling_price')
    squad.append(p)

st.info(f'Using publicly visible picks from GW {picks_gw}. They may not reflect unannounced transfers or your current bank.')
if len(squad) != 15:
    st.error('Public picks did not contain 15 players; optimisation stopped.')
    st.stop()

lineup = best_lineup(squad)
col1, col2, col3 = st.columns(3)
col1.metric('Projected XI + captain', f"{lineup['expected']:.1f} pts")
col2.metric('Captain', lineup['captain']['name'])
col3.metric('Vice captain', lineup['vice']['name'])

def rows(players):
    return [{'Player': p['name'], 'Position': POSITIONS[p['position']],
             'Price (£m)': p['price']/10, 'Next GW xPts': round(p['next'],2),
             f'{horizon}-GW xPts': round(p['total'],2)} for p in players]

left, right = st.columns([2,1])
with left:
    st.subheader('Optimal starting XI')
    st.dataframe(pd.DataFrame(rows(lineup['xi'])), hide_index=True, use_container_width=True)
with right:
    st.subheader('Bench (GK first)')
    st.dataframe(pd.DataFrame(rows(lineup['bench'])), hide_index=True, use_container_width=True)

st.subheader('Automated transfer research')
st.caption('Automatically generated from public FPL data. No manual bank or selling-price entry.')
last_bank = entry.get('last_deadline_bank')
if last_bank is not None:
    st.metric('Last published bank (may be stale)', f"£{last_bank / 10:.1f}m")
st.warning('Current selling prices, bank and unannounced transfers cannot be verified from public picks. Recommendations below are provisional, not confirmed affordable transfers.')
existing = {p['id'] for p in squad}
team_counts = {}
for p in squad:
    team_counts[p['team']] = team_counts.get(p['team'], 0) + 1
candidates = []
for outgoing in squad:
    for incoming in all_players.values():
        if incoming['id'] in existing or incoming['position'] != outgoing['position']:
            continue
        if team_counts.get(incoming['team'], 0) - int(outgoing['team'] == incoming['team']) >= 3:
            continue
        if incoming['status'] not in ('a', 'd'):
            continue
        improvement = incoming['total'] - outgoing['total']
        if improvement <= 0:
            continue
        candidates.append({
            'Sell': outgoing['name'], 'Consider buying': incoming['name'],
            f'{horizon}-GW player xPts gain': round(improvement, 2),
            'Buying price (£m)': incoming['price'] / 10,
            'Affordability': 'Unverified',
        })
candidates.sort(key=lambda x: x[f'{horizon}-GW player xPts gain'], reverse=True)
if candidates:
    st.dataframe(pd.DataFrame(candidates[:12]), hide_index=True, use_container_width=True)
    st.caption('Research shortlist only. Player-to-player comparisons are not confirmed legal transfers or guaranteed squad gains.')
else:
    st.info('No positive projected player swaps found.')

st.subheader('Safety gate status')
status = evaluate(policy=Policy(), points_hit=0, chip=None, budget_valid=False,
                  rules_valid=False, minutes_to_deadline=None, data_fresh=False,
                  action_id='no-action', processed_ids=set())
st.error('EXECUTION DISABLED — ' + '; '.join(status['reasons']))
st.link_button('Open official FPL to make changes yourself', 'https://fantasy.premierleague.com/')
