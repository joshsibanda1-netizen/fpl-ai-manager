# Windows Chrome read-only FPL account export (experimental)

This is an unpacked Chrome extension. It does not ask for or store your Google password or session cookies. It fetches the FPL account endpoint from your existing signed-in FPL tab and downloads a JSON file locally. It does not send data to any other server. The FPL endpoint is unofficial and may stop working; Google sign-in or FPL browser security can block it.

## Install on Windows
1. On GitHub, download the repository ZIP (Code > Download ZIP) and extract it.
2. In Chrome, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the `fpl-agent-mvp/fpl-agent/windows-sync` folder.
3. Visit https://fantasy.premierleague.com/ in Chrome and sign in normally using Google. Confirm you are signed into the account that owns team 1052748.
4. While the FPL tab is active, click the extension icon and **Export my current squad**.
5. If the export succeeds, a local file named `fpl-my-team.json` is downloaded.
6. Open your Streamlit FPL dashboard and upload that file under **Current account squad — optional local export**.

The dashboard uses the file to show your actual snapshot squad and bank. This is NOT continuous automatic cloud sync. Export again after transfers. Do not share the JSON file publicly: it contains private squad and financial data. Never commit it to GitHub.

## Safeguards
No transfer or chip endpoints are called. No automatic execution is implemented. All private data stays in the browser until you explicitly download and upload the file. Streamlit processes uploaded data in the active session; do not upload it to an untrusted deployment.

If the FPL private endpoint returns 401/403, this companion cannot bypass that restriction. Do not paste passwords, session cookies, or access tokens into this tool.
