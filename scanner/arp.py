import os
import subprocess
import re
import socket
import netifaces
from concurrent.futures import ThreadPoolExecutor

def get_local_subnet():
    try:
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
        
        # Priority 1: Use default gateway interface
        if default_gateway:
            interface = default_gateway[1]
            print(f"[DEBUG] Default gateway interface: {interface}")
        else:
            # Priority 2: Look for common physical interfaces (en0, en1)
            interfaces = netifaces.interfaces()
            interface = next((i for i in ['en0', 'en1', 'wlan0', 'eth0'] if i in interfaces), None)
            if not interface:
                interface = interfaces[0]
            print(f"[DEBUG] No default gateway, fallback interface: {interface}")

        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET not in addrs:
            # Try to find any interface with a valid IPv4 that isn't loopback
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    addr_info = addrs[netifaces.AF_INET][0]
                    if not addr_info['addr'].startswith('127.'):
                        interface = iface
                        print(f"[DEBUG] Found IP on interface: {interface}")
                        break
            
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET not in addrs:
                return None
        
        ip_info = addrs[netifaces.AF_INET][0]
        ip = ip_info['addr']
        mask = ip_info['netmask']
        print(f"[DEBUG] Scanning from IP: {ip} with mask: {mask}")
        
        # Simple way to get /24 subnet
        parts = ip.split('.')
        subnet = ".".join(parts[:3]) + "."
        return subnet
    except Exception as e:
        print(f"[ERROR] Subnet detection failed: {e}")
        return None

def ping_host(ip):
    try:
        # -t 1 for timeout 1 sec, -c 1 for 1 packet
        subprocess.run(['ping', '-c', '1', '-t', '1', ip], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
    except:
        pass

def scan_arp():
    subnet = get_local_subnet()
    if not subnet:
        return []
    
    print(f"Scanning subnet {subnet}0/24...")
    
    # Ping all 254 hosts to populate ARP cache
    with ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(1, 255):
            executor.submit(ping_host, f"{subnet}{i}")
    
    # Read ARP cache
    devices = []
    try:
        output = subprocess.check_output(['arp', '-an']).decode('utf-8')
        # Format: ? (192.168.1.1) at 00:00:00:00:00:00 on en0 ifscope [ethernet]
        pattern = r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-fA-F:]+)"
        matches = re.finditer(pattern, output)
        
        for match in matches:
            ip = match.group(1)
            mac = match.group(2).lower()
            if mac != "ff:ff:ff:ff:ff:ff" and mac != "incomplete":
                devices.append({"ip": ip, "mac": mac})
    except Exception as e:
        print(f"Error reading ARP cache: {e}")
        
    return devices

if __name__ == "__main__":
    devices = scan_arp()
    for d in devices:
        print(f"Found: {d['ip']} [{d['mac']}]")
