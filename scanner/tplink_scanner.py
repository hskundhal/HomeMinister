import asyncio
from kasa import Discover

def scan_tplink(timeout=5, arp_ips=[], username=None, password=None):
    """Discover TP-Link Kasa/Tapo devices on the local network."""
    async def _discover():
        # 1. Try Broadcast Discovery (more efficient)
        print("[TP-Link] Starting broadcast discovery...")
        found = {}
        
        # Try both global and potential subnet broadcasts
        broadcast_targets = ["255.255.255.255"]
        if arp_ips:
            # Infer subnet broadcast from first ARP IP
            parts = arp_ips[0].split('.')
            if len(parts) == 4:
                broadcast_targets.append(".".join(parts[:3]) + ".255")
        
        for target in broadcast_targets:
            try:
                print(f"[TP-Link] Broadcasting to {target}...")
                discovered = await Discover.discover(
                    timeout=2, 
                    target=target,
                    username=username,
                    password=password
                )
                found.update(discovered)
            except Exception as e:
                print(f"[TP-Link] Broadcast to {target} failed: {e}")

        # 2. Parallel Probe Fallback (much faster than sequential)
        if not found and arp_ips:
            print(f"[TP-Link] No devices found via broadcast. Probing {len(arp_ips)} IPs in parallel...")
            
            async def probe(ip):
                try:
                    # Very short timeout for probes to keep things fast
                    dev = await Discover.discover_single(
                        ip, 
                        username=username, 
                        password=password,
                        timeout=1 
                    )
                    print(f"[TP-Link] Found device at {ip}!")
                    return ip, dev
                except Exception:
                    return None
            
            # Limit concurrency to 20 at a time to avoid socket exhaustion
            semaphore = asyncio.Semaphore(20)
            async def limited_probe(ip):
                async with semaphore:
                    return await probe(ip)

            tasks = [limited_probe(ip) for ip in arp_ips]
            probe_results = await asyncio.gather(*tasks)
            
            for res in probe_results:
                if res:
                    found[res[0]] = res[1]

        # 3. Fetch Details
        results = []
        for ip, dev in found.items():
            print(f"[TP-Link] Updating details for {ip}...")
            try:
                await dev.update()
                results.append({
                    "ip": ip,
                    "mac": dev.mac,
                    "brand": "TP-Link",
                    "type": "Switch",
                    "name": dev.alias,
                    "model": dev.model,
                    "confidence": 1.0,
                    "source": "tplink_udp"
                })
            except Exception as e:
                print(f"[TP-Link] Error updating device {ip}: {e}")
                continue
                
        print(f"[TP-Link] Found {len(results)} devices")
        return results

    try:
        # Create a new event loop for this thread if necessary
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_discover())
    except Exception as e:
        print(f"[TP-Link] Discovery error: {e}")
        return []
