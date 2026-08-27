import asyncio
from playwright.async_api import async_playwright

async def main():
    urls = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        def on_response(resp):
            url = resp.url
            if 'startuptn' in url.lower() or '/ecosystem/' in url:
                urls.append(url)
        page.on('response', on_response)
        await page.goto('https://startuptn.in', wait_until='domcontentloaded', timeout=120000)
        await page.wait_for_timeout(15000)
        await browser.close()
    for url in dict.fromkeys(urls):
        print(url)

asyncio.run(main())
