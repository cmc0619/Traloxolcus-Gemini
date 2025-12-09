const API_BASE = "/api";

async function updateStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();

        // --- Machine Stats ---
        document.getElementById('disk-free').textContent = `${data.disk_free_gb} GB`;

        // --- Ingest Status ---
        const ingest = data.ingest;
        const ingestStatus = document.getElementById('ingest-status');
        const ingestList = document.getElementById('ingest-list');

        ingestStatus.textContent = ingest.status.toUpperCase();
        ingestStatus.className = ingest.status === 'idle' ? 'status-badge status-idle' : 'status-badge status-active';

        if (ingest.status.startsWith('downloading')) {
            ingestList.innerHTML = `
                <div style="margin-bottom:10px">
                    <strong>${ingest.node}</strong>: ${ingest.file}
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${ingest.progress}%"></div>
                    </div>
                    <small>${ingest.progress}%</small>
                </div>
            `;
        } else if (ingest.status === 'scanning') {
            ingestList.innerHTML = `<p style="color:#94a3b8">Scanning network for Rigs...</p>`;
        } else {
            ingestList.innerHTML = `<p style="color:#64748b">No active transfers.</p>`;
        }

        // --- Pipeline Status (Stitcher + ML) ---
        const pipe = data.pipeline;
        const stitcher = pipe.stitcher;
        const ml = pipe.ml;

        // Header
        const activeCount = (stitcher.active_job ? 1 : 0) + (ml.status === 'analyzing' ? 1 : 0);
        document.getElementById('pipeline-count').textContent = activeCount > 0 ? `${activeCount} Active` : "Idle";

        const pipeList = document.getElementById('pipeline-list');
        let html = "";

        // Stitcher Card
        if (stitcher.active_job) {
            html += `
                <div style="padding:10px; background:#334155; border-radius:4px; margin-bottom:5px">
                    <div style="display:flex; justify-content:space-between">
                        <strong>Stitching</strong>
                        <span class="status-badge status-active">RUNNING</span>
                    </div>
                    <small>Session: ${stitcher.active_job}</small>
                </div>`;
        } else if (stitcher.queue_length > 0) {
            html += `<div style="padding:5px; color:#94a3b8">Stitcher Queue: ${stitcher.queue_length}</div>`;
        }

        // ML Card
        if (ml.status === 'analyzing') {
            html += `
                <div style="padding:10px; background:#1e1b4b; border-radius:4px; border:1px solid #4f46e5; margin-top:5px">
                    <div style="display:flex; justify-content:space-between">
                        <strong>ML Analysis</strong>
                        <span class="status-badge status-active">ACTIVE</span>
                    </div>
                    <small>${ml.file}</small>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${ml.progress}%"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.8em; color:#a5b4fc">
                        <span>FPS: ${ml.fps}</span>
                        <span>Players: ${ml.stats.players}</span>
                        <span>Ball: ${ml.stats.ball ? 'YES' : 'NO'}</span>
                    </div>
                </div>`;
        } else if (ml.status === 'loading_model') {
            html += `<div style="padding:10px; color:#f59e0b">Loading AI Model...</div>`;
        }

        if (html === "") html = `<p style="color:#64748b">Queue empty.</p>`;
        pipeList.innerHTML = html;

        // --- Upload Status (Injecting into Machine Card for now) ---
        const upload = data.upload;
        const machineCard = document.querySelectorAll('.card')[2];
        let uploadRow = document.getElementById('upload-row');

        // Create row if not exists
        if (!uploadRow && machineCard) {
            uploadRow = document.createElement('div');
            uploadRow.id = 'upload-row';
            uploadRow.className = 'stat-row';
            uploadRow.style.marginTop = "15px";
            uploadRow.style.borderTop = "1px solid #334155";
            uploadRow.style.paddingTop = "10px";
            uploadRow.innerHTML = `<span>Upload Queue:</span> <span id="upload-status">--</span>`;
            machineCard.appendChild(uploadRow);
        }

        if (uploadRow) {
            const upStatus = document.getElementById('upload-status');
            if (upload.status === 'uploading') {
                upStatus.textContent = `Uploading ${upload.file}...`;
                upStatus.style.color = "#f59e0b";
            } else {
                upStatus.textContent = `${upload.queue_length} Pending`;
                upStatus.style.color = "#f8fafc";
            }
        }

    } catch (e) {
        console.error("Status poll failed", e);
        const statusEl = document.getElementById('system-status');
        if (statusEl) {
            statusEl.textContent = "OFFLINE";
            statusEl.className = "status-badge status-idle";
        }
    }
}

// Poll every 1s for smoother UI
setInterval(updateStatus, 1000);
updateStatus();
