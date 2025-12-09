const API_BASE = "/api/v1";

const els = {
    nodeId: document.getElementById('node-id'),
    recStatus: document.getElementById('rec-status'),
    timeOffset: document.getElementById('time-offset'),
    storageFree: document.getElementById('storage-free'),
    battery: document.getElementById('battery-level'),
    btnRecord: document.getElementById('btn-record'),
    btnStop: document.getElementById('btn-stop'),
    btnSnap: document.getElementById('btn-snapshot'),
    sessionIdInput: document.getElementById('session-id'),
    preview: document.getElementById('cam-preview'),
    fileList: document.getElementById('file-list'),
    // Config
    confNodeId: document.getElementById('conf-node-id'),
    confWidth: document.getElementById('conf-width'),
    confHeight: document.getElementById('conf-height'),
    confFps: document.getElementById('conf-fps'),
    confBitrate: document.getElementById('conf-bitrate'),
    btnSaveConf: document.getElementById('btn-save-conf'),
    // System
    btnReboot: document.getElementById('btn-reboot'),
    btnShutdown: document.getElementById('btn-shutdown'),
    netSsid: document.getElementById('net-ssid')
};

// JS Logic for Rig UI
// Removed unused element references
// Updated Config Save to only send Node ID
// Added Mesh Status Polling for CAM_C

async function loadConfig() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        const data = await res.json();
        if (els.confNodeId) els.confNodeId.value = data.node_id;

        // Show Mesh Panel if CAM_C
        if (data.node_id === "CAM_C") {
            document.getElementById('mesh-panel').style.display = 'block';
            startMeshPolling();
        }
    } catch (e) {
        console.error("Config load failed", e);
    }
}

async function saveConfig() {
    // Only Node ID is user-configurable now.
    // Quality is hardcoded Max.
    const payload = {
        node_id: els.confNodeId.value,
        width: 3840,
        height: 2160,
        fps: 30,
        bitrate: 40000000
    };
    try {
        const res = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert("Role saved! Rebooting...");
            doSystemAction('reboot');
        } else {
            alert("Failed to save settings");
        }
    } catch (e) {
        alert("Error saving settings");
    }
}

let meshInterval = null;
function startMeshPolling() {
    if (meshInterval) clearInterval(meshInterval);
    updateMeshStatus();
    meshInterval = setInterval(updateMeshStatus, 5000);
}

async function updateMeshStatus() {
    try {
        const res = await fetch(`${API_BASE}/system/mesh`);
        const peers = await res.json();
        const grid = document.getElementById('mesh-grid');
        grid.innerHTML = '';

        if (Object.keys(peers).length === 0) {
            grid.innerHTML = '<p>No peers detected.</p>';
            return;
        }

        for (const [id, status] of Object.entries(peers)) {
            const color = status.online ? '#10b981' : '#ef4444';
            const text = status.online ?
                `REC: ${status.recorder?.is_recording} | BAT: ${status.battery_percent}%` :
                `ERROR: ${status.error}`;

            const item = document.createElement('div');
            item.style.border = `1px solid ${color}`;
            item.style.padding = '10px';
            item.style.borderRadius = '4px';
            item.style.marginBottom = '5px';
            item.innerHTML = `<strong>${id}</strong> <span style="color:${color}">●</span><br><small>${text}</small>`;
            grid.appendChild(item);
        }
    } catch (e) {
        console.error("Mesh status failed", e);
    }
}

async function updateStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();

        els.nodeId.textContent = data.node_id;

        const isRec = data.recorder.is_recording;
        els.recStatus.textContent = isRec ? `Recording (${Math.round(data.recorder.duration)}s)` : "Idle";
        if (isRec) {
            els.recStatus.style.color = "var(--danger)";
            els.btnRecord.disabled = true;
            els.btnStop.disabled = false;
        } else {
            els.recStatus.style.color = "var(--success)";
            els.btnRecord.disabled = false;
            els.btnStop.disabled = true;
        }

        els.storageFree.textContent = `${data.disk_free_gb} GB`;
        els.battery.textContent = `${data.battery_percent}%`;
        els.timeOffset.textContent = `${data.sync_offset_ms}ms`;

    } catch (e) {
        console.error("Status fetch failed", e);
    }

    // Net status (lightweight check, ideally separate poll)
    // For now we assume status endpoint might carry it or we fetch once.
    // Let's lazy load net status.
}

