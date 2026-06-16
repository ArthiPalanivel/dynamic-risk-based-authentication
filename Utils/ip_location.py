import requests

def get_location(ip):

    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        data = response.json()

        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat and lon:
            return (lat, lon)

    except:
        pass

    return None
