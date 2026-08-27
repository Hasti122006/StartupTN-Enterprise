"""Run a safe authentication diagnostic for StartupTN storage_state and API token.

This script verifies that:
- storage state file exists and is loadable by Playwright
- the StartupTN base page is accessible
- a runtime API token can be located (without printing it)
- the profile API for userid=12804 returns HTTP 200

It prints only safe diagnostics and a short fingerprint of the token (not the token itself).
"""
import asyncio
import hashlib
import json
import os
import sys

from playwright.async_api import async_playwright

from config import ScraperConfig


async def main():
    cfg = ScraperConfig()
    storage = cfg.storage_state_path
    print("[AUTH-CHECK] Storage state path:", storage)
    if not os.path.exists(storage):
        print("[AUTH-CHECK] Storage state file not found")
        return 2

    # Inspect storage-state file for cookie names and storage keys (safe diagnostics)
    try:
        with open(storage, 'r', encoding='utf-8') as sf:
            raw = json.load(sf)
        cookies = raw.get('cookies', []) or []
        cookie_names = [c.get('name') for c in cookies if c.get('name')]
        print('[AUTH-CHECK] Storage-state cookie names:', cookie_names)
        origins = raw.get('origins', []) or []
        for origin in origins:
            origin_name = origin.get('origin')
            local_items = origin.get('localStorage', []) or []
            ls_keys = [item.get('name') for item in local_items if item.get('name')]
            print(f"[AUTH-CHECK] localStorage keys for {origin_name}:", ls_keys)
    except Exception as exc:
        print('[AUTH-CHECK] Failed to introspect storage-state file:', exc)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use storage_state so Playwright will load cookies/localStorage/sessionStorage
        context = await browser.new_context(storage_state=storage, viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        try:
            await page.goto(cfg.base_url, wait_until="domcontentloaded", timeout=cfg.timeout)

            if "login" in page.url.lower():
                print('[AUTH-CHECK] Page loaded but redirected to login; storage state may be expired')
            else:
                print('[AUTH-CHECK] Authenticated page loaded')

            # Probe for token using a method similar to the scraper without printing it
            probe_script = """
            () => {
                try {
                    const keys = ['token','jwttoken','jwt','authToken','accessToken','authorization'];
                    for (const k of keys) {
                        try { const v = window.localStorage.getItem(k); if (v && typeof v === 'string' && v.split('.').length === 3) return {key:k, value:v}; } catch(e){}
                        try { const v2 = window.sessionStorage.getItem(k); if (v2 && typeof v2 === 'string' && v2.split('.').length === 3) return {key:k, value:v2}; } catch(e){}
                    }

                    for (let i = 0; i < localStorage.length; i++) {
                        try {
                            const k = localStorage.key(i);
                            const v = localStorage.getItem(k);
                            if (!v) continue;
                            if (typeof v === 'string' && v.split('.').length === 3) return {key:k, value:v};
                            try {
                                const parsed = JSON.parse(v);
                                if (parsed && typeof parsed === 'object') {
                                    for (const p of ['token','jwt','jwttoken','accessToken','auth']) {
                                        if (parsed[p] && typeof parsed[p] === 'string' && parsed[p].split('.').length === 3) return {key:k+'->'+p, value:parsed[p]};
                                    }
                                }
                            } catch(e){}
                        } catch(e){}
                    }

                    for (let i = 0; i < sessionStorage.length; i++) {
                        try {
                            const k = sessionStorage.key(i);
                            const v = sessionStorage.getItem(k);
                            if (!v) continue;
                            if (typeof v === 'string' && v.split('.').length === 3) return {key:k, value:v};
                            try {
                                const parsed = JSON.parse(v);
                                if (parsed && typeof parsed === 'object') {
                                    for (const p of ['token','jwt','jwttoken','accessToken','auth']) {
                                        if (parsed[p] && typeof parsed[p] === 'string' && parsed[p].split('.').length === 3) return {key:k+'->'+p, value:parsed[p]};
                                    }
                                }
                            } catch(e){}
                        } catch(e){}
                    }

                } catch(e){}
                return null;
            }
            """

            probe_result = await page.evaluate(probe_script)
            token = None
            if probe_result and isinstance(probe_result, dict) and probe_result.get('value'):
                token = probe_result['value']

            if token:
                fingerprint = hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]
                print('[AUTH-CHECK] Runtime API token found: yes')
                print('[AUTH-CHECK] Runtime API token length:', len(token))
                print('[AUTH-CHECK] Runtime API token fingerprint:', fingerprint)
            else:
                print('[AUTH-CHECK] Runtime API token not found')

            # Build API profile URL similar to the scraper behavior (api.<host>)
            from urllib.parse import urlparse
            parsed = urlparse(cfg.base_url)
            host = parsed.netloc
            scheme = parsed.scheme or 'https'
            api_host = host
            if host and not host.startswith('api.'):
                api_host = f'api.{host}'
            profile_url = f"{scheme}://{api_host}/ecosystem/userprofile/get?persona=STARTUP&userid=12804"

            print('[AUTH-CHECK] API profile request:', profile_url)

            # Use headers matching the real browser: Origin and Referer
            origin = f"{scheme}://{parsed.netloc}" if parsed.netloc else ''
            headers = {
                'Origin': origin,
                'Referer': origin + '/',
                'Accept': 'application/json, text/plain, */*',
            }
            if token:
                headers['token'] = token

            # First try an in-page fetch so browser cookies/localStorage are included
            try:
                fetch_script = """
                async ({url, headers}) => {
                    try {
                        const opts = { method: 'GET', headers: headers, credentials: 'include' };
                        const r = await fetch(url, opts);
                        const status = r.status;
                        let jsonKeys = null;
                        try {
                            const body = await r.clone().json();
                            if (body && typeof body === 'object') jsonKeys = Object.keys(body).slice(0, 50);
                        } catch(e){}
                        return {status: status, ok: r.ok, keys: jsonKeys};
                    } catch(e) {
                        return {error: String(e)};
                    }
                }
                """
                page_result = await page.evaluate(fetch_script, {"url": profile_url, "headers": headers})
                if isinstance(page_result, dict) and page_result.get('error'):
                    print('[AUTH-CHECK] In-page fetch error:', page_result.get('error'))
                else:
                    status = page_result.get('status') if isinstance(page_result, dict) else None
                    print(f"[AUTH-CHECK] Profile API response status (in-page fetch): {status}")
                    if status and 200 <= int(status) < 300:
                        keys = page_result.get('keys') if isinstance(page_result, dict) else None
                        if keys:
                            print('[AUTH-CHECK] Profile API returned JSON top-level keys:', keys)
                        print('\nAUTHENTICATED')
                        print('Profile API:', status)
                        print('Storage state: VALID')
                        return 0
                    else:
                        print('[AUTH-CHECK] In-page fetch did not return success; falling back to context.request')
            except Exception as exc:
                print('[AUTH-CHECK] Error during in-page fetch attempt:', exc)

            # Fallback to context.request.get (may not include browser cookies)
            try:
                resp = await context.request.get(profile_url, headers=headers, timeout=cfg.timeout)
                print(f"[AUTH-CHECK] Profile API response status: {resp.status}")
                if resp.ok:
                    # Print safe information about JSON shape without values
                    try:
                        body = await resp.json()
                        if isinstance(body, dict):
                            top_keys = list(body.keys())
                            print('[AUTH-CHECK] Profile API returned JSON top-level keys:', top_keys)
                            if 'data' in body and isinstance(body['data'], dict):
                                print('[AUTH-CHECK] Data object keys (sample):', list(body['data'].keys())[:20])
                        else:
                            print('[AUTH-CHECK] Profile API returned non-dict JSON of type:', type(body))

                        print('\nAUTHENTICATED')
                        print('Profile API:', resp.status)
                        print('Storage state: VALID')
                        return 0
                    except Exception:
                        text = await resp.text()
                        print('[AUTH-CHECK] Failed to parse JSON response (length):', len(text))
                        print('\nAUTHENTICATED')
                        print('Profile API:', resp.status)
                        print('Storage state: VALID (non-JSON response)')
                        return 0
                else:
                    print('[AUTH-CHECK] Profile API request failed; status indicates authorization or other error')
                    print('\nAUTHENTICATION FAILED')
                    print('Profile API:', resp.status)
                    print('Storage state: INVALID')
                    return 3
            except Exception as exc:
                print('[AUTH-CHECK] Error while calling profile API:', exc)
                print('\nAUTHENTICATION ERROR')
                return 4

        finally:
            try:
                await context.close()
            except Exception:
                pass
            try:
                await browser.close()
            except Exception:
                pass


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
