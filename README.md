# 🏛️ HomeMinister

A central hub for managing your smart home devices, featuring a premium dark-themed dashboard and a robust discovery engine that identifies **Amazon Echo, Philips Hue, Govee, Lefant, CamHi, and Eufy** devices.

## ✨ Features

- **Multi-Protocol Discovery**: Combined mDNS (Bonjour), SSDP (UPnP), and ARP subnet sweeping.
- **Smart Fingerprinting**: Identifies brands and device types using MAC OUI and protocol headers.
- **Device Persistence**: Saves discovered devices to `devices.json` so you never lose track of your hardware.
- **Unified Dashboard**: Real-time scan progress and interactive device cards with glassmorphism styling.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Run HomeMinister

```bash
python3 main.py
```

### 3. Access the Dashboard

Open **[http://localhost:5001](http://localhost:5001)** in your browser.

---

## 📂 Project Structure

- `app.py`: Flask backend with REST API and static file routing.
- `scanner/`:
  - `mdns.py`: Bonjour/mDNS service discovery.
  - `ssdp.py`: UPnP/SSDP device discovery.
  - `arp.py`: Subnet host discovery via ping and ARP cache.
  - `fingerprint.py`: Brand identification logic.
- `static/`:
  - `index.html`: Main dashboard structure.
  - `style.css`: Premium dark glassmorphism styling.
  - `app.js`: Frontend logic and real-time polling.

## 🛠 Troubleshooting

- **No devices found?** Ensure your computer is on the same Wi-Fi/subnet as your smart devices. Check the terminal logs for `[DEBUG] Scanning from IP: ...` to verify the correct interface is being used.
- **Port Conflict?** The app runs on port `5001` by default to avoid conflicts with macOS AirPlay (which often uses `5000`).
