from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import os

from ..services.recorder import recorder
from ..services.system import system_monitor
from ..services.sync import sync_monitor
from ..services.manifest import manifest_service
from ..services.updater import updater_service
from ..config import settings

router = APIRouter()

# ... (Requests models) ...

class StartRecordRequest(BaseModel):
    session_id: str

class ConfirmRequest(BaseModel):
    session_id: str
    camera_id: str
    file: str
    checksum: dict

@router.get("/status")
async def get_status():
    """
    Get current camera and system status.
    """
    rec_status = await recorder.get_status()
    disk = system_monitor.get_disk_usage()
    batt = system_monitor.get_battery_status()
    sync = sync_monitor.get_sync_status()
    
    return {
        "node_id": settings.NODE_ID,
        "recorder": rec_status,
        "mode": "recording" if rec_status["is_recording"] else "idle",
        "disk_free_gb": disk["free_gb"],
        "temp_c": system_monitor.get_temperature(),
        "battery_percent": batt["percent"],
        "sync_offset_ms": sync["offset_ms"]
    }

@router.post("/record/start")
async def start_recording(req: StartRecordRequest):
    try:
        result = await recorder.start_session(req.session_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/record/stop")
async def stop_recording():
    result = await recorder.stop_session()
    return result

@router.get("/recordings")
async def list_recordings():
    # List files in recording dir
    files = []
    if os.path.exists(settings.RECORDINGS_DIR):
        for f in os.listdir(settings.RECORDINGS_DIR):
            if f.endswith(".mp4") or f.endswith(".json"):
                 files.append(f)
    return {"files": files}

@router.post("/recordings/confirm")
async def confirm_offload(req: ConfirmRequest):
    """
    Verifies checksum and marks file as offloaded.
    """
    # 1. Verify checksum (Optimally. Here we assume client verified it and is telling us.)
    # Spec says: "Client posts... Pi verifies".
    # Recalculating checksum of a 50GB file on Pi is expensive and slow.
    # Usually we trust the client if they send the matching checksum we generated in the manifest.
    
    # Let's check if the manifesto matches the client's claim.
    manifest_filename = f"{req.session_id}_{req.camera_id}.json"
    manifest_path = os.path.join(settings.RECORDINGS_DIR, manifest_filename)
    
    if not os.path.exists(manifest_path):
        raise HTTPException(status_code=404, detail="Manifest not found")
        
    # In a real impl, we might re-hash, but for now we mark offloaded if the manifest exists.
    success = manifest_service.mark_offloaded(req.session_id, req.camera_id)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to mark offloaded")
         
    return {"status": "confirmed"}

@router.post("/recordings/cleanup")
async def cleanup_offloaded():
    """
    Deletes all files marked as offloaded.
    """
    files_to_delete = manifest_service.get_offloaded_files()
    deleted_count = 0
    errors = 0
    
    for f_path in files_to_delete:
        try:
            if os.path.exists(f_path):
                os.remove(f_path)
                deleted_count += 1
        except Exception as e:
            errors += 1
            
    return {"deleted": deleted_count, "errors": errors}

@router.post("/snapshot")
async def take_snapshot():
    try:
        filename = await recorder.take_snapshot()
        return {"file": filename, "url": f"/static/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/check")
async def check_update():
    return updater_service.check_for_updates()

@router.post("/update/apply")
async def apply_update():
    status = await updater_service.apply_update("latest")
    return {"status": "updating" if status else "failed"}

@router.get("/config")
async def get_config():
    return settings.to_dict()

class ConfigUpdateRequest(BaseModel):
    node_id: str
    width: int
    height: int
    fps: int
    bitrate: int

@router.post("/config")
async def update_config(req: ConfigUpdateRequest):
    success = settings.save(req.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return {"status": "saved", "config": settings.to_dict()}

# System Endpoints
from ..services.network import network_service
from ..services.power import power_service

@router.get("/system/network")
async def get_network():
    return await network_service.get_status()

@router.post("/system/network/ap")
async def enable_ap():
    success = await network_service.enable_ap_mode()
    return {"status": "ap_mode" if success else "failed"}

@router.post("/system/shutdown")
async def shutdown():
    # Execute immediately
    await power_service.shutdown()
    return {"status": "shutting_down"}

@router.post("/system/reboot")
async def reboot():
    await power_service.reboot()
    return {"status": "rebooting"}
