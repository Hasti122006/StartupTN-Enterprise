"""Shared StartupTN browser authentication used by the scraper and diagnostics."""
from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from config import ScraperConfig

logger = logging.getLogger("scraper.authenticate")


async def authenticate_page(page: Page, cfg: ScraperConfig) -> None:
    """Log in through the website UI and prove that navigation left the login page."""
    if not cfg.login_email or not cfg.login_password:
        raise RuntimeError("StartupTN credentials are missing from the scraper environment")
    await page.goto(cfg.login_url, wait_until="domcontentloaded", timeout=cfg.timeout)
    username = page.locator(cfg.username_selector).first
    password = page.locator(cfg.password_selector).first
    if await username.count() == 0 or await password.count() == 0:
        raise RuntimeError("StartupTN login fields were not found; update selector environment variables")
    await username.fill(cfg.login_email)
    await password.fill(cfg.login_password)
    submit = page.locator(cfg.submit_selector).first
    if await submit.count() == 0:
        raise RuntimeError("StartupTN login submit control was not found; set STARTUPTN_SUBMIT_SELECTOR")
    await submit.click()
    try:
        await page.wait_for_url(lambda url: "login" not in url.lower(), timeout=cfg.auth_timeout * 1000)
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("StartupTN login did not complete; credentials, verification, or selectors may be invalid") from exc


async def main() -> int:
    cfg = ScraperConfig()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=cfg.headless)
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        try:
            await authenticate_page(await context.new_page(), cfg)
            logger.info("StartupTN authentication verified")
            return 0
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
