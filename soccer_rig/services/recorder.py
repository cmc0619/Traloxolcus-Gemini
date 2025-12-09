import os
import time
import logging
from datetime import datetime
from typing import Optional

from ..config import settings
from .camera import get_camera_service, BaseCameraService
from .manifest import manifest_service
from .audio import audio_service
from .system import system_monitor

logger = logging.getLogger(__name__)

class RecorderService:
    def __init__(self):
        self.camera: BaseCameraService = get_camera_service()
        self.is_recording = False
        self.current_session_id = None
        self.current_file_path = None
        self.start_time = None
        
    async def start_session(self, session_id: str):
        if self.is_recording:
            raise RuntimeError("Recording already in progress")

        # Pre-flight Checks
        disk = system_monitor.get_disk_usage()
        if disk["free_gb"] < 1.0: # 1GB limit
             raise RuntimeError(f"Disk full ({disk['free_gb']}GB free). Cleanup required.")
             
        batt = system_monitor.get_battery_status()
        # Battery critical check (10%)
        if batt["percent"] > 0 and batt["percent"] < 10 and not batt["charging"]:
             raise RuntimeError(f"Battery Critical ({batt['percent']}%). Connect power.")

        # Audio Sync
        await audio_service.play_beep()
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{settings.NODE_ID}_{timestamp}.mp4"
        file_path = os.path.join(settings.RECORDINGS_DIR, filename)
        
        logger.info(f"Starting session {session_id} -> {file_path}")
        
        await self.camera.start_recording(file_path)
        
        self.is_recording = True
        self.current_session_id = session_id
        self.current_file_path = file_path
        self.start_time = time.time()
        
        return {
            "session_id": session_id,
            "file": filename,
            "status": "recording",
            "start_time": self.start_time
        }

    async def run_self_test(self):
        """
        Runs a 10-second test recording.
        """
        test_id = "SELFTEST"
        try:
            # Start
            await self.start_session(test_id)
            # Wait 10s
            await asyncio.sleep(10)
            # Stop
            result = await self.stop_session()
            result["status"] = "passed"
            return result
        except Exception as e:
            logger.error(f"Self test failed: {e}")
            # Ensure stopped
            if self.is_recording:
                await self.camera.stop_recording()
                self.is_recording = False
            return {"status": "failed", "error": str(e)}

    async def stop_session(self):
        if not self.is_recording:
            return {"status": "stopped", "message": "No recording was active"}
            
        logger.info("Stopping session")
        await self.camera.stop_recording()
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        manifest_file = manifest_service.create_manifest(
            session_id=self.current_session_id,
            file_path=self.current_file_path,
            start_time_local=self.start_time,
            duration=duration
        )
        
        result = {
            "session_id": self.current_session_id,
            "file": self.current_file_path,
            "manifest": manifest_file,
            "duration": duration,
            "status": "stopped"
        }
        
        self.is_recording = False
        self.current_session_id = None
        self.current_file_path = None
        self.start_time = None
        
        return result

    async def get_status(self):
        return {
            "is_recording": self.is_recording,
            "session_id": self.current_session_id,
            "duration": (time.time() - self.start_time) if self.is_recording else 0,
            "file": os.path.basename(self.current_file_path) if self.current_file_path else None
        }

    async def take_snapshot(self) -> str:
        """
        Takes a snapshot.
        """
        filename = f"snap_{int(time.time())}.jpg"
        filepath = os.path.join(settings.BASE_DIR, "soccer_rig/static", filename) 
        
        await self.camera.capture_snapshot(filepath)
        return filename

recorder = RecorderService()
