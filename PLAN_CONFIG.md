# Implementation Plan - Dynamic Configuration via GUI

## Goal

Allow the operator to change system settings (Bitrate, Resolution, Node ID, WiFi) directly from the Web UI, replacing the hardcoded `config.py`.

## Proposed Changes

### Backend (`soccer_rig/`)

3. **Configuration Storage**:
   - Create `settings.json` in the app directory for persistent storage.
   - Update `config.py` (or create `services/config_manager.py`) to load from this JSON on startup.

4. **API Updates (`api/routes.py`)**:
   - `GET /config`: Return current settings.
   - `POST /config`: Update settings and save to JSON. (May require restart).

### Frontend (`static/`)

1. **Settings UI**:
   - Add a "Settings" section/tab to `index.html`.
   - Fields: Node ID, Resolution, FPS, Bitrate, WiFi Config (Simulated).
   - "Save" button to POST changes.

## Verification

- Change a setting (e.g., node ID) in UI.
- Verify persistence after restart.
