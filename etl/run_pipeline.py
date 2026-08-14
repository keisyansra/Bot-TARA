"""
Orkestrasi pipeline Silver + Gold secara berurutan. Jalanin ini abis
ada data bronze baru (misal abis scraping tambahan, atau upload
ODP/CBASE baru), biar nggak perlu jalanin 6 script manual satu-satu
dan nggak lupa urutannya.

Kalau salah satu step gagal, pipeline langsung berhenti (nggak lanjut
ke step berikutnya pakai data yang mungkin nggak lengkap) -- traceback
error-nya bakal keliatan di terminal.

Usage:
    python -m etl.run_pipeline
"""
from etl.silver import clean_odp, clean_prospect, clean_cbase, match_prospect_customer
from etl.gold import build_recommendation, enrich_nearest_odp

STEPS = [
    ("Silver: ODP", clean_odp.main),
    ("Silver: Prospect", clean_prospect.main),
    ("Silver: CBASE", clean_cbase.main),
    ("Silver: Fuzzy match Prospect <-> CBASE", match_prospect_customer.main),
    ("Gold: Build recommendation", build_recommendation.main),
    ("Gold: Enrich nearest ODP", enrich_nearest_odp.main),
]


def main():
    for i, (label, fn) in enumerate(STEPS, start=1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(STEPS)}] {label}")
        print("=" * 60)
        fn()

    print(f"\n{'=' * 60}")
    print("Pipeline selesai semua.")
    print("=" * 60)


if __name__ == "__main__":
    main()