async function doSystemAction(action) {
    if (!confirm(`Are you sure you want to ${action}?`)) return;
    try {
        await fetch(`${API_BASE}/system/${action}`, { method: 'POST' });
        alert(`${action} initiated.`);
    } catch (e) {
        alert("Action failed");
    }
}

async function loadNetwork() {
    try {
        const res = await fetch(`${API_BASE}/system/network`);
        const data = await res.json();
        els.netSsid.textContent = data.ssid || "No WiFi";
    } catch { els.netSsid.textContent = "Net Error"; }
}

async function startRecording() {
    const sessionId = els.sessionIdInput.value || "session_default";
    try {
        const res = await fetch(`${API_BASE}/record/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        if (!res.ok) alert("Failed to start");
        updateStatus();
    } catch (e) {
        alert("Error starting recording");
    }
}

async function stopRecording() {
    try {
        await fetch(`${API_BASE}/record/stop`, { method: 'POST' });
        updateStatus();
        updateFileList();
    } catch (e) {
        alert("Error stopping recording");
    }
}

async function switchUplink() {
    const ssid = document.getElementById('net-uplink-ssid').value;
    const psk = document.getElementById('net-uplink-psk').value;

    if (!ssid || !psk) {
        alert("Enter SSID and Password");
        return;
    }

    if (!confirm(`Switch ENTIRE RIG to Wi-Fi '${ssid}'? connection will be lost!`)) return;

    try {
        await fetch(`${API_BASE}/system/network/uplink`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ssid: ssid, psk: psk })
        });
        alert("Command sent! Nodes are switching...");
    } catch (e) {
        alert("Error sending uplink command");
    }
}

async function takeSnapshot() {
    try {
        const res = await fetch(`${API_BASE}/snapshot`, { method: 'POST' });
        const data = await res.json();
        // Add timestamp to bust cache
        els.preview.src = `${data.url}?t=${Date.now()}`;
        els.preview.style.display = 'block';
    } catch (e) {
        alert("Snapshot failed");
    }
}

async function updateFileList() {
    try {
        const res = await fetch(`${API_BASE}/recordings`);
        const data = await res.json();
        els.fileList.innerHTML = data.files.map(f => `<li>${f}</li>`).join('');
    } catch (e) {
        els.fileList.innerHTML = "<li>Error loading files</li>";
    }
}

// Event Listeners
els.btnRecord.onclick = startRecording;
els.btnStop.onclick = stopRecording;
els.btnSnap.onclick = takeSnapshot;
els.btnSaveConf.onclick = saveConfig;

async function doPowerAction(scope, action) {
    try {
        await fetch(`${API_BASE}/system/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scope: scope })
        });
        alert(`${action} initiated (${scope})`);
    } catch (e) { alert("Failed"); }
}

els.btnReboot.onclick = function () {
    if (confirm("Reboot ENTIRE FLEET? (Cancel for Local only)")) {
        doPowerAction('fleet', 'reboot');
    } else {
        if (confirm("Reboot THIS NODE only?")) doPowerAction('local', 'reboot');
    }
};

els.btnShutdown.onclick = function () {
    if (confirm("Shutdown ENTIRE FLEET? (Cancel for Local only)")) {
        doPowerAction('fleet', 'shutdown');
    } else {
        if (confirm("Shutdown THIS NODE only?")) doPowerAction('local', 'shutdown');
    }
};
document.getElementById('btn-uplink').onclick = switchUplink;

// Init
loadConfig();
loadNetwork();
setInterval(updateStatus, 2000);
updateStatus();
updateFileList();
