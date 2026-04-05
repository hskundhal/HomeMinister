const state = {
    scanId: null,
    isScanning: false,
    startTime: null,
    devices: [],
    timerInterval: null
};

const dom = {
    scanBtn: document.getElementById('scan-btn'),
    statusText: document.getElementById('status-text'),
    progressBar: document.getElementById('progress-bar'),
    deviceCount: document.getElementById('device-count'),
    scanTime: document.getElementById('scan-time'),
    deviceGrid: document.getElementById('device-grid'),
    cardTemplate: document.getElementById('device-card-template')
};

const BRAND_ICONS = {
    "Amazon": "🏠",
    "Philips Hue": "💡",
    "Govee": "✨",
    "Lefant": "🧹",
    "CamHi": "📹",
    "Eufy": "🛡️",
    "Google Nest": "🔉",
    "Unknown": "❓"
};

function startTimer() {
    state.startTime = Date.now();
    state.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
        dom.scanTime.textContent = `${elapsed}s`;
    }, 1000);
}

function stopTimer() {
    clearInterval(state.timerInterval);
}

async function startScan() {
    if (state.isScanning) return;

    // Reset UI
    state.isScanning = true;
    state.devices = [];
    dom.deviceGrid.innerHTML = '';
    dom.deviceCount.textContent = '0';
    dom.scanBtn.classList.add('loading');
    dom.progressBar.style.width = '10%';
    
    startTimer();

    try {
        const response = await fetch('/api/scan', { method: 'POST' });
        const data = await response.json();
        state.scanId = data.scan_id;
        
        pollStatus();
    } catch (err) {
        console.error("Failed to start scan", err);
        dom.statusText.textContent = "Error starting scan. Please try again.";
        state.isScanning = false;
        dom.scanBtn.classList.remove('loading');
        stopTimer();
    }
}

async function pollStatus() {
    if (!state.scanId) return;

    try {
        const response = await fetch(`/api/scan/${state.scanId}/status`);
        const data = await response.json();

        dom.statusText.textContent = data.status;
        
        // Progress emulation based on status
        if (data.status.includes('mDNS')) dom.progressBar.style.width = '30%';
        if (data.status.includes('SSDP')) dom.progressBar.style.width = '50%';
        if (data.status.includes('ARP')) dom.progressBar.style.width = '80%';

        if (data.is_complete) {
            dom.progressBar.style.width = '100%';
            dom.statusText.textContent = "Scan complete!";
            fetchResults();
            return;
        }

        // Poll every 1s
        setTimeout(pollStatus, 1000);
    } catch (err) {
        console.error("Polling error", err);
    }
}

async function fetchResults() {
    try {
        // Fetch the global persistent list instead of the transient scan results
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        state.devices = data;
        renderDevices();
        
        state.isScanning = false;
        dom.scanBtn.classList.remove('loading');
        stopTimer();
    } catch (err) {
        console.error("Failed to fetch results", err);
    }
}

async function controlDevice(ip, command, btn) {
    if (btn) {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = "...";
        btn.disabled = true;
    }
    try {
        const response = await fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, command })
        });
        const data = await response.json();
        console.log("Control result:", data);
        if (btn) {
            btn.style.backgroundColor = data.error ? '#ff4d4d' : '#4dff4d';
            setTimeout(() => btn.style.backgroundColor = '', 1000);
        }
        return data;
    } catch (err) {
        console.error("Control failed", err);
        if (btn) {
            btn.style.backgroundColor = '#ff4d4d';
            setTimeout(() => btn.style.backgroundColor = '', 1000);
        }
    } finally {
        if (btn) {
            btn.textContent = btn.dataset.originalText;
            btn.disabled = false;
        }
    }
}

async function getDeviceStatus(ip) {
    try {
        const response = await fetch(`/api/device/${ip}/status`);
        return await response.json();
    } catch (err) {
        console.error("Status fetch failed", err);
    }
}

