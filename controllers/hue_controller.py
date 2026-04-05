from phue import Bridge
from .base_controller import BaseController
import logging

class HueController(BaseController):
    def __init__(self, ip, mac=None, username=None):
        super().__init__(ip, mac)
        self.username = username
        self.bridge = None
        self._connect()

    def _connect(self):
        try:
            self.bridge = Bridge(self.ip, username=self.username)
            # If username is None, this will prompt for button press on first run
            self.bridge.connect()
            print(f"[Hue] Connected to bridge at {self.ip}")
        except Exception as e:
            print(f"[Hue] Connection failed: {e}")

    def toggle(self, state: bool):
        if not self.bridge: return
        lights = self.bridge.get_light_objects()
        for light in lights:
            light.on = state

    def get_status(self):
        if not self.bridge: return {"status": "Disconnected"}
        return self.bridge.get_api()

    def set_brightness(self, level: int):
        if not self.bridge: return
        # Hue uses 0-254
        hue_level = int((level / 100) * 254)
        lights = self.bridge.get_light_objects()
        for light in lights:
            light.brightness = hue_level
