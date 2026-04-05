from flask import Flask, jsonify, request, send_from_directory, Response
import threading
import uuid
import time
import json
import os
from scanner.mdns import scan_mdns
from scanner.ssdp import scan_ssdp
from scanner.arp import scan_arp
from scanner.tplink_scanner import scan_tplink
from scanner.camhi_scanner import scan_camhi
from scanner.fingerprint import merge_results
from scanner.govee_cloud import fetch_govee_devices
from controllers.factory import get_controller

app = Flask(__name__, static_folder='static', static_url_path='')

# Paths for persistent storage
DEVICES_FILE = 'devices.json'
CONFIG_FILE = 'config.json'
scans = {}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_devices(devices):
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices, f, indent=4)

def run_background_scan(scan_id):
    try:
        print(f"[SCAN {scan_id}] Starting full house sweep...")
        config = load_config()
        
        scans[scan_id]["status"] = "Scanning mDNS (5s)..."
        mdns_results = scan_mdns(timeout=5)
        
        scans[scan_id]["status"] = "Scanning SSDP..."
        ssdp_results = scan_ssdp(timeout=5)
        
        # 3. Scanning ARP (Subnet sweep) as fallback
        scans[scan_id]["status"] = "Scanning ARP (Subnet)..."
        arp_results = scan_arp()
        arp_ips = [d['ip'] for d in arp_results]
        
        # 2.5 TP-Link UDP Discovery
        scans[scan_id]["status"] = "Scanning TP-Link..."
        tplink_results = scan_tplink(
            timeout=5, 
            arp_ips=arp_ips,
            username=config.get('tplink_username'),
            password=config.get('tplink_password')
        )
        
        # 2.7 CamHi UDP Discovery
        scans[scan_id]["status"] = "Scanning CamHi..."
        camhi_results = scan_camhi(timeout=5)
        
        # 3.5 Cloud Discovery (Govee)
        govee_results = []
        if config.get("govee_api_key"):
            scans[scan_id]["status"] = "Syncing Govee Cloud..."
            govee_results = fetch_govee_devices(config["govee_api_key"])
        
        scans[scan_id]["status"] = "Identifying and Merging..."
        final_devices = merge_results(arp_results, mdns_results, ssdp_results, tplink_results, camhi_results)
        
        # Merge cloud devices (prioritize MAC matching)
        device_map = {d.get('mac') or d['ip']: d for d in final_devices}
        for gd in govee_results:
            mac = gd.get('mac')
            if mac in device_map:
                # Update local device with cloud info (name, etc.)
                device_map[mac].update({
                    "brand": gd["brand"],
                    "name": gd["name"],
                    "model": gd["model"],
                    "source": "local+cloud"
                })
            else:
                # Add as new cloud-only device
                device_map[mac] = gd
                
        final_combined = list(device_map.values())
        
        # Merge with existing persistent devices
        existing_devices = load_devices()
        persisted_map = {d.get('mac') or d['ip']: d for d in existing_devices}
        for d in final_combined:
            persisted_map[d.get('mac') or d['ip']] = d
        
        updated_list = list(persisted_map.values())
        save_devices(updated_list)
        
        print(f"[SCAN {scan_id}] Final device count: {len(updated_list)}")
        scans[scan_id]["results"] = updated_list
        scans[scan_id]["status"] = "Completed"
        print(f"[SCAN {scan_id}] SCAN COMPLETED SUCCESSFULLY")
    except Exception as e:
        print(f"[SCAN {scan_id}] THREAD CRASHED: {e}")
        scans[scan_id]["status"] = f"Error: {str(e)}"


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    scan_id = str(uuid.uuid4())
    scans[scan_id] = {
        "id": scan_id,
        "status": "Starting",
        "results": [],
        "timestamp": time.time()
    }
    
    thread = threading.Thread(target=run_background_scan, args=(scan_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"scan_id": scan_id})

@app.route('/api/scan/<scan_id>/status')
def scan_status(scan_id):
    if scan_id not in scans:
        return jsonify({"error": "Scan not found"}), 404
    
    return jsonify({
        "status": scans[scan_id]["status"],
        "is_complete": scans[scan_id]["status"] == "Completed",
        "device_count": len(scans[scan_id]["results"])
    })

@app.route('/api/devices')
def get_devices():
    return jsonify(load_devices())

@app.route('/api/control', methods=['POST'])
def control_device():
    data = request.json
    device_ip = data.get('ip')
    command = data.get('command') # 'on', 'off', 'brightness'
    value = data.get('value')
    
    # 1. Find device info in persistence
    devices = load_devices()
    matching_devices = [d for d in devices if d.get('ip') == device_ip]
    
    if not matching_devices:
        return jsonify({"error": "Device not found"}), 404
        
    # Prioritize devices with known brands, otherwise fallback to the first match
    device = next((d for d in matching_devices if d.get('brand', '').lower() != 'unknown'), matching_devices[0])
        
    # 2. Get controller and config
    config = load_config()
    controller = get_controller(device, config)
    
    if not controller:
        return jsonify({"error": f"No controller for {device.get('brand')}"}), 400
        
    # 3. Action
    try:
        if command == 'on':
            controller.toggle(True)
        elif command == 'off':
            controller.toggle(False)
        elif command == 'brightness':
            controller.set_brightness(int(value))
        else:
            return jsonify({"error": "Unknown command"}), 400
            
        return jsonify({"status": "Success", "device": device['ip'], "command": command})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/device/<ip>/status')
def device_status(ip):
    print(f"[API] Status request for {ip}")
    devices = load_devices()
    matching_devices = [d for d in devices if d.get('ip') == ip]
    
    if not matching_devices:
        print(f"[API] Device {ip} not found in persistence")
        return jsonify({"error": "Device not found"}), 404
        
    device = next((d for d in matching_devices if d.get('brand', '').lower() != 'unknown'), matching_devices[0])
        
    config = load_config()
    controller = get_controller(device, config)
    if not controller:
        print(f"[API] No controller for device {ip}")
        return jsonify({"error": "No controller"}), 400
    
    status = controller.get_status()
    print(f"[API] Returning status for {ip}")
    return jsonify(status)

if __name__ == '__main__':
    # HomeMinister runs on 5001 to avoid AirPlay conflict
    app.run(host='0.0.0.0', port=5001, debug=True)
