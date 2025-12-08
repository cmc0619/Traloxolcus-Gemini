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
    btnSaveConf: document.getElementById('btn-save-conf')
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

// Init
loadConfig();
setInterval(updateStatus, 2000);
updateStatus();
updateFileList();
