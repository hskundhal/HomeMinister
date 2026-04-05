import socket
import time

def scan_camhi(timeout=3):
    """
    Discover CamHi/HiSilicon cameras using UDP broadcast on port 10000.
    Standard HiSearch protocol.
    """
    print("[CamHi] Discovering cameras...")
    # Discovery packet for HiSearch
    # This is a common hex string used for searching HiSilicon based cameras
    search_packet = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00"
    
    results = []
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
                # Parse response - very basic for now, just identifying the IP
                # Real parser would extract MAC and Model from the binary data
                results.append({
                    "ip": addr[0],
                    "mac": None, # Will be filled by ARP merge
                    "brand": "CamHi",
                    "type": "IP Camera",
                    "name": f"CamHi Camera ({addr[0]})",
                    "confidence": 0.9,
                    "source": "camhi_udp"
                })
            except socket.timeout:
                break
    except Exception as e:
        print(f"[CamHi] Discovery error: {e}")
    finally:
        sock.close()
        
    print(f"[CamHi] Found {len(results)} devices")
    return results
