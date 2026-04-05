import asyncio
from kasa import Discover
from .base_controller import BaseController

class TPLinkController(BaseController):
    def __init__(self, ip, mac=None, username=None, password=None):
        super().__init__(ip, mac)
        self.username = username
        self.password = password

    def _run_async(self, coro):
        """Helper to run async kasa calls in our sync environment."""
        try:
            return asyncio.run(coro)
        except Exception as e:
            print(f"[TP-Link] Error: {e}")
            return None

    async def _get_device(self):
        device = await Discover.discover_single(
            self.ip, 
            username=self.username, 
            password=self.password
        )
        if device:
            await device.update()
        return device

    def toggle(self, state: bool):
        async def _toggle():
            dev = await self._get_device()
            if not dev:
                return False
            if state:
                await dev.turn_on()
            else:
                await dev.turn_off()
            return True
        
        return self._run_async(_toggle())

    def get_status(self):
        async def _status():
            dev = await self._get_device()
            if not dev:
                return {"error": "Device not found or unreachable"}
            return {
                "is_on": dev.is_on,
                "model": dev.model,
                "alias": dev.alias,
                "mac": dev.mac
            }
        
        return self._run_async(_status())

    def set_brightness(self, level: int):
        async def _dim():
            dev = await self._get_device()
            if dev and dev.is_dimmable:
                await dev.set_brightness(level)
                return True
            return False
            
        return self._run_async(_dim())
