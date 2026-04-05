from .base_controller import BaseController
from bscpylgtv import WebOsClient
from wakeonlan import send_magic_packet
import asyncio

class LGController(BaseController):
    def __init__(self, ip, mac=None):
        super().__init__(ip, mac)

    def _run_async(self, coro):
        try:
            return asyncio.run(coro)
        except Exception as e:
            print(f"[LG] Error: {e}")
            return None

    def toggle(self, state: bool):
        async def _toggle():
            try:
                if state:
                    if self.mac:
                        send_magic_packet(self.mac)
                    return True
                else:
                    client = await WebOsClient.create(
                        self.ip, 
                        timeout_connect=5, 
                        connect_retry_attempts=150, 
                        connect_retry_interval_ms=200,
                        states=[]
                    )
                    await client.connect()
                    await client.power_off()
                    await client.disconnect()
                    return True
            except Exception as e:
                print(f"[LG] Toggle error: {e}")
                return False
        return self._run_async(_toggle())

    def get_status(self):
        async def _status():
            try:
                client = await WebOsClient.create(
                    self.ip, 
                    ping_timeout=2,
                    states=[]
                )
                await client.connect()
                await client.disconnect()
                return {"is_on": True, "brand": "LG", "mac": self.mac}
            except Exception:
                return {"is_on": False, "brand": "LG", "mac": self.mac}
        return self._run_async(_status())
        
    def set_brightness(self, level: int):
        pass
