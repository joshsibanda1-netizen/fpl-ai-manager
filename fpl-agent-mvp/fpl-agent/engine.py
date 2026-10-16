"""Transparent baseline projections and constrained squad decisions."""
from itertools import combinations

POSITIONS = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}

def projections(bootstrap, fixtures, horizon=5):
    teams = {t['id']: t for t in bootstrap['teams']}
    upcoming = [f for f in fixtures if not f.get('finished') and f.get('event') is not None]
    upcoming.sort(key=lambda f: (f['event'], f.get('kickoff_time') or ''))
    first = min((f['event'] for f in upcoming), default=1)
    end = first + horizon
    by_team = {t: [] for t in teams}
    for f in upcoming:
        if first <= f['event'] < end:
            by_team[f['team_h']].append((f['event'], f.get('team_h_difficulty', 3)))
            by_team[f['team_a']].append((f['event'], f.get('team_a_difficulty', 3)))
    result = {}
    for p in bootstrap['elements']:
        minutes = p.get('minutes', 0) or 0
        starts = p.get('starts', 0) or 0
        appearances = max(starts, minutes / 80, 1)
        historical_ppg = float(p.get('points_per_game') or 0)
        # Shrink early-season observations towards position-level prior.
        prior = {1: 3.2, 2: 3.4, 3: 4.0, 4: 4.0}[p['element_type']]
        evidence = min(appearances / 8, 1)
        baseline = historical_ppg * evidence + prior * (1 - evidence)
        availability = max(0, min(1, (p.get('chance_of_playing_next_round') if p.get('chance_of_playing_next_round') is not None else 100) / 100))
        # A conservative minutes factor; recent season minutes can be misleading.
        minutes_factor = min(1, max(.35, minutes / max(1, appearances * 85))) if minutes else .7
        gameweeks = {}
        for gw, difficulty in by_team.get(p['team'], []):
            gameweeks[gw] = gameweeks.get(gw, 0) + baseline * (1.15 - .075 * (difficulty - 2)) * availability * minutes_factor
        result[p['id']] = {'id': p['id'], 'name': p['web_name'], 'team': p['team'],
                           'position': p['element_type'], 'price': p['now_cost'],
                           'status': p.get('status'), 'weekly': gameweeks,
                           'total': sum(gameweeks.values()), 'next': gameweeks.get(first, 0)}
    return result, first

def valid_lineup(players):
    counts = {pos: sum(p['position'] == pos for p in players) for pos in range(1, 5)}
    return counts[1] == 1 and 3 <= counts[2] <= 5 and 2 <= counts[3] <= 5 and 1 <= counts[4] <= 3

def best_lineup(squad, metric='next'):
    if len(squad) != 15:
        raise ValueError('Expected a 15-player squad')
    best = None
    for ids in combinations(range(15), 11):
        xi = [squad[i] for i in ids]
        if not valid_lineup(xi):
            continue
        score = sum(p[metric] for p in xi)
        if best is None or score > best[0]:
            best = (score, xi)
    if best is None:
        raise ValueError('No legal XI found')
    xi = best[1]
    bench = [p for p in squad if p['id'] not in {x['id'] for x in xi}]
    bench.sort(key=lambda p: (p['position'] != 1, -p[metric]))
    ordered = sorted(xi, key=lambda p: p[metric], reverse=True)
    return {'xi': xi, 'bench': bench, 'captain': ordered[0], 'vice': ordered[1], 'expected': best[0] + ordered[0][metric]}

def recommend_transfers(squad, all_players, bank, max_results=10):
    """One free transfer only; prices in tenths of GBP. Selling value must be supplied in squad."""
    existing = {p['id'] for p in squad}
    team_counts = {}
    for p in squad:
        team_counts[p['team']] = team_counts.get(p['team'], 0) + 1
    base = best_lineup(squad)['expected']
    options = []
    for out in squad:
        sale = out.get('selling_price')
        if sale is None:
            continue
        for incoming in all_players.values():
            if incoming['id'] in existing or incoming['position'] != out['position']:
                continue
            if incoming['price'] > bank + sale:
                continue
            if team_counts.get(incoming['team'], 0) - (out['team'] == incoming['team']) >= 3:
                continue
            if incoming['status'] not in ('a', 'd'):
                continue
            new_squad = [incoming if p['id'] == out['id'] else p for p in squad]
            gain = best_lineup(new_squad)['expected'] - base
            # Multiweek value is shown separately, not substituted for next-GW improvement.
            long_gain = incoming['total'] - out['total']
            options.append({'out': out, 'in': incoming, 'gain_next': gain,
                            'gain_horizon': long_gain, 'bank_after': bank + sale - incoming['price']})
    return sorted(options, key=lambda x: (x['gain_horizon'], x['gain_next']), reverse=True)[:max_results]
