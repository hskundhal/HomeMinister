import socket
import re

def scan_ssdp(timeout=5):
    ssdp_request = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: %d\r\n'
        'ST: ssdp:all\r\n'
        '\r\n'
    ) % timeout

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    devices = []
    try:
        sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
        
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(65535)
                response = data.decode('utf-8', errors='ignore')
                
                device = {
                    "ip": addr[0],
                    "raw_response": response,
                    "headers": {}
                }
                
                # Parse headers
                lines = response.split('\r\n')
                for line in lines[1:]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        device["headers"][key.strip().upper()] = value.strip()
                
                # Deduplicate by IP and ST/USN if possible
                if not any(d['ip'] == device['ip'] and d.get('headers', {}).get('ST') == device['headers'].get('ST') for d in devices):
                    devices.append(device)
            except socket.timeout:
                break
    finally:
        sock.close()
    
    return devices

if __name__ == "__main__":
    print("Scanning for SSDP devices...")
    devices = scan_ssdp()
    for d in devices:
        print(f"Found: {d['ip']} - {d['headers'].get('ST', 'Unknown')}")
