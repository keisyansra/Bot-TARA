import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def search_location(location_name: str):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "id"
    }

    headers = {
        "User-Agent": "Bot-TARA/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        result = data[0]

        return {
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "display_name": result["display_name"]
        }

    except requests.RequestException as e:
        print(f"❌ Error Nominatim: {e}")
        return None

    except (KeyError, ValueError) as e:
        print(f"❌ Format response Nominatim tidak sesuai: {e}")
        return None

def reverse_location(latitude: float, longitude: float):
    """
    Mengubah koordinat menjadi nama/alamat lokasi.
    """

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "zoom": 18,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "Bot-TARA/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "display_name": data.get(
                "display_name",
                "Lokasi tidak diketahui"
            )
        }

    except Exception as e:
        print(f"❌ Error Nominatim reverse: {e}")
        return None