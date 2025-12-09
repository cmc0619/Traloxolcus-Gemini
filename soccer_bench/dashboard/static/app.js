const API_BASE = "/api";

async function updateStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();

        // Machine Stats
        document.getElementById('disk-free').textContent = `${data.disk_free_gb} GB`;

        // Ingest Status
        const ingestEl = document.getElementById('ingest-status');
        ingestEl.textContent = data.ingest;
        ingestEl.className = data.ingest === 'idle' ? 'status-badge status-idle' : 'status-badge status-active';

        // Mocking some visual updates for now
    } catch (e) {
        console.error("Status poll failed", e);
        document.getElementById('system-status').textContent = "OFFLINE";
        document.getElementById('system-status').className = "status-badge status-idle";
    }
}

// Poll every 2s
setInterval(updateStatus, 2000);
updateStatus();
