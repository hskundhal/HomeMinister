import requests
import json
from .base_controller import BaseController

class EufySecurityController(BaseController):
    BASE_URL = "https://security-app.eufylife.com/v1"

    def __init__(self, ip=None, mac=None, email=None, password=None):
        super().__init__(ip, mac)
        self.email = email
        self.password = password
        self.token = None
        self.devices = []

    def _login(self):
        url = f"{self.BASE_URL}/passport/login"
        payload = {
            "email": self.email,
            "password": self.password,
            "enc": 0
        }
        res = requests.post(url, json=payload)
        data = res.json()
        if data.get("code") == 0:
            self.token = data["data"]["auth_token"]
            return True
        return False

    def _fetch_devices(self):
        if not self.token and not self._login():
            return []
        
        url = f"{self.BASE_URL}/app/get_devs_list"
        headers = {"X-Auth-Token": self.token}
        res = requests.post(url, headers=headers, json={"num": 100, "page": 0})
        data = res.json()
        if data.get("code") == 0:
            self.devices = data["data"]
            return self.devices
        return []

    def toggle(self, state: bool):
        devices = self._fetch_devices()
        # Find the device by MAC or IP if possible, or just the first one for now
        # Eufy uses SN (Serial Number)
        target = None
        for d in devices:
            if self.mac and self.mac.replace(":", "").lower() in d.get("device_sn", "").lower():
                target = d
                break
        
        if not target and devices:
            target = devices[0]
            
        if not target:
            print("[Eufy] Device not found in account")
            return

        url = f"{self.BASE_URL}/app/upload_devs_params"
        headers = {"X-Auth-Token": self.token}
        payload = {
            "device_sn": target["device_sn"],
            "station_sn": target["station_sn"],
            "params": [
                {
                    "param_type": 2001, # Power/Open
                    "param_value": "1" if state else "0"
                }
            ]
        }
        res = requests.post(url, headers=headers, json=payload)
        return res.json()

    def get_status(self):
        devices = self._fetch_devices()
        results = []
        for d in devices:
            results.append({
                "name": d.get("device_name"),
                "sn": d.get("device_sn"),
                "thumbnail": d.get("cover_path") or d.get("snapshot_path"),
                "is_online": d.get("extra", {}).get("is_online", True)
            })
        return results

    def set_brightness(self, level: int):
        # Cameras don't use brightness in the same way, maybe LED control?
        pass
