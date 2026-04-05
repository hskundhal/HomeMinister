from .base_controller import BaseController
from samsungtvws import SamsungTVWS
from wakeonlan import send_magic_packet

class SamsungController(BaseController):
    def __init__(self, ip, mac=None):
        super().__init__(ip, mac)

    def toggle(self, state: bool):
        try:
            if state:
                if self.mac:
                    send_magic_packet(self.mac)
                return True
            else:
                tv = SamsungTVWS(self.ip)
                tv.shortcuts().power()
                return True
        except Exception as e:
            print(f"[Samsung] Toggle error: {e}")
            return False

    def get_status(self):
        try:
            tv = SamsungTVWS(self.ip)
            return {"is_on": True, "brand": "Samsung", "mac": self.mac}
        except Exception:
            return {"is_on": False, "brand": "Samsung", "mac": self.mac}
            
    def set_brightness(self, level: int):
        pass
