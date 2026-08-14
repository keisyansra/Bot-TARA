import re

def clean_company_name(text: str) -> str:
    if not text:
        return ""
    
    # Bersihkan karakter aneh di depan/belakang
    cleaned = text.strip()
    
    # Hapus imbuhan awal PT / CV / UD jika ingin pencarian lebih fleksibel, 
    # tetapi jika hasil hapusnya kosong, kembalikan teks asli.
    cleaned_no_prefix = re.sub(r'^(pt|cv|ud|tb)\.?\s+', '', cleaned, flags=re.IGNORECASE).strip()
    
    return cleaned_no_prefix if cleaned_no_prefix else cleaned