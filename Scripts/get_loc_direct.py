import subprocess
import json
import requests

def get_location():
    # 1. Пробуем стандартный termux-location
    try:
        result = subprocess.run(
            ['termux-location', '-p', 'network'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                if "latitude" in data:
                    data["provider"] = "gps"
                    return data
            except json.JSONDecodeError:
                pass
    except Exception:
        pass

    # 2. Резервный IP-геолокатор ip-api.com при ограничении Google Play / Termux:API
    try:
        response = requests.get("http://ip-api.com/json", timeout=5)
        if response.status_code == 200:
            ip_data = response.json()
            if ip_data.get("status") == "success":
                return {
                    "latitude": ip_data.get("lat"),
                    "longitude": ip_data.get("lon"),
                    "provider": "ip-geolocation",
                    "city": ip_data.get("city"),
                    "country": ip_data.get("countryCode")
                }
    except Exception as e:
        return {"error": f"Both GPS and IP Geolocation failed: {e}"}

    return {"error": "Location not available"}

if __name__ == "__main__":
    print(json.dumps(get_location(), indent=2))
