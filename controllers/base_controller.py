from abc import ABC, abstractmethod

class BaseController(ABC):
    def __init__(self, ip, mac=None):
        self.ip = ip
        self.mac = mac

    @abstractmethod
    def toggle(self, state: bool):
        """Turn device on (True) or off (False)."""
        pass

    @abstractmethod
    def get_status(self):
        """Return the current status of the device."""
        pass

    @abstractmethod
    def set_brightness(self, level: int):
        """Set brightness level (0-100 or 0-255)."""
        pass
