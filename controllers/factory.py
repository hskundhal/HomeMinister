from .hue_controller import HueController
from .govee_controller import GoveeController
from .eufy_security_controller import EufySecurityController
from .eufy_robovac_controller import EufyRoboVacController
from .tplink_controller import TPLinkController
from .camhi_controller import CamHiController
from .samsung_controller import SamsungController
from .lg_controller import LGController
from .hisense_controller import HisenseController

def get_controller(device_info, config=None):
    brand = device_info.get('brand', '').lower()
    ip = device_info.get('ip')
    mac = device_info.get('mac')
    
    if "hue" in brand:
        return HueController(ip, mac, username=config.get('hue_username'))
    elif "govee" in brand:
        return GoveeController(
            ip, mac, 
            api_key=config.get('govee_api_key'),
            model=device_info.get('model')
        )
    elif "tp-link" in brand or "kasa" in brand or "tapo" in brand:
        return TPLinkController(
            ip, mac, 
            username=config.get('tplink_username'),
            password=config.get('tplink_password')
        )
    elif "camhi" in brand:
        return CamHiController(
            ip, mac, 
            username=config.get('camhi_username'), 
            password=config.get('camhi_password')
        )
    elif "samsung" in brand:
        return SamsungController(ip, mac)
    elif "lg" in brand:
        return LGController(ip, mac)
    elif "hisense" in brand:
        return HisenseController(ip, mac)
    elif "eufy" in brand:
        # Check if it's a vacuum or a camera based on type/name
        device_type = device_info.get('type', '').lower()
        if "vacuum" in device_type or "robovac" in device_type:
            return EufyRoboVacController(
                ip, mac, 
                device_id=config.get('eufy_robovac_id'), 
                local_key=config.get('eufy_robovac_key')
            )
        else:
            return EufySecurityController(
                ip, mac, 
                email=config.get('eufy_email'), 
                password=config.get('eufy_password')
            )
    
    return None
