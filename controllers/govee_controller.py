import requests
from .base_controller import BaseController

class GoveeController(BaseController):
    API_URL = "https://developer-api.govee.com/v1/devices"

    def __init__(self, ip, mac=None, api_key=None, model=None):
        super().__init__(ip, mac)
        self.api_key = api_key
        self.device_model = model or "Generic"
        self.device_id = mac # Govee uses MAC as device ID

    def _get_headers(self):
        return {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def toggle(self, state: bool):
        if not self.api_key or not self.device_id: return
        payload = {
            "device": self.device_id,
            "model": self.device_model,
            "cmd": {
                "name": "turn",
                "value": "on" if state else "off"
            }
        }
        res = requests.put(f"{self.API_URL}/control", headers=self._get_headers(), json=payload)
        return res.json()

    def get_status(self):
        if not self.api_key: return {"status": "No API Key"}
        res = requests.get(self.API_URL, headers=self._get_headers())
        return res.json()

    def set_brightness(self, level: int):
        if not self.api_key or not self.device_id: return
        payload = {
            "device": self.device_id,
            "model": self.device_model,
            "cmd": {
                "name": "brightness",
                "value": level # Govee uses 0-100 usually
            }
        }
        res = requests.put(f"{self.API_URL}/control", headers=self._get_headers(), json=payload)
        return res.json()
