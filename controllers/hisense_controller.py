from .base_controller import BaseController
from wakeonlan import send_magic_packet

class HisenseController(BaseController):
    def __init__(self, ip, mac=None):
        super().__init__(ip, mac)

    def toggle(self, state: bool):
        if state and self.mac:
            send_magic_packet(self.mac)
            return True
        return False

    def get_status(self):
        return {
            "is_on": False, 
            "brand": "Hisense", 
            "mac": self.mac, 
            "error": "Full state unsupported"
        }
        
    def set_brightness(self, level: int):
        pass
