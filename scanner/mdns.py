from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import socket
import logging

class MDNSListener(ServiceListener):
    def __init__(self):
        self.discovered_devices = []

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        pass

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            device = {
                "name": name,
                "type": type_,
                "ips": addresses,
                "port": info.port,
                "properties": {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in info.properties.items()}
            }
            self.discovered_devices.append(device)

def scan_mdns(timeout=5):
    zeroconf = Zeroconf()
    listener = MDNSListener()
    
    # Common smart home service types
    services = [
        "_hue._tcp.local.",
        "_amzn-alexa._tcp.local.",
        "_amzn-wplay._tcp.local.",
        "_googlecast._tcp.local.",
        "_eufysecurity._tcp.local.",
        "_http._tcp.local.",
        "_ipp._tcp.local.",
        "_printer._tcp.local.",
        "_spotify-connect._tcp.local."
    ]
    
    browsers = [ServiceBrowser(zeroconf, s, listener) for s in services]
    
    import time
    time.sleep(timeout)
    
    zeroconf.close()
    return listener.discovered_devices

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Scanning for mDNS services...")
    devices = scan_mdns()
    for d in devices:
        print(f"Found: {d['name']} at {d['ips']}")
