import socket
import time
import json
import os

def scan_camhi(timeout=3, static_ips=None):
    """
    Discover CamHi/HiSilicon cameras using UDP broadcast on port 10000.
    Standard HiSearch protocol. Also includes static IP fallback.
    """
    print("[CamHi] Discovering cameras...")
    # Official HiSearch protocol discovery packet
    # Magic header + command ID 0x20000100 for search
    search_packet = bytes([
        0xFF, 0x00, 0x00, 0x00,  # magic
        0x00, 0x00, 0x00, 0x00,  # session id
        0x00, 0x00, 0x00, 0x00,  # seq num
        0x00, 0x00, 0x00, 0x00,  # reserved
        0x00, 0x01, 0x00, 0x20,  # cmd id: 0x20000100
    ])
    
    results = []
    found_ips = set()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        
        # Broadcast to local subnet
        sock.sendto(search_packet, ('255.255.255.255', 10000))
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                if ip not in found_ips:
                    found_ips.add(ip)
                    results.append({
                        "ip": ip,
                        "mac": None,
                        "brand": "CamHi",
                        "type": "IP Camera",
                        "name": f"CamHi Camera ({ip})",
                        "confidence": 0.9,
                        "source": "camhi_udp"
                    })
            except socket.timeout:
                break
    except Exception as e:
        print(f"[CamHi] Discovery error: {e}")
    finally:
        sock.close()
    
    # Static IP fallback for cameras that don't respond to broadcast
    for ip in (static_ips or []):
        if ip not in found_ips:
            print(f"[CamHi] Adding static camera: {ip}")
            results.append({
                "ip": ip,
                "mac": None,
                "brand": "CamHi",
                "type": "IP Camera",
                "name": f"CamHi Camera ({ip})",
                "confidence": 0.85,
                "source": "camhi_static"
            })
        
    print(f"[CamHi] Found {len(results)} devices")
    return results
