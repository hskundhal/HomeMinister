import requests
from requests.auth import HTTPBasicAuth
from .base_controller import BaseController

class CamHiController(BaseController):
    def __init__(self, ip, mac=None, username="admin", password=""):
        super().__init__(ip, mac)
        self.username = username or "admin"
        self.password = password or ""
        self.base_url = f"http://{self.ip}"

    def toggle(self, state: bool):
        # Cameras don't exactly have "toggle", maybe IR cut or alarm?
        # For now, let's treat ON as "Start Recording" and OFF as "Stop" if supported.
        pass

    def get_status(self):
        # Return snapshot URL as status
        return {
            "thumbnail": f"{self.base_url}/tmpfs/auto.jpg",
            "is_online": True # We assume if controller exists, it's online
        }

    def set_brightness(self, level: int):
        # CamHi handles brightness via CGI commands
        url = f"{self.base_url}/cgi-bin/hi3510/param.cgi?cmd=setimageattr&-brightness={level}"
        try:
            res = requests.get(url, auth=HTTPBasicAuth(self.username, self.password), timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"[CamHi] Error setting brightness: {e}")
            return False

    def ptz_move(self, direction):
        """
        Move camera: up, down, left, right, stop
        """
        commands = {
            "up": 0,
            "down": 1,
            "left": 2,
            "right": 3,
            "stop": 1
        }
        cmd_id = commands.get(direction, 1)
        url = f"{self.base_url}/cgi-bin/hi3510/ptzctrl.cgi?-step=1&-act=move&-speed=30&-command={cmd_id}"
        try:
            res = requests.get(url, auth=HTTPBasicAuth(self.username, self.password), timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"[CamHi] Error moving PTZ: {e}")
            return False
