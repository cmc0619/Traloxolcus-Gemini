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

async function loadConfig() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        const data = await res.json();
        els.confNodeId.value = data.node_id;
        els.confWidth.value = data.width;
        els.confHeight.value = data.height;
        els.confFps.value = data.fps;
        els.confBitrate.value = data.bitrate;
    } catch (e) {
        console.error("Config load failed", e);
    }
}

async function saveConfig() {
    const payload = {
        node_id: els.confNodeId.value,
        width: parseInt(els.confWidth.value),
        height: parseInt(els.confHeight.value),
        fps: parseInt(els.confFps.value),
        bitrate: parseInt(els.confBitrate.value)
    };
    try {
        const res = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert("Settings saved!");
            updateStatus(); // Refresh node ID in header
        } else {
            alert("Failed to save settings");
        }
    } catch (e) {
        alert("Error saving settings");
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
els.btnReboot.onclick = () => doSystemAction('reboot');
els.btnShutdown.onclick = () => doSystemAction('shutdown');

// Init
loadConfig();
loadNetwork();
setInterval(updateStatus, 2000);
updateStatus();
updateFileList();
