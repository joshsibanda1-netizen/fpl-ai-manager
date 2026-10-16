"""Read-only FPL public data client. No login, cookies, or write endpoints."""
import requests

BASE = 'https://fantasy.premierleague.com/api'

class FPLError(RuntimeError):
    pass

def get_json(path):
    try:
        r = requests.get(BASE + path, timeout=15, headers={'User-Agent': 'Personal-FPL-Research/0.1'})
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as exc:
        raise FPLError(f'Could not retrieve {path}: {exc}') from exc

def load_team(team_id=1052748):
    bootstrap = get_json('/bootstrap-static/')
    fixtures = get_json('/fixtures/')
    entry = get_json(f'/entry/{int(team_id)}/')
    current = next((e['id'] for e in bootstrap['events'] if e.get('is_current')), None)
    finished = [e['id'] for e in bootstrap['events'] if e.get('finished')]
    # Picks are public after a gameweek starts. Prefer current; otherwise most recent finished.
    candidates = ([current] if current else []) + sorted(finished, reverse=True)
    picks = None
    event_id = None
    for gw in dict.fromkeys(x for x in candidates if x is not None):
        try:
            data = get_json(f'/entry/{int(team_id)}/event/{gw}/picks/')
            if data.get('picks'):
                picks, event_id = data, gw
                break
        except FPLError:
            continue
    return bootstrap, fixtures, entry, picks, event_id
