import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        seen = {}
        def on_request(req):
            url = req.url
            if 'api.startuptn' in url or 'startuptn' in url:
                if url not in seen:
                    seen[url] = {'method': req.method, 'post_data': req.post_data()}
        def on_response(res):
            url = res.url
            if 'api.startuptn' in url or 'startuptn' in url:
                if url not in seen:
                    seen[url] = {'method': None, 'post_data': None}
        page.on('request', on_request)
        page.on('response', on_response)
        await page.goto('https://startuptn.in', wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(10000)
        for url, meta in seen.items():
            print(url)
            print(' METHOD', meta['method'])
            if meta['post_data']:
                print(' POST', meta['post_data'])
            print('---')
        print('TOTAL', len(seen))
        await browser.close()

asyncio.run(main())
