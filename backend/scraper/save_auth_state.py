"""Interactive helper to produce a Playwright storage state for StartupTN."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

LOGIN_URL = os.getenv(
    "SCRAPER_LOGIN_URL",
    os.getenv("STARTUPTN_LOGIN_URL", "https://startuptn.in/login"),
)


async def main(storage_path: str, timeout: int = 600):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )

        page = await context.new_page()

        print(f"Opening {LOGIN_URL} — please authenticate in the opened browser window.")

        try:
            await page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded",
                timeout=120000,
            )
        except Exception:
            print(
                f"Warning: could not load {LOGIN_URL} cleanly, "
                "opening site root instead."
            )

            await page.goto(
                "https://startuptn.in/",
                wait_until="domcontentloaded",
                timeout=120000,
            )

        print("Please complete the StartupTN login in the opened browser.")
        print(
            f"Waiting up to {timeout} seconds for the browser "
            "to leave the login page..."
        )

        # Collect tokens observed in network responses.
        observed_tokens = []

        async def _on_response(response):
            try:
                content_type = response.headers.get("content-type", "") or ""

                if "application/json" not in content_type.lower():
                    return

                try:
                    text = await response.text()
                except Exception:
                    return

                if not text:
                    return

                try:
                    payload = json.loads(text)
                except Exception:
                    return

                def _find_token(obj):
                    if not obj or not isinstance(obj, dict):
                        return None

                    for key, value in obj.items():
                        key_lower = str(key).lower()

                        if key_lower in (
                            "token",
                            "auth",
                            "jwttoken",
                            "jwt",
                            "access_token",
                            "accesstoken",
                        ):
                            if isinstance(value, str) and len(value) > 20:
                                return value

                        if isinstance(value, dict):
                            token = _find_token(value)

                            if token:
                                return token

                    return None

                token = _find_token(payload)

                if token and token not in observed_tokens:
                    observed_tokens.append(token)
                    print("Observed authentication token from network response.")

            except Exception:
                # Never allow the network listener to crash the script.
                return

        page.on("response", _on_response)

        # Wait for the user to finish authentication.
        for _ in range(timeout):
            try:
                current_url = page.url

                if "/login" not in current_url.lower():
                    print(f"Login page left: {current_url}")
                    break

            except Exception:
                pass

            await asyncio.sleep(1)

        # Give the application a moment to finish writing localStorage/cookies.
        await asyncio.sleep(3)

        storage_file = Path(storage_path)

        storage_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Save Playwright storage state.
        await context.storage_state(
            path=str(storage_file)
        )

        print()
        print("Storage state saved successfully.")
        print(f"Storage path: {storage_file.resolve()}")
        print(f"Observed network tokens: {len(observed_tokens)}")

        # Inspect localStorage for StartupTN JWT.
        try:
            local_storage = await page.evaluate(
                "() => Object.fromEntries(Object.entries(localStorage))"
            )

            if "jwttoken" in local_storage:
                print("StartupTN jwttoken found in localStorage.")
            else:
                print("WARNING: StartupTN jwttoken was not found in localStorage.")

        except Exception as exc:
            print(f"Could not inspect localStorage: {exc}")

        await browser.close()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--storage",
        required=True,
        help="Path where the Playwright storage state should be saved.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Maximum authentication wait time in seconds.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            storage_path=args.storage,
            timeout=args.timeout,
        )
    )