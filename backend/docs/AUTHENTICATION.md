# StartupTN scraper authentication

The scraper uses a Playwright `storage_state` file at `.runtime/startuptn-auth-state.json`.  A file that only contains analytics or accessibility preferences is **not** an authenticated session and must not be used to start a job.

## Safe manual refresh

From the project root on a workstation with an interactive desktop:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r scraper/requirements.txt
playwright install chromium
python scraper/save_auth_state.py --storage .runtime/startuptn-auth-state.json
```

Complete StartupTN login and any CAPTCHA, OTP, MFA, or browser verification yourself in the headed browser. Do not automate or bypass those controls. The helper writes the state only after the browser navigates away from the login page.

Then start or recreate the scraper service so Docker mounts the same project directory, and validate without disclosing credentials:

```powershell
docker compose up -d --build scraper
docker compose exec scraper python auth_check.py
```

Only run a small scraper job after `auth_check.py` reports a successful profile API response. If the check reports that no runtime API token was found or returns 401/403, repeat the manual login; the saved state is stale or incomplete.

The state file is intentionally excluded by `.gitignore`. Never commit it, browser profiles, `.env`, passwords, cookies, or tokens.
