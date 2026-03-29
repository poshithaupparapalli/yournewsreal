"""
test_scrapers.py

Tests every scraping method on WSJ.
Run with: python test_scrapers.py

For each method it prints:
  - SUCCESS or FAILED
  - How many characters of content it got
  - First 200 chars of content so you can see quality
"""

import asyncio
import requests
import feedparser
from playwright.async_api import async_playwright

WSJ_URL = "https://www.wsj.com"
WSJ_ARTICLE = "https://www.wsj.com/finance"

def print_result(method_name, content, error=None):
    print(f"\n{'='*50}")
    print(f"METHOD: {method_name}")
    if error:
        print(f"RESULT: FAILED")
        print(f"REASON: {error}")
    elif content and len(content) > 200:
        print(f"RESULT: SUCCESS")
        print(f"CHARS:  {len(content)}")
        print(f"PREVIEW: {content[:200]}...")
    else:
        print(f"RESULT: FAILED — got content but too short ({len(content) if content else 0} chars)")
        if content:
            print(f"GOT: {content[:200]}")


# ─────────────────────────────────────────
# METHOD 1: Simple HTTP request
# ─────────────────────────────────────────
def test_simple_http():
    try:
        response = requests.get(WSJ_URL, timeout=10)
        content = response.text
        print_result("1. Simple HTTP request", content)
    except Exception as e:
        print_result("1. Simple HTTP request", None, str(e))


# ─────────────────────────────────────────
# METHOD 2: HTTP request with browser headers
# ─────────────────────────────────────────
def test_http_with_headers():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com",
        }
        response = requests.get(WSJ_URL, headers=headers, timeout=10)
        content = response.text
        print_result("2. HTTP with browser headers", content)
    except Exception as e:
        print_result("2. HTTP with browser headers", None, str(e))


# ─────────────────────────────────────────
# METHOD 3: RSS feed
# ─────────────────────────────────────────
def test_rss():
    try:
        rss_urls = [
            "https://feeds.a.mm.com/wsj/xml/rss/3_7011.xml",
            "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
            "https://www.wsj.com/xml/rss/3_7014.xml",
        ]
        all_content = ""
        for url in rss_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                all_content += entry.get("title", "") + " "
                all_content += entry.get("summary", "") + " "

        print_result("3. RSS feed", all_content)
    except Exception as e:
        print_result("3. RSS feed", None, str(e))


# ─────────────────────────────────────────
# METHOD 4: Playwright (basic, no stealth)
# ─────────────────────────────────────────
async def test_playwright_basic():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(WSJ_URL, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)

            # try to get article text
            content = await page.inner_text("body")
            await browser.close()
            print_result("4. Playwright basic", content)
    except Exception as e:
        print_result("4. Playwright basic", None, str(e))


# ─────────────────────────────────────────
# METHOD 5: Playwright with stealth
# ─────────────────────────────────────────
async def test_playwright_stealth():
    try:
        from playwright_stealth import stealth_async
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await stealth_async(page)
            await page.goto(WSJ_URL, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)

            content = await page.inner_text("body")
            await browser.close()
            print_result("5. Playwright with stealth", content)
    except ImportError:
        print_result("5. Playwright with stealth", None,
                     "playwright_stealth not installed — run: pip install playwright-stealth")
    except Exception as e:
        print_result("5. Playwright with stealth", None, str(e))


# ─────────────────────────────────────────
# METHOD 6: Jina Reader
# ─────────────────────────────────────────
def test_jina():
    try:
        jina_url = f"https://r.jina.ai/{WSJ_URL}"
        response = requests.get(jina_url, timeout=30)
        content = response.text
        print_result("6. Jina Reader", content)
    except Exception as e:
        print_result("6. Jina Reader", None, str(e))


# ─────────────────────────────────────────
# METHOD 7: Jina on a specific article
# ─────────────────────────────────────────
def test_jina_article():
    try:
        # Try a specific WSJ article URL if you have one
        # Replace this with a real WSJ article URL
        article_url = "https://www.wsj.com/finance/stocks/stock-market-news"
        jina_url = f"https://r.jina.ai/{article_url}"
        response = requests.get(jina_url, timeout=30)
        content = response.text
        print_result("7. Jina on specific article", content)
    except Exception as e:
        print_result("7. Jina on specific article", None, str(e))


# ─────────────────────────────────────────
# METHOD 8: Google News RSS proxy for WSJ
# ─────────────────────────────────────────
def test_google_news_proxy():
    try:
        url = "https://news.google.com/rss/search?q=when:24h+allinurl:wsj.com&ceid=US:en&hl=en-US&gl=US"
        feed = feedparser.parse(url)
        content = ""
        for entry in feed.entries[:5]:
            content += entry.get("title", "") + " "
            content += entry.get("summary", "") + " "
        print_result("8. Google News RSS proxy", content)
    except Exception as e:
        print_result("8. Google News RSS proxy", None, str(e))


# ─────────────────────────────────────────
# METHOD 9: Playwright headless=False (visible)
# So you can SEE what the browser sees
# ─────────────────────────────────────────
async def test_playwright_visible():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            await page.goto(WSJ_URL, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(5000)  # wait 5 seconds so you can see

            content = await page.inner_text("body")
            await browser.close()
            print_result("9. Playwright visible (headless=False)", content)
    except Exception as e:
        print_result("9. Playwright visible (headless=False)", None, str(e))


# ─────────────────────────────────────────
# MAIN — runs all methods and prints results
# ─────────────────────────────────────────
async def main():
    print("\n" + "="*50)
    print("SCRAPING TEST — WSJ")
    print("Testing every method. This takes ~60 seconds.")
    print("="*50)

    # Synchronous methods
    print("\n--- Running synchronous methods ---")
    test_simple_http()
    test_http_with_headers()
    test_rss()
    test_jina()
    test_jina_article()
    test_google_news_proxy()

    # Async methods (require browser)
    print("\n--- Running browser methods ---")
    await test_playwright_basic()
    await test_playwright_stealth()
    await test_playwright_visible()

    # Summary
    print("\n" + "="*50)
    print("ALL METHODS TESTED")
    print("Look above for SUCCESS or FAILED on each one")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())