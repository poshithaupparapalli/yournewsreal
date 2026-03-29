import asyncio
import json
from playwright.async_api import async_playwright

async def save_wsj_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.wsj.com")

        print("Browser is open.")
        print("Log into WSJ manually now.")
        print("When fully logged in, come back and press Enter.")
        input()

        cookies = await context.cookies()
        with open("cookies/wsj_cookies.json", "w") as f:
            json.dump(cookies, f)

        print(f"Saved {len(cookies)} cookies")
        await browser.close()

asyncio.run(save_wsj_cookies())