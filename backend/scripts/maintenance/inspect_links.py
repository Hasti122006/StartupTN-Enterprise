import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://startuptn.in/', wait_until='domcontentloaded', timeout=120000)
        await page.wait_for_timeout(8000)
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href], button')).map(el => ({
                text: (el.textContent || '').trim(),
                href: el.getAttribute('href') || '',
                id: el.getAttribute('id') || '',
                className: el.getAttribute('class') || ''
            })).filter(x => x.text || x.href || x.id)
        """)
        for item in links:
            if 'startup' in (item['text']+' '+item['href']+' '+item['id']).lower():
                print(item)
        await browser.close()

asyncio.run(main())
