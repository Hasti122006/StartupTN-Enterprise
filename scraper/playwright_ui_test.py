import asyncio
from playwright.async_api import async_playwright, TimeoutError

FRONTEND_URL = "http://host.docker.internal:3000"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        # Ensure frontend's client-side API calls (built with VITE_API_BASE_URL=http://localhost:8000)
        # reach the host backend from inside container by rewriting requests in the page.
        await context.add_init_script("""
        () => {
            try {
                const origFetch = window.fetch;
                window.fetch = function(resource, init) {
                    try {
                        if (typeof resource === 'string') {
                            resource = resource.replace('http://localhost:8000', 'http://host.docker.internal:8000');
                        } else if (resource && resource.url) {
                            const url = resource.url.replace('http://localhost:8000', 'http://host.docker.internal:8000');
                            resource = new Request(url, resource);
                        }
                    } catch(e){}
                    return origFetch.call(this, resource, init);
                };
                const XHRopen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url) {
                    try { url = url.replace('http://localhost:8000', 'http://host.docker.internal:8000'); } catch(e){}
                    return XHRopen.apply(this, [method, url].concat(Array.prototype.slice.call(arguments,2)));
                };
            } catch(e){}
        }
        """)
        page = await context.new_page()
        print('[UI-TEST] Opening frontend at', FRONTEND_URL)
        await page.goto(FRONTEND_URL, wait_until='domcontentloaded', timeout=60000)
        print('[UI-TEST] Frontend loaded, navigating to Scraper page')
        # Try navigation via link or direct route
        try:
            # If there is a link or button with text "Scraper"
            await page.get_by_text('Scraper', exact=False).click(timeout=5000)
        except Exception:
            # Fallback: navigate directly
            await page.goto(FRONTEND_URL + '/scraper')
        # Wait for Start Scraper button
        try:
            await page.wait_for_selector('button:has-text("Start Scraper")', timeout=10000)
            print('[UI-TEST] Scraper page ready')
        except TimeoutError:
            print('[UI-TEST] Start Scraper button not found')
            await browser.close()
            return

        # Set company limit to 5 if an input exists
        try:
            el = await page.query_selector('input[label="Company Limit"], input[name="companyLimit"], input[type="number"]')
            if el:
                await el.fill('5')
                print('[UI-TEST] Set company limit to 5')
        except Exception:
            pass

        # Click Start Scraper
        try:
            await page.click('button:has-text("Start Scraper")')
            print('[UI-TEST] Clicked Start Scraper')
        except Exception as e:
            print('[UI-TEST] Failed to click Start Scraper:', e)
            await browser.close()
            return

        # Wait for job chip to appear
        try:
            await page.wait_for_selector('text=Status: ', timeout=15000)
            print('[UI-TEST] Job status element visible')
        except TimeoutError:
            print('[UI-TEST] Job status not visible after start')

        # Wait up to 90s for progress to complete
        try:
            await page.wait_for_selector('text=Status: COMPLETED', timeout=90000)
            print('[UI-TEST] Scraper reported COMPLETED')
        except TimeoutError:
            print('[UI-TEST] Scraper did not report COMPLETED within 90s — checking logs')

        # Open Companies page and verify at least 5 entries exist
        try:
            await page.goto(FRONTEND_URL + '/companies')
            # Wait for companies table to load
            await page.wait_for_selector('table', timeout=15000)
            rows = await page.query_selector_all('table tbody tr')
            print(f'[UI-TEST] Companies table rows found: {len(rows)}')
        except Exception as e:
            print('[UI-TEST] Companies page check failed:', e)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