function renderDevices() {
    dom.deviceCount.textContent = state.devices.length;
    dom.deviceGrid.innerHTML = '';

    state.devices.forEach((device, index) => {
        const clone = dom.cardTemplate.content.cloneNode(true);
        const card = clone.querySelector('.device-card');
        
        // Stagger entrance animation
        card.style.animationDelay = `${index * 0.1}s`;

        const brandStr = device.brand !== "Unknown" ? device.brand : "Generic";
        clone.querySelector('.device-brand').textContent = device.name || brandStr;
        clone.querySelector('.device-type').textContent = `${brandStr} ${device.type || ''}`.trim();
        clone.querySelector('.ip').textContent = device.ip;
        clone.querySelector('.mac').textContent = device.mac || '??:??:??:??';
        clone.querySelector('.confidence-badge').textContent = `${Math.round(device.confidence * 100)}%`;
        
        // Find icon based on actual brand, since device.brand might be capitalized differently or generic
        const normalizedBrand = Object.keys(BRAND_ICONS).find(k => k.toLowerCase() === (device.brand || "").toLowerCase()) || "Unknown";
        const icon = BRAND_ICONS[normalizedBrand] || BRAND_ICONS["Unknown"];
        if (device.brand.includes("Amazon")) clone.querySelector('.device-brand-icon').textContent = BRAND_ICONS["Amazon"];
        else if (device.brand.includes("Philips")) clone.querySelector('.device-brand-icon').textContent = BRAND_ICONS["Philips Hue"];
        else clone.querySelector('.device-brand-icon').textContent = icon;

        // Show/Hide control buttons
        const b = device.brand.toLowerCase();
        const t = (device.type || "").toLowerCase();
        const n = (device.name || "").toLowerCase();
        
        console.log(`Rendering device: ${device.ip} | Brand: ${b} | Type: ${t}`);

        if (b.includes("hue") || b.includes("govee") || b.includes("eufy") || b.includes("camhi") || b.includes("tp-link") || b.includes("kasa")) {
            const actions = card.querySelector('.control-actions');
            actions.style.display = 'flex';
            card.querySelector('.btn-control.on').onclick = (e) => controlDevice(device.ip, 'on', e.target);
            card.querySelector('.btn-control.off').onclick = (e) => controlDevice(device.ip, 'off', e.target);
            
            // If it's a camera or Eufy device, show the VIEW button
            if (t.includes("camera") || t.includes("doorbell") || b.includes("camhi") || b.includes("eufy") || n.includes("camera")) {
                const viewBtn = card.querySelector('.view-btn');
                viewBtn.style.display = 'block';
                viewBtn.onclick = async () => {
                    const preview = card.querySelector('.camera-preview');
                    console.log(`View requested for ${device.ip}`);
                    if (preview.style.display === 'none') {
                        const status = await getDeviceStatus(device.ip);
                        console.log(`Status for ${device.ip}:`, status);
                        if (status && status.length > 0 && (status[0].thumbnail || status.thumbnail)) {
                            const thumb = status[0].thumbnail || status.thumbnail;
                            preview.querySelector('img').src = thumb;
                            preview.style.display = 'block';
                        } else {
                            alert("Could not load camera preview. Check if Eufy account has a recent snapshot.");
                        }
                    } else {
                        preview.style.display = 'none';
                    }
                };
            }
        }

        dom.deviceGrid.appendChild(clone);
    });
}

async function fetchDevices() {
    try {
        const response = await fetch('/api/devices');
        const devices = await response.json();
        if (devices.length > 0) {
            state.devices = devices;
            renderDevices();
            dom.statusText.textContent = `Loaded ${devices.length} saved devices.`;
        }
    } catch (err) {
        console.error("Failed to load saved devices", err);
    }
}

dom.scanBtn.addEventListener('click', startScan);
document.addEventListener('DOMContentLoaded', () => {
    dom.statusText.textContent = "Click the button to scan your local network.";
    fetchDevices();
});
