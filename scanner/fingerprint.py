import json

# Pre-defined MAC OUI prefixes for identification
MANUFACTURERS = {
    "b4:e6:2d": "Amazon (Echo)",
    "00:17:88": "Philips Hue",
    "fc:65:de": "Govee",
    "60:01:94": "Espressif (Common in Govee/Cheap Smart Devices)",
    "d4:d2:d6": "Lefant",
    "00:0e:53": "CamHi",
    "b4:cf:33": "Eufy",
    "8c:85:80": "Eufy",
    "50:c7:bf": "TP-Link",
    "60:a4:4c": "TP-Link",
    "cc:32:e5": "TP-Link",
    "00:31:92": "TP-Link"
}

def identify_device(ip, mac, mdns_devices, ssdp_devices):
    brand = "Unknown"
    device_type = "Generic Device"
    confidence = 0.5
    
    # Check MAC OUI
    if mac:
        oui = mac[:8].lower()
        if oui in MANUFACTURERS:
            brand = MANUFACTURERS[oui]
            confidence = 0.8

    # Check mDNS
    for mdns in mdns_devices:
        if ip in mdns['ips']:
            if "hue" in mdns['type'].lower() or "hue" in mdns['name'].lower():
                brand = "Philips Hue"
                device_type = "Lighting Bridge"
                confidence = 1.0
            elif "alexa" in mdns['type'].lower() or "amzn" in mdns['name'].lower():
                brand = "Amazon"
                device_type = "Voice Assistant"
                confidence = 1.0
            elif "googlecast" in mdns['type'].lower():
                brand = "Google Nest"
                device_type = "Smart Speaker/TV"
                confidence = 1.0
            elif "eufy" in mdns['name'].lower():
                brand = "Eufy"
                device_type = "Security Camera/Vac"
                confidence = 1.0
            elif "samsung" in mdns['name'].lower() or "_samsung_tv._tcp" in mdns['type'].lower():
                brand = "Samsung"
                device_type = "TV"
                confidence = 1.0
            elif "lg" in mdns['name'].lower() or "webos" in mdns['name'].lower() or "_lg-smart-device" in mdns['type'].lower() or "_viziocast" in mdns['type'].lower():
                brand = "LG"
                device_type = "TV"
                confidence = 1.0
            elif "hisense" in mdns['name'].lower() or "_hisensetv._tcp" in mdns['type'].lower():
                brand = "Hisense"
                device_type = "TV"
                confidence = 1.0

    # Check SSDP
    for ssdp in ssdp_devices:
        if ssdp['ip'] == ip:
            headers = ssdp.get('headers', {})
            server = headers.get('SERVER', '').lower()
            st = headers.get('ST', '').lower()
            
            if "philips" in server or "hue" in st:
                brand = "Philips Hue"
                device_type = "Lighting Bridge"
                confidence = 1.0
            elif "alexa" in server or "echo" in server:
                brand = "Amazon Alexa"
                device_type = "Voice Assistant"
                confidence = 1.0
            elif "camhi" in server:
                brand = "CamHi"
                device_type = "IP Camera"
                confidence = 0.9
            elif "samsung" in server or "tizen" in server or "samsung" in st:
                brand = "Samsung"
                device_type = "TV"
                confidence = 1.0
            elif "webos" in server or "lg" in server:
                brand = "LG"
                device_type = "TV"
                confidence = 1.0
            elif "hisense" in server or "hisense" in st:
                brand = "Hisense"
                device_type = "TV"
                confidence = 1.0

    return {
        "ip": ip,
        "mac": mac,
        "brand": brand,
        "type": device_type,
        "confidence": confidence
    }

def merge_results(arp_devs, mdns_devs, ssdp_devs, tplink_devs=[], camhi_devs=[]):
    """Merge and deduplicate results from all scanning sources."""
    # Build a base map from ARP (all active IPs on local subnet)
    device_map = {}
    for arp in arp_devs:
        ip = arp['ip']
        # Initialize with identification from ARP (MAC OUI, etc.)
        device_map[ip] = identify_device(ip, arp['mac'], mdns_devs, ssdp_devs)
    
    # Update with mDNS info (in case some were not in ARP or need specific merge)
    for md in mdns_devs:
        for ip in md['ips']:
            info = identify_device(ip, None, [md], [])
            if ip in device_map:
                if info['confidence'] >= device_map[ip]['confidence']:
                    device_map[ip].update(info)
            else:
                device_map[ip] = info
            
    # Update with SSDP info
    for sd in ssdp_devs:
        ip = sd['ip']
        info = identify_device(ip, None, [], [sd])
        if ip in device_map:
            if info['confidence'] >= device_map[ip]['confidence']:
                device_map[ip].update(info)
        else:
            device_map[ip] = info

    # Update with TP-Link info
    for td in tplink_devs:
        ip = td['ip']
        if ip in device_map:
            device_map[ip].update(td)
        else:
            device_map[ip] = td

    # Update with CamHi info
    for cd in camhi_devs:
        ip = cd['ip']
        if ip in device_map:
            device_map[ip].update(cd)
        else:
            device_map[ip] = cd
            
    return list(device_map.values())
