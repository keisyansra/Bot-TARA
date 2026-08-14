import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright


def extract_phone(text):
    """Ambil nomor telepon murni dari teks mentah (dipinjam & disesuaikan dari script pertama)."""
    if not text:
        return ""
    match = re.search(r'(\+?62[\s-]?\d+|\(0\d+\)[\s-]?\d+|08\d+[\s-]?\d+[\s-]?\d+)', text)
    return match.group(0).strip() if match else ""


def cocok_kata_kunci(nama: str, kata_kunci_list: list) -> bool:
    """Cek apakah nama tempat mengandung salah satu kata kunci (PT/CV/UD) sebagai kata utuh.
    Ini nyaring hasil yang Maps balikin tapi sebenernya gak relevan (namanya gak ada PT/CV/UD-nya)."""
    if not nama:
        return False
    pattern = r"\b(" + "|".join(re.escape(k) for k in kata_kunci_list) + r")\b"
    return bool(re.search(pattern, nama, re.IGNORECASE))


def scrape_gmaps(keyword: str, kata_kunci_list: list, max_hasil: int = None, headless: bool = False):
    """Scraping 1 keyword pencarian di Google Maps, balikin list of dict."""
    hasil = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        panel_selector = 'div[role="feed"]'
        try:
            page.wait_for_selector(panel_selector, timeout=15000)
        except Exception:
            print(f"[SKIP] Panel hasil gak ketemu buat keyword '{keyword}'.")
            browser.close()
            return hasil

        # Scroll ADAPTIF: berenti otomatis kalau 3x scroll berturut-turut gak nambah card baru,
        # bukan angka scroll tetap kayak script pertama (`for _ in range(6)`).
        card_selector = 'div[role="feed"] a.hfpxzc'
        prev_count = 0
        stagnant_rounds = 0

        while True:
            cards = page.query_selector_all(card_selector)
            if max_hasil is not None and len(cards) >= max_hasil:
                break

            page.eval_on_selector(panel_selector, "el => el.scrollBy(0, 1500)")
            page.wait_for_timeout(1500)

            cards = page.query_selector_all(card_selector)
            if len(cards) == prev_count:
                stagnant_rounds += 1
                if stagnant_rounds >= 3:
                    break
            else:
                stagnant_rounds = 0
            prev_count = len(cards)

        cards = page.query_selector_all(card_selector)
        print(f"[{keyword}] Total card ditemukan: {len(cards)}")

        jumlah_dicek = len(cards) if max_hasil is None else min(len(cards), max_hasil)
        for i in range(jumlah_dicek):
            cards = page.query_selector_all(card_selector)  # refresh referensi tiap loop
            card = cards[i]

            try:
                card.click()
                page.wait_for_timeout(2500)

                # Nama tempat, dari panel detail (bukan card list kiri)
                nama_el = page.query_selector("h1.DUwDvf")
                nama = nama_el.inner_text().strip() if nama_el else ""

                if not cocok_kata_kunci(nama, kata_kunci_list):
                    continue  # skip kalau namanya gak ada PT/CV/UD-nya

                # Alamat & telepon: pake selector data-item-id spesifik (bukan nebak dari teks jumbled)
                alamat_el = page.query_selector('button[data-item-id="address"]')
                alamat = alamat_el.inner_text().strip() if alamat_el else ""

                telp_el = page.query_selector('button[data-item-id^="phone"]')
                telp_raw = telp_el.inner_text().strip() if telp_el else ""
                telepon = extract_phone(telp_raw)  # dibersihin jadi format nomor murni

                rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
                rating = rating_el.inner_text().strip() if rating_el else ""

                kategori_el = page.query_selector("button.DkEaL")
                kategori = kategori_el.inner_text().strip() if kategori_el else ""

                # Koordinat PRESISI milik tempat (pola !3d...!4d...), bukan posisi map saat itu
                # (pola @lat,lng bisa geser kalau map di-pan/zoom, jadi kurang akurat)
                current_url = page.url
                koordinat_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", current_url)
                if koordinat_match:
                    lat, lng = float(koordinat_match.group(1)), float(koordinat_match.group(2))
                else:
                    lat, lng = None, None

                hasil.append({
                    "nama": nama,
                    "kategori": kategori,
                    "alamat": alamat,
                    "telepon": telepon,
                    "rating": rating,
                    "latitude": lat,
                    "longitude": lng,
                    "url_gmaps": current_url,
                })

                print(f"  [{len(hasil)}] Ditemukan: {nama}")

            except Exception as e:
                print(f"  [GAGAL] Card ke-{i}: {e}")
                continue

        browser.close()

    return hasil


def simpan_excel(data, nama_file):
    """Simpan list of dict ke Excel. Bikin folder tujuan otomatis kalau belum ada."""
    if not data:
        print(f"[INFO] Tidak ada data untuk disimpen ke '{nama_file}'.")
        return

    folder = os.path.dirname(nama_file)
    if folder and not os.path.exists(folder):
        os.makedirs(folder) 

    pd.DataFrame(data).to_excel(nama_file, index=False, engine="openpyxl")
    print(f"[INFO] {len(data)} data berhasil disimpan ke '{nama_file}'")


if __name__ == "__main__":

    kota_list = [
        # Witel Kediri
        "Kediri", "Nganjuk", "Tulungagung", "Blitar", "Kota Kediri", "Trenggalek", "Kota Blitar",
        # Witel Madiun
        "Tuban", "Bojonegoro", "Ponorogo", "Ngawi", "Magetan", "Madiun", "Kota Madiun", "Pacitan",
        # Witel Malang 
        "Malang", "Kepanjen", "Batu"
    ] 

    kata_kunci_list = [
        "PT", "CV", "UD"
    ]

    JUMLAH_MAKSIMAL_PER_KEYWORD = None  # None = ambil semua yang ketemu

    FOLDER_OUTPUT = "data/Scraping_PTCV_JatimBarat"

    # ============================================================
    # CHECKPOINT: tiap kota selesai, langsung disimpan ke file SENDIRI.
    # Kalau file kota itu SUDAH ADA, kota itu di-skip (gak diulang).
    # Jadi kalau script berhenti di tengah jalan (error/internet putus),
    # tinggal run ulang -> otomatis lanjut dari kota yang belum kelar.
    # ============================================================
    for kota in kota_list:
        nama_kota_file = kota.replace(" ", "_")
        file_hasil = f"{FOLDER_OUTPUT}/scraping_ptcv_{nama_kota_file}.xlsx"

        if os.path.exists(file_hasil):
            print(f"\n=== Lewati '{kota}' (file udah ada: {file_hasil}) ===")
            continue

        print(f"\n=== Memproses kota: {kota} ===")
        data_kota = []

        for kunci in kata_kunci_list:
            kw = f"{kunci} di {kota}"
            print(f"\n--- Mencari: {kw} ---")
            hasil_kw = scrape_gmaps(kw, kata_kunci_list, max_hasil=JUMLAH_MAKSIMAL_PER_KEYWORD, headless=False)
            data_kota.extend(hasil_kw)

        # Dedup dalam kota yang sama (kalau ada nama yang sama muncul di beberapa keyword)
        data_kota_unik = []
        nama_sudah_ada = set()
        for row in data_kota:
            if row["nama"] not in nama_sudah_ada:
                data_kota_unik.append(row)
                nama_sudah_ada.add(row["nama"])

        simpan_excel(data_kota_unik, file_hasil)

    print("\n✅ SELESAI semua kota.")