import streamlit as st
import pandas as pd
from fpl import load_team, FPLError
from engine import projections, best_lineup, POSITIONS
from safety import Policy, evaluate

st.set_page_config(page_title='FPL Research Agent', layout='wide')
st.title('FPL Research Agent — Team 1052748')
st.caption('Live public player data; historical published team picks. No account login, transfer submission, or chip activation.')
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

st.error(f'ACCOUNT SYNC NOT VERIFIED: These are published GW {picks_gw} picks, NOT your confirmed current squad. Transfers made after that deadline may be missing.')
st.caption(f'Public team ID: {team_id} | Published squad: GW {picks_gw} | Projection starts: GW {next_gw}. Your current squad and bank are private until an authorised account connection is configured.')
if len(squad) != 15:
    st.error('Public picks did not contain 15 players; optimisation stopped.')
    st.stop()

lineup = best_lineup(squad)
col1, col2, col3 = st.columns(3)
col1.metric('Historical-squad projected XI + captain', f"{lineup['expected']:.1f} pts")
col2.metric('Captain', lineup['captain']['name'])
col3.metric('Vice captain', lineup['vice']['name'])

def rows(players):
    return [{'Player': p['name'], 'Position': POSITIONS[p['position']],
             'Price (£m)': p['price']/10, 'Next GW xPts': round(p['next'],2),
             f'{horizon}-GW xPts': round(p['total'],2)} for p in players]

left, right = st.columns([2,1])
with left:
    st.subheader(f'Illustrative starting XI — based on GW {picks_gw} picks')
    st.dataframe(pd.DataFrame(rows(lineup['xi'])), hide_index=True, use_container_width=True)
with right:
    st.subheader('Illustrative bench (GK first)')
    st.dataframe(pd.DataFrame(rows(lineup['bench'])), hide_index=True, use_container_width=True)

st.subheader('Player market watch — no account-specific transfer advice')
st.warning('Account-specific transfers are paused. The app cannot confirm which players you own, your bank, selling prices or free transfers. Showing buy/sell recommendations here would be misleading.')
st.caption('Public market information is refreshed automatically. Prices are current listed buying prices, not your personal selling values.')
watch = sorted(
    (p for p in all_players.values() if p['status'] == 'a' and p['next'] > 0),
    key=lambda p: (p['total'], p['next']), reverse=True
)[:15]
st.dataframe(pd.DataFrame([{
    'Player': p['name'], 'Position': POSITIONS[p['position']],
    'Current buying price (£m)': p['price'] / 10,
    'Next GW projected pts': round(p['next'], 2),
    f'{horizon}-GW projected pts': round(p['total'], 2)
} for p in watch]), hide_index=True, use_container_width=True)
st.caption('Research only. These projections are heuristic estimates, not verified predictions or recommendations to transfer anyone.')

st.subheader('Safety gate status')
status = evaluate(policy=Policy(), points_hit=0, chip=None, budget_valid=False,
                  rules_valid=False, minutes_to_deadline=None, data_fresh=False,
                  action_id='no-action', processed_ids=set())
st.error('EXECUTION DISABLED — Account not synced; ' + '; '.join(status['reasons']))
st.link_button('Open official FPL to make changes yourself', 'https://fantasy.premierleague.com/')
