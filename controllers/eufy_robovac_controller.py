import tinytuya
from .base_controller import BaseController

class EufyRoboVacController(BaseController):
    def __init__(self, ip, mac=None, device_id=None, local_key=None):
        super().__init__(ip, mac)
        self.device_id = device_id
        self.local_key = local_key
        self.device = None
        if self.device_id and self.local_key:
            self.device = tinytuya.OutletDevice(self.device_id, self.ip, self.local_key)
            self.device.set_version(3.3) # Eufy usually uses 3.3

    def toggle(self, state: bool):
        if not self.device: return
        if state:
            # Command 1 is usually the power/clean command for Tuya vacuums
            self.device.turn_on()
        else:
            self.device.turn_off()

    def get_status(self):
        if not self.device: return {"status": "Missing Keys"}
        return self.device.status()

    def set_brightness(self, level: int):
        # Vacuums don't have brightness, maybe suction power?
        pass
