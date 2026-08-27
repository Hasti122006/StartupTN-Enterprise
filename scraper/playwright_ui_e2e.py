import asyncio
import time
import os
from playwright.async_api import async_playwright, TimeoutError

FRONTEND = "http://host.docker.internal:3000"
BACKEND = "http://host.docker.internal:8000"
EXPORT_DIR = "/app/data/exports"

async def main():
    results = {
        'console_errors': [],
        'failed_requests': [],
        'actions': []
    }
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # capture console errors
        page.on('console', lambda msg: results['console_errors'].append({'type': msg.type, 'text': msg.text}))

        # capture failed requests (4xx/5xx)
        def on_response(resp):
            try:
                if resp.status >= 400:
                    results['failed_requests'].append({'url': resp.url, 'status': resp.status})
            except Exception:
                pass
        page.on('response', on_response)

        print('[E2E] Opening frontend', FRONTEND)
        await page.goto(FRONTEND, wait_until='domcontentloaded', timeout=60000)
        results['actions'].append('opened_frontend')

        # navigate to scraper page
        try:
            await page.get_by_text('Scraper', exact=False).click(timeout=5000)
            results['actions'].append('navigated_to_scraper_via_link')
        except Exception:
            await page.goto(FRONTEND + '/scraper')
            results['actions'].append('navigated_to_scraper_direct')

        # wait for controls
        try:
            await page.wait_for_selector('button:has-text("Start Scraper")', timeout=10000)
            results['actions'].append('scraper_page_ready')
        except TimeoutError:
            print('[E2E] Start Scraper not found')

        # set company limit to 5
        try:
            # prefer specific input name if present
            el = await page.query_selector('input[type="number"]')
            if el:
                await el.fill('5')
                results['actions'].append('company_limit_set')
        except Exception:
            pass

        # start scraper
        try:
            await page.click('button:has-text("Start Scraper")')
            results['actions'].append('start_clicked')
            print('[E2E] Start clicked')
        except Exception as e:
            print('[E2E] Start click failed', e)
            results['actions'].append('start_click_failed')

        # wait for job chip or status
        try:
            await page.wait_for_selector('text=Status:', timeout=15000)
            results['actions'].append('job_status_visible')
        except TimeoutError:
            results['actions'].append('job_status_not_visible')

        # try Pause and Resume if available
        try:
            if await page.query_selector('button:has-text("Pause")'):
                await page.click('button:has-text("Pause")')
                results['actions'].append('pause_clicked')
                await asyncio.sleep(1)
                if await page.query_selector('button:has-text("Resume")'):
                    await page.click('button:has-text("Resume")')
                    results['actions'].append('resume_clicked')
        except Exception as e:
            results['actions'].append('pause_resume_failed')

        # wait for completion up to 90s
        try:
            await page.wait_for_selector('text=Status: COMPLETED', timeout=90000)
            results['actions'].append('reported_completed')
        except TimeoutError:
            results['actions'].append('not_reported_completed')

        # navigate to companies and count rows
        try:
            await page.goto(FRONTEND + '/companies')
            await page.wait_for_selector('table', timeout=15000)
            rows = await page.query_selector_all('table tbody tr')
            results['companies_rows'] = len(rows)
        except Exception as e:
            results['companies_rows'] = 0
            results['actions'].append(f'companies_page_error:{e}')

        # try export buttons
        try:
            await page.goto(FRONTEND + '/export')
            # click CSV export if present
            if await page.query_selector('button:has-text("Export CSV")'):
                await page.click('button:has-text("Export CSV")')
                results['actions'].append('export_csv_clicked')
            if await page.query_selector('button:has-text("Export Excel")'):
                await page.click('button:has-text("Export Excel")')
                results['actions'].append('export_excel_clicked')
        except Exception as e:
            results['actions'].append(f'export_page_error:{e}')

        # collect console/errors
        await asyncio.sleep(2)
        await browser.close()

    # inspect export directory on host (mounted into container at /app/data/exports)
    exports = []
    try:
        for name in os.listdir(EXPORT_DIR):
            path = os.path.join(EXPORT_DIR, name)
            if os.path.isfile(path):
                exports.append({'name': name, 'size': os.path.getsize(path)})
    except Exception as e:
        exports = f'error:{e}'

    print('E2E RESULTS:')
    print('actions:', results['actions'])
    print('console_errors_count:', len(results['console_errors']))
    for i, c in enumerate(results['console_errors'][:10], 1):
        print(f'console_error_{i}:', c)
    print('failed_requests_count:', len(results['failed_requests']))
    for i, r in enumerate(results['failed_requests'][:10], 1):
        print(f'failed_request_{i}:', r)
    print('companies_rows:', results.get('companies_rows'))
    print('exports:', exports)

if __name__ == '__main__':
    asyncio.run(main())
