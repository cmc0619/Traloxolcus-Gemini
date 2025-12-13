import asyncio
import subprocess
import logging
import os
from typing import Optional
from abc import ABC, abstractmethod

from ..config import settings

logger = logging.getLogger(__name__)

class BaseCameraService(ABC):
    @abstractmethod
    async def start_recording(self, file_path: str, duration: int = 0, width: int = None, height: int = None, fps: int = None, bitrate: int = None):
        pass

    @abstractmethod
    async def stop_recording(self):
        pass

    @abstractmethod
    async def capture_snapshot(self, output_path: str):
        pass
    
    @abstractmethod
    def must_stop_before_snapshot(self) -> bool:
        """Returns True if recording must be stopped to take a snapshot (resource conflict)"""
        pass

class RealCameraService(BaseCameraService):
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        
    async def start_recording(self, file_path: str, duration: int = 0, width: int = None, height: int = None, fps: int = None, bitrate: int = None):
        if self.process and self.process.poll() is None:
            logger.warning("Recording already in progress")
            return

        cmd = [
            "rpicam-vid",
            "-o", file_path,
            "--width", str(width or settings.DEFAULT_WIDTH),
            "--height", str(height or settings.DEFAULT_HEIGHT),
            "--framerate", str(fps or settings.DEFAULT_FPS),
            "--bitrate", str(bitrate or settings.DEFAULT_BITRATE),
            "--codec", "h265",
            "--nopreview",
            "--timeout", str(duration * 1000) # 0 = infinite
        ]
        
        logger.info(f"Starting recording: {' '.join(cmd)}")
        self.process = subprocess.Popen(cmd)

    async def stop_recording(self):
        if self.process:
            logger.info("Stopping recording process")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    async def capture_snapshot(self, output_path: str):
        # rpicam-jpeg conflicts with rpicam-vid if not careful. 
        # For now, we assume we might need to stop recording to snapshot if hardware is locked.
        # But commonly we want to snapshot while recording.
        # libcamera allows multiple streams, but rpicam-apps cli might be exclusive.
        # IF recording is running, we can't easily grab a frame via simple CLI call without interrupting,
        # UNLESS we used --signal to capture a frame from the running video process (if it supported it).
        # rpicam-vid doesn't natively dump stills on signal easily without specific config.
        # Workaround: For this version, snapshots are best effort or require stopping.
        # However, spec implies "Framing" which is usually pre-recording.
        
        cmd = [
            "rpicam-jpeg",
            "-o", output_path,
            "--width", "1920",
            "--height", "1080",
            "--nopreview",
            "--timeout", "1000"
        ]
        
        logger.info(f"Taking snapshot: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Snapshot command failed with exit code {proc.returncode}")

    def must_stop_before_snapshot(self) -> bool:
        # Simplistic assumption for CLI tools: yes, usually exclusive access.
        return True

class MockCameraService(BaseCameraService):
    def __init__(self):
        self._recording_task: Optional[asyncio.Task] = None
        self._is_recording = False
        
    async def start_recording(self, file_path: str, duration: int = 0, width: int = None, height: int = None, fps: int = None, bitrate: int = None):
        if self._is_recording:
            logger.warning("Mock recording already in progress")
            return
            
        logger.info(f"Starting MOCK recording to {file_path}")
        self._is_recording = True
        self._recording_task = asyncio.create_task(self._simulate_file_growth(file_path))

    async def _simulate_file_growth(self, file_path):
        try:
            with open(file_path, "wb") as f:
                while self._is_recording:
                    f.write(b"\x00" * 1024 * 1024) # 1MB per tick
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Mock recording failed: {e}")

    async def stop_recording(self):
        logger.info("Stopping MOCK recording")
        self._is_recording = False
        if self._recording_task:
            await self._recording_task
            self._recording_task = None

    async def capture_snapshot(self, output_path: str):
        logger.info(f"Taking MOCK snapshot to {output_path}")
        # Create a dummy JPEG (red square)
        # minimal jpeg header? or just text for now since browser might not display it locally well without real image.
        # Let's write text but name it .jpg, browser will fail to render but file checks pass.
        # Better: valid empty image? Nah, mock is mock.
        with open(output_path, "w") as f:
            f.write("Mock Snapshot Data")

    def must_stop_before_snapshot(self) -> bool:
        return False

def get_camera_service() -> BaseCameraService:
    if settings.IS_PI and not settings.DEV_MODE:
        return RealCameraService()
    else:
        return MockCameraService()
