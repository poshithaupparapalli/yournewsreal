"""
scraper_tester.py

Interactive tool to test every scraping method on any news outlet.
Run with: python3 scraper_tester.py

You choose which outlet to test.
It tries every method and shows you exactly what each one got.
"""

import asyncio
import requests
import feedparser
import json
import os
from playwright.async_api import async_playwright

# ─────────────────────────────────────────────────────
# NEWS OUTLETS — add more here anytime
# ─────────────────────────────────────────────────────

OUTLETS = {
    # TECHNOLOGY
    "1":  {
        "name": "TechCrunch",
        "url": "https://techcrunch.com",
        "rss": "https://techcrunch.com/feed/",
        "article_filter": "techcrunch.com/20",
        "body_selector": ".entry-content p, div.article-content p",
        "jina_url": "https://techcrunch.com",
        "google_query": "site:techcrunch.com"
    },
    "2":  {
        "name": "The Verge",
        "url": "https://www.theverge.com",
        "rss": "https://www.theverge.com/rss/index.xml",
        "article_filter": "theverge.com/",
        "body_selector": "div.duet--article--article-body-component p",
        "jina_url": "https://www.theverge.com",
        "google_query": "site:theverge.com"
    },
    "3":  {
        "name": "Ars Technica",
        "url": "https://arstechnica.com",
        "rss": "https://feeds.arstechnica.com/arstechnica/index",
        "article_filter": "arstechnica.com/",
        "body_selector": "div.article-content p",
        "jina_url": "https://arstechnica.com",
        "google_query": "site:arstechnica.com"
    },
    "4":  {
        "name": "Wired",
        "url": "https://www.wired.com",
        "rss": "https://www.wired.com/feed/rss",
        "article_filter": "wired.com/story",
        "body_selector": "div.body__inner-container p",
        "jina_url": "https://www.wired.com",
        "google_query": "site:wired.com"
    },

    # GENERAL NEWS
    "5":  {
        "name": "The Guardian",
        "url": "https://www.theguardian.com",
        "rss": "https://www.theguardian.com/world/rss",
        "article_filter": "theguardian.com/",
        "body_selector": "div.article-body-commercial-selector p",
        "jina_url": "https://www.theguardian.com",
        "google_query": "site:theguardian.com"
    },
    "6":  {
        "name": "BBC News",
        "url": "https://www.bbc.com/news",
        "rss": "https://feeds.bbci.co.uk/news/rss.xml",
        "article_filter": "bbc.com/news",
        "body_selector": "article p, div[data-component='text-block'] p",
        "jina_url": "https://www.bbc.com/news",
        "google_query": "site:bbc.com/news"
    },
    "7":  {
        "name": "NPR",
        "url": "https://www.npr.org",
        "rss": "https://feeds.npr.org/1001/rss.xml",
        "article_filter": "npr.org/",
        "body_selector": "div.storytext p",
        "jina_url": "https://www.npr.org",
        "google_query": "site:npr.org"
    },
    "8":  {
        "name": "AP News",
        "url": "https://apnews.com",
        "rss": None,
        "article_filter": "apnews.com/article",
        "body_selector": ".RichTextStoryBody p",
        "jina_url": "https://apnews.com",
        "google_query": "site:apnews.com"
    },

    # BUSINESS
    "9":  {
        "name": "Reuters",
        "url": "https://www.reuters.com",
        "rss": "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en",
        "article_filter": "reuters.com/",
        "body_selector": "div.article-body p",
        "jina_url": "https://www.reuters.com",
        "google_query": "site:reuters.com"
    },
    "10": {
        "name": "Bloomberg",
        "url": "https://www.bloomberg.com",
        "rss": "https://feeds.bloomberg.com/markets/news.rss",
        "article_filter": "bloomberg.com/",
        "body_selector": "div.body-content p",
        "jina_url": "https://www.bloomberg.com",
        "google_query": "site:bloomberg.com"
    },
    "11": {
        "name": "Wall Street Journal",
        "url": "https://www.wsj.com",
        "rss": "https://feeds.a.mm.com/wsj/xml/rss/3_7011.xml",
        "article_filter": "wsj.com/",
        "body_selector": "div.article-content p",
        "jina_url": "https://www.wsj.com",
        "google_query": "site:wsj.com"
    },

    # SPORTS
    "12": {
        "name": "ESPN",
        "url": "https://www.espn.com",
        "rss": "https://www.espn.com/espn/rss/news",
        "article_filter": "espn.com/",
        "body_selector": "div.article-body p",
        "jina_url": "https://www.espn.com",
        "google_query": "site:espn.com"
    },

    # HEALTHCARE
    "13": {
        "name": "STAT News",
        "url": "https://www.statnews.com",
        "rss": "https://www.statnews.com/feed/",
        "article_filter": "statnews.com/",
        "body_selector": "div.entry-content p",
        "jina_url": "https://www.statnews.com",
        "google_query": "site:statnews.com"
    },

    # FOOD
    "14": {
        "name": "Eater",
        "url": "https://www.eater.com",
        "rss": "https://www.eater.com/rss/index.xml",
        "article_filter": "eater.com/",
        "body_selector": "div.c-entry-content p",
        "jina_url": "https://www.eater.com",
        "google_query": "site:eater.com"
    },
}


