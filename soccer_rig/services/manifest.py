import json
import os
import hashlib
import logging
import time
from typing import Dict, Any, List

from ..config import settings
from .system import system_monitor
from .sync import sync_monitor

logger = logging.getLogger(__name__)

class ManifestService:
    def calculate_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Checksum calculation failed: {e}")
            return "error"

    def create_manifest(self, 
                        session_id: str, 
                        file_path: str, 
                        start_time_local: float, 
                        duration: float, 
                        dropped_frames: int = 0) -> str:
        
        filename = os.path.basename(file_path)
        manifest_filename = f"{session_id}_{settings.NODE_ID}.json"
        manifest_path = os.path.join(settings.RECORDINGS_DIR, manifest_filename)
        
        sync_status = sync_monitor.get_sync_status()
        
        data = {
            "session_id": session_id,
            "camera_id": settings.NODE_ID,
            "file": filename,
            "start_time_local": start_time_local,
            "start_time_master": start_time_local - (sync_status.get("offset_ms", 0)/1000.0), # Approx
            "offset_ms": sync_status.get("offset_ms", 0),
            "duration": duration,
            "resolution": f"{settings.DEFAULT_WIDTH}x{settings.DEFAULT_HEIGHT}",
            "fps": settings.DEFAULT_FPS,
            "codec": "h265",
            "dropped_frames": dropped_frames,
            "checksum": {
                "algo": "sha256",
                "value": self.calculate_checksum(file_path)
            },
            "offloaded": False,
            "software_version": settings.VERSION,
            "created_at": time.time()
        }
        
        try:
            with open(manifest_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Manifest created: {manifest_path}")
            return manifest_filename
        except Exception as e:
            logger.error(f"Failed to write manifest: {e}")
            return None

    def mark_offloaded(self, session_id: str, camera_id: str) -> bool:
        """
        Marks a session as offloaded in its manifest.
        """
        manifest_filename = f"{session_id}_{camera_id}.json"
        manifest_path = os.path.join(settings.RECORDINGS_DIR, manifest_filename)
        
        if not os.path.exists(manifest_path):
            return False
            
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
            
            data["offloaded"] = True
            
            with open(manifest_path, "w") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update manifest: {e}")
            return False

    def get_offloaded_files(self) -> List[str]:
        """
        Returns list of file paths that are marked offloaded.
        """
        offloaded_files = []
        if not os.path.exists(settings.RECORDINGS_DIR):
            return []
            
        for f in os.listdir(settings.RECORDINGS_DIR):
            if f.endswith(".json"):
                try:
                    path = os.path.join(settings.RECORDINGS_DIR, f)
                    with open(path, "r") as json_file:
                        data = json.load(json_file)
                        if data.get("offloaded"):
                            if "file" in data:
                                video_path = os.path.join(settings.RECORDINGS_DIR, data["file"])
                                offloaded_files.append(video_path)
                                offloaded_files.append(path) # Delete manifest too? Spec implies "files post-offload", usually means both.
                except:
                    continue
        return offloaded_files

manifest_service = ManifestService()
