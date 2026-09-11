import time
import urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError
from ingestion.parser import parse_result_card

query = "restoran di Malang"
url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        locale="id-ID",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"
    )

    page = context.new_page()
    page.set_default_timeout(10000)

    print(f"Membuka: {query}")

    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    try:
        btn = page.locator('button:has-text("Setuju")')
        if btn.count() > 0:
            btn.first.click()
    except Exception:
        pass

    try:
        page.wait_for_selector('div[role="feed"]', timeout=10000)
    except TimeoutError:
        print("Feed Google Maps tidak ditemukan.")
        browser.close()
        exit()

    cards = page.locator('div[role="article"]').element_handles()

    print(f"\nJumlah card yang ditemukan: {len(cards)}")
    print("=" * 60)

    # Ambil maksimal 5 card untuk test
    for i, card in enumerate(cards[:5], start=1):
        result = parse_result_card(card, "restoran")

        print(f"\n--HASIL PARSE CARD {i}--")
        print(result)
        print('-' * 60)

    browser.close()