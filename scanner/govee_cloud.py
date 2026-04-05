import requests

def fetch_govee_devices(api_key):
    """Fetch devices from Govee Cloud API."""
    if not api_key:
        return []
    
    url = "https://developer-api.govee.com/v1/devices"
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        print("[Govee Cloud] Polling devices...")
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        
        if data.get("code") == 200:
            devices = data["data"]["devices"]
            cloud_results = []
            for d in devices:
                cloud_results.append({
                    "ip": "Cloud Connection", # We don't necessarily have the local IP from the cloud API
                    "mac": d.get("device"),
                    "brand": "Govee",
                    "type": "Light / " + d.get("model", "Device"),
                    "name": d.get("deviceName", "Govee Light"),
                    "model": d.get("model"),
                    "confidence": 1.0,
                    "source": "cloud"
                })
            print(f"[Govee Cloud] Found {len(cloud_results)} devices")
            return cloud_results
    except Exception as e:
        print(f"[Govee Cloud] Error: {e}")
        
    return []
