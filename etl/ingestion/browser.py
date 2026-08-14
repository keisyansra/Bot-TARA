import time
import urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError
from etl.ingestion.parser import parse_result_card

MAX_SCROLLS = 30
MAX_RESULTS_PER_QUERY = 150
SCROLL_PAUSE_TIME = 2.0

def scroll_and_extract(page, kategori):
    """
    Melakukan scroll pada panel hasil pencarian dan mengekstrak datanya.
    Menggunakan mekanisme scroll bertahap dan berhenti saat tidak ada hasil baru
    atau limit tercapai.
    """
    # Menunggu kontainer hasil pencarian (role=feed)
    try:
        page.wait_for_selector('div[role="feed"]', timeout=10000)
    except TimeoutError:
        # Jika tidak ada hasil pencarian (misal, langsung masuk ke detail tempat atau kosong)
        # Coba cek apakah kita berada di halaman detail
        if page.locator('h1.fontHeadlineLarge').count() > 0:
            # Langsung ekstrak satu elemen karena masuk ke halaman detail
            body = page.locator('body')
            res = parse_result_card(body, kategori)
            return [res] if res and res["nama"] else []
        return []
        
    feed_locator = page.locator('div[role="feed"]')
    
    seen_urls = set()
    extracted_data = []
    
    prev_count = 0
    stagnant_count = 0
    
    for _ in range(MAX_SCROLLS):
        # Ambil semua card hasil yang terlihat saat ini
        cards = feed_locator.locator('div[role="article"]').element_handles()
        
        # Ekstrak data dari card
        for card in cards:
            result = parse_result_card(card, kategori)
            if result and result["url_gmaps"] and result["url_gmaps"] not in seen_urls:
                if result["nama"]: # Pastikan ada nama
                    seen_urls.add(result["url_gmaps"])
                    extracted_data.append(result)
                    
        if len(extracted_data) >= MAX_RESULTS_PER_QUERY:
            break
            
        current_count = len(extracted_data)
        if current_count == prev_count:
            stagnant_count += 1
            if stagnant_count >= 3:
                # Berhenti jika 3 kali scroll tidak ada hasil baru (sudah mentok)
                break
        else:
            stagnant_count = 0
            
        prev_count = current_count
        
        # Lakukan scroll down di dalam elemen feed
        # Coba cari elemen scrollable di dalam feed atau feed itu sendiri
        page.evaluate("""
            const feed = document.querySelector('div[role="feed"]');
            if(feed) feed.scrollBy(0, 1000);
            else window.scrollBy(0, 1000);
        """)
        
        time.sleep(SCROLL_PAUSE_TIME)
        
    return extracted_data

def scrape_google_maps(wilayah, kategori):
    """
    Melakukan pencarian di Google Maps untuk kombinasi wilayah dan kategori.
    Mengembalikan list of dictionaries berisi raw data prospect.
    """
    query = f"{kategori} di {wilayah}"
    url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}"
    
    results = []
    
    with sync_playwright() as p:
        # Gunakan Chromium (Google Chrome / Edge)
        browser = p.chromium.launch(headless=True)
        # Gunakan context dengan locale ID agar struktur bahasa Maps konsisten
        context = browser.new_context(
            locale="id-ID",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        # Set default timeout untuk navigasi
        page.set_default_navigation_timeout(30000)
        page.set_default_timeout(10000)
        
        try:
            page.goto(url)
            # Accept cookies dialog if appears (often in EU, less in ID but good to have)
            try:
                btn = page.locator('button:has-text("Setuju")')
                if btn.count() > 0:
                    btn.first.click()
            except Exception:
                pass
                
            results = scroll_and_extract(page, kategori)
            
        except Exception as e:
            # Re-raise agar orchestrator bisa tangani logging error
            raise e
        finally:
            # Selalu pastikan cleanup browser dan context
            try:
                page.close()
                context.close()
                browser.close()
            except Exception:
                pass
                
    return results
