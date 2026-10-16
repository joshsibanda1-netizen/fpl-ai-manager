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

st.subheader('Transfer analysis')
st.caption('For accurate transfers, enter your CURRENT bank and each player’s actual selling price. Public gameweek picks can be stale.')
bank_text = st.text_input('Current bank (£m)', placeholder='e.g. 1.2')
with st.expander('Enter selling prices (£m) for each player'):
    sales = {}
    for p in squad:
        sales[p['id']] = st.text_input(f"{p['name']} — selling price", key=f"sale_{p['id']}", placeholder='e.g. 6.4')

if st.button('Calculate one-transfer recommendations'):
    try:
        bank = int(round(float(bank_text)*10))
        assert bank >= 0
        for p in squad:
            p['selling_price'] = int(round(float(sales[p['id']])*10))
            if p['selling_price'] < 0: raise ValueError('Negative selling price')
        options = recommend_transfers(squad, all_players, bank)
        if not options:
            st.info('No affordable legal single-transfer candidates found.')
        else:
            st.dataframe(pd.DataFrame([{'Sell': x['out']['name'], 'Buy': x['in']['name'],
                'Next GW XI gain': round(x['gain_next'],2),
                f'{horizon}-GW player gain': round(x['gain_horizon'],2),
                'Bank after (£m)': x['bank_after']/10} for x in options]),
                hide_index=True, use_container_width=True)
            st.warning('Recommendations are research only. Free transfers, price changes, deadlines, and squad updates must be verified on the official FPL site. No action is submitted.')
    except (ValueError, AssertionError):
        st.error('Enter a valid nonnegative bank and all 15 selling prices.')

st.subheader('Safety gate status')
status = evaluate(policy=Policy(), points_hit=0, chip=None, budget_valid=False,
                  rules_valid=False, minutes_to_deadline=None, data_fresh=False,
                  action_id='no-action', processed_ids=set())
st.error('EXECUTION DISABLED — ' + '; '.join(status['reasons']))
st.link_button('Open official FPL to make changes yourself', 'https://fantasy.premierleague.com/')
