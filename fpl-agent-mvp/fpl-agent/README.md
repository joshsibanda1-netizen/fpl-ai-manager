# FPL Research Agent — Team 1052748

A **read-only** Streamlit prototype. It does not log in, automate transfers, activate chips, or store credentials. The six requested safeguards are represented in `safety.py`, and execution is permanently unavailable in this release.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown in the terminal. For tests: `pytest -q`.

## Deploy to Streamlit Community Cloud

1. Create a **private** GitHub repository (or a public repository if you're comfortable exposing this source) and upload the contents of this folder to its root.
2. Sign into https://share.streamlit.io/ and select **Create app** → **Deploy a public app from GitHub** (or an available private deployment option).
3. Choose the repository and branch, and set the main file path to `app.py`.
4. Deploy. No API key or FPL password is required. Note that Streamlit Community Cloud may make the app publicly accessible; don't enter confidential information into a public deployment.
5. Open the app, inspect the public squad, and supply the **current** bank and each actual selling price if you want transfer suggestions.

## Important limitations

- Public picks are generally a snapshot from a published gameweek, **not a reliable live view** of transfers before the next deadline.
- Selling prices and current bank may not be public or current. The dashboard **requires manual entry** rather than guessing them.
- The heuristic expected-points model uses FPL points-per-game, minutes, injury availability, and fixture difficulty. It is **not** a calibrated ML forecast. Its horizon score sums expected player points and does not model captaincy or optimal XI for each future week.
- Transfer suggestions compare single-player horizon gain and immediate optimal XI gain; they do **not** yet optimise multiweek transfer plans, future free-transfer rollovers, chips, or hits.
- Data are fetched from publicly accessible FPL endpoints on demand, cached for one hour. These endpoints may change or restrict access; review applicable FPL terms and use authorised data sources where required.
- There is no unattended background polling, Telegram alerting, authenticated integration, or execution adapter in this MVP.
- The safety gate is a fail-closed **prototype**, not a transactional lock service. Never interpret its output as permission for an automated submission.

## Next engineering milestones

1. Add a licensed or otherwise authorised data feed and historical dataset; measure forecast calibration and error.
2. Add authenticated **read-only** squad import through an officially authorised mechanism if one becomes available.
3. Replace heuristic projections with tested per-fixture minutes, goals, assists, defensive and bonus models.
4. Add multiweek constrained optimisation and simulation, including free-transfer rollovers and selling-price rules for the current season.
5. Add a persistent database, job scheduler, audit log, notifications, and a server-side emergency-stop flag.
6. Keep execution disabled unless an authorised FPL write integration is available and independently audited.

## Safeguard policy

- No automatic points hits.
- No automatic chip activation.
- Validate budget and game rules.
- Freeze near deadlines (default 15 minutes).
- Prevent duplicate transactions (a production version requires persistent idempotency and locking).
- Emergency stop engaged by default; **all execution is absent from this app**.
