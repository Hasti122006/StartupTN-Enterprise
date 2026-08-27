import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        seen = []
        async def handle_request(req):
            url = req.url
            if 'api.startuptn' in url or '/ecosystem/' in url:
                seen.append((req.method, url, req.post_data))
        page.on('request', lambda req: asyncio.create_task(handle_request(req)))
        await page.goto('https://startuptn.in', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(10000)
        for item in seen:
            print(item[0], item[1])
            if item[2]:
                print(item[2])
            print('---')
        print('TOTAL', len(seen))
        await browser.close()

asyncio.run(main())
