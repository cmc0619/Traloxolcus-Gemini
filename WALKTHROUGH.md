# Walkthrough - Multi-Camera Pi 5 Soccer Recording System

I have successfully implemented the software stack for the 3-camera recording system.

## Features Implemented

- **Core Recorder**: Wraps `libcamera-vid` (or mocks it on non-Pi) for 4K30 recording.
- **Web Dashboard**: Mobile-friendly UI to control recording, view status, and framing.
- **Dynamic Settings**: Configure Resolution, FPS, Bitrate, and ID via GUI.
- **Data Management**: Automatic manifest generation, offload confirmation, and cleanup.
- **System Monitoring**: Tracks Disk Space, Temperature, Battery, and NTP Sync.
- **Updater**: Checks GitHub Releases for updates.

## Verification

I ran an end-to-end test script (`test_e2e.py`) and config test (`test_config.py`).

### Results

- **Status API**: Correctly reports mock hardware stats and "Idle" state.
- **Recording**: Successfully started a session `test_session_01`.
- **Config**: Verified settings are saved to `settings.json` and persist.
- **Offload**: Successfully marked file as offloaded via API.

### How to Run

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Start Server**:

   ```bash
   # Run with auto-reload for dev
   python -m uvicorn soccer_rig.main:app --host 0.0.0.0 --port 8000
   ```

3. **Access UI**:
   Open `http://<IP>:8000` on your phone or laptop.
   - Go to "Settings" card to configure Node ID.

## Configuration

- Default settings are loaded on first run.
- Modify them in the Web UI.
- Values are stored in `settings.json`.