# ─────────────────────────────────────────────────────
# RESULT PRINTER
# ─────────────────────────────────────────────────────

def print_result(method, success, chars, preview, error=None):
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"\n  {status} — {method}")
    if error:
        print(f"  Error: {error}")
    elif success:
        print(f"  Characters: {chars}")
        print(f"  Preview: {preview[:300]}...")
    else:
        print(f"  Got {chars} chars — not enough content")
        if preview:
            print(f"  Got: {preview[:200]}")


def is_success(text):
    """Check if we actually got real article content"""
    if not text or len(text) < 500:
        return False
    # Check it's not just a bot block page
    block_signals = ["enable javascript", "access denied", "blocked",
                     "cloudflare", "please enable", "bot activity", "unusual activity"]
    text_lower = text.lower()
    for signal in block_signals:
        if signal in text_lower:
            return False
    return True


# ─────────────────────────────────────────────────────
# METHOD 1: Simple HTTP
# ─────────────────────────────────────────────────────

def test_simple_http(outlet):
    try:
        response = requests.get(outlet["url"], timeout=15)
        text = response.text
        success = is_success(text)
        print_result("Simple HTTP request", success, len(text), text)
    except Exception as e:
        print_result("Simple HTTP request", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 2: HTTP with headers
# ─────────────────────────────────────────────────────

def test_http_headers(outlet):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com",
        }
        response = requests.get(outlet["url"], headers=headers, timeout=15)
        text = response.text
        success = is_success(text)
        print_result("HTTP with browser headers", success, len(text), text)
    except Exception as e:
        print_result("HTTP with browser headers", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 3: RSS feed
# ─────────────────────────────────────────────────────

def test_rss(outlet):
    if not outlet["rss"]:
        print_result("RSS feed", False, 0, "", "No RSS feed configured for this outlet")
        return
    try:
        feed = feedparser.parse(outlet["rss"])
        content = ""
        for entry in feed.entries[:5]:
            content += entry.get("title", "") + "\n"
            content += entry.get("summary", "") + "\n\n"
        success = len(content) > 200
        print_result("RSS feed", success, len(content), content)
    except Exception as e:
        print_result("RSS feed", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 4: Jina Reader
# ─────────────────────────────────────────────────────

def test_jina(outlet):
    try:
        url = f"https://r.jina.ai/{outlet['jina_url']}"
        response = requests.get(url, timeout=30)
        text = response.text
        success = is_success(text)
        print_result("Jina Reader", success, len(text), text)
    except Exception as e:
        print_result("Jina Reader", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 5: Google News RSS proxy
# ─────────────────────────────────────────────────────

def test_google_news(outlet):
    try:
        query = outlet["google_query"].replace("site:", "allinurl:")
        url = f"https://news.google.com/rss/search?q=when:24h+{query}&ceid=US:en&hl=en-US&gl=US"
        feed = feedparser.parse(url)
        content = ""
        for entry in feed.entries[:5]:
            content += entry.get("title", "") + "\n"
            content += entry.get("summary", "") + "\n\n"
        success = len(content) > 200
        print_result("Google News RSS proxy", success, len(content), content)
    except Exception as e:
        print_result("Google News RSS proxy", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 6: Playwright basic
# ─────────────────────────────────────────────────────

async def test_playwright(outlet):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            await page.goto(outlet["url"], timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)

            # Try the specific body selector first
            els = await page.query_selector_all(outlet["body_selector"])
            if els:
                text = " ".join([await el.inner_text() for el in els[:10]])
            else:
                text = await page.inner_text("body")

            await browser.close()
            success = is_success(text)
            print_result("Playwright (headless)", success, len(text), text)
    except Exception as e:
        print_result("Playwright (headless)", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 7: Playwright visible — you can watch it
# ─────────────────────────────────────────────────────

async def test_playwright_visible(outlet):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            await page.goto(outlet["url"], timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(4000)

            els = await page.query_selector_all(outlet["body_selector"])
            if els:
                text = " ".join([await el.inner_text() for el in els[:10]])
            else:
                text = await page.inner_text("body")

            await browser.close()
            success = is_success(text)
            print_result("Playwright (visible browser)", success, len(text), text)
    except Exception as e:
        print_result("Playwright (visible browser)", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# METHOD 8: RSS + Jina enrichment on first article
# ─────────────────────────────────────────────────────

def test_rss_plus_jina(outlet):
    if not outlet["rss"]:
        print_result("RSS + Jina enrichment", False, 0, "", "No RSS feed configured")
        return
    try:
        # Step 1: get article URL from RSS
        feed = feedparser.parse(outlet["rss"])
        if not feed.entries:
            print_result("RSS + Jina enrichment", False, 0, "", "RSS feed returned no entries")
            return

        first_url = feed.entries[0].get("link", "")
        if not first_url:
            print_result("RSS + Jina enrichment", False, 0, "", "No URL in RSS entry")
            return

        print(f"  → Found article URL: {first_url[:80]}")

        # Step 2: use Jina to get full text
        jina_url = f"https://r.jina.ai/{first_url}"
        response = requests.get(jina_url, timeout=30)
        text = response.text
        success = is_success(text)
        print_result("RSS + Jina enrichment", success, len(text), text)
    except Exception as e:
        print_result("RSS + Jina enrichment", False, 0, "", str(e))


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────

async def main():
    # Show outlet menu
    print("\n" + "="*60)
    print("SCRAPER TESTER — pick an outlet to test")
    print("="*60)

    print("\nTECHNOLOGY")
    print("  1.  TechCrunch")
    print("  2.  The Verge")
    print("  3.  Ars Technica")
    print("  4.  Wired")
    print("\nGENERAL NEWS")
    print("  5.  The Guardian")
    print("  6.  BBC News")
    print("  7.  NPR")
    print("  8.  AP News")
    print("\nBUSINESS")
    print("  9.  Reuters")
    print("  10. Bloomberg")
    print("  11. Wall Street Journal")
    print("\nSPORTS")
    print("  12. ESPN")
    print("\nHEALTHCARE")
    print("  13. STAT News")
    print("\nFOOD")
    print("  14. Eater")

    choice = input("\nEnter number: ").strip()

    if choice not in OUTLETS:
        print("Invalid choice. Run again and pick a number from the list.")
        return

    outlet = OUTLETS[choice]

    print(f"\n{'='*60}")
    print(f"TESTING: {outlet['name']}")
    print(f"URL: {outlet['url']}")
    print(f"{'='*60}")
    print("Running all 8 methods...\n")

    # Run all methods
    print("── METHOD 1: Simple HTTP ──")
    test_simple_http(outlet)

    print("\n── METHOD 2: HTTP with headers ──")
    test_http_headers(outlet)

    print("\n── METHOD 3: RSS feed ──")
    test_rss(outlet)

    print("\n── METHOD 4: Jina Reader ──")
    test_jina(outlet)

    print("\n── METHOD 5: Google News RSS proxy ──")
    test_google_news(outlet)

    print("\n── METHOD 6: Playwright headless ──")
    await test_playwright(outlet)

    print("\n── METHOD 7: Playwright visible ──")
    await test_playwright_visible(outlet)

    print("\n── METHOD 8: RSS + Jina enrichment ──")
    test_rss_plus_jina(outlet)

    # Summary
    print(f"\n{'='*60}")
    print(f"DONE — {outlet['name']}")
    print("Check above for ✅ SUCCESS or ❌ FAILED on each method")
    print("The methods that succeed are the ones to use in your scraper")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())