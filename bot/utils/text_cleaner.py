import re

def clean_company_name(text: str) -> str:
    if not text:
        return ""
    

    cleaned = text.strip()
    
   
    cleaned_no_prefix = re.sub(r'^(pt|cv|ud|tb)\.?\s+', '', cleaned, flags=re.IGNORECASE).strip()
    
    return cleaned_no_prefix if cleaned_no_prefix else cleaned