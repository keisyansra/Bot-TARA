import re

# Kata umum yang dianggap noise untuk dihapus dari nama perusahaan/prospek
COMMON_WORDS = re.compile(r"\b(pt|cv|ud|tb|tbk)\b", re.IGNORECASE)

def normalize_name(name) -> str:
    """
    Normalisasi nama dengan aturan:
    1. Lowercase
    2. Titik dan koma menjadi spasi
    3. Hapus noise word (PT, CV, dll)
    4. Rapikan multiple spaces menjadi satu spasi
    5. Trim spasi awal dan akhir
    """
    if not isinstance(name, str) or not name.strip():
        return ""
    
    n = name.lower()
    # Ubah titik dan koma menjadi spasi
    n = re.sub(r"[.,]", " ", n)
    # Hapus kata noise
    n = COMMON_WORDS.sub(" ", n)
    # Rapikan spasi ganda dan trim
    n = re.sub(r"\s+", " ", n).strip()
    return n
