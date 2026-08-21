import requests


FASTAPI_BASE_URL = "http://192.168.15.146:8000"  

def get_nearby_prospects_from_fastapi(lat: float, lon: float, limit: int = 20):
    """Menembak GET /api/prospects/nearby"""
    try:
        url = f"{FASTAPI_BASE_URL}/api/prospects/nearby"
        params = {"lat": lat, "lon": lon, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, dict):
                return res_json.get("data", [])
            elif isinstance(res_json, list):
                return res_json
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error HTTP (Nearby): {e}")
    return []

def search_prospects_from_fastapi(query: str, limit: int = 20):
    """Menembak GET /api/prospects/search"""
    try:
        url = f"{FASTAPI_BASE_URL}/api/prospects/search"
        params = {"query": query, "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, dict):
                return res_json.get("data", [])
            elif isinstance(res_json, list):
                return res_json
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error HTTP ke API (Search): {e}")
    return []