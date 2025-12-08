import subprocess
import shutil
from typing import Dict, Any
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class SyncService:
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Returns NTP/Chrony sync status.
        """
        if settings.IS_PI and not settings.DEV_MODE:
            try:
                # Run chronyc tracking
                # output example: "Last offset : +0.000012345 seconds"
                cmd = shutil.which("chronyc")
                if not cmd:
                    return {"offset_ms": 0, "status": "no_chrony"}
                
                result = subprocess.run([cmd, "tracking"], capture_output=True, text=True, timeout=1)
                for line in result.stdout.splitlines():
                    if "Last offset" in line:
                         # "+0.000012345 seconds"
                         parts = line.split(":")
                         if len(parts) > 1:
                             val_str = parts[1].strip().split(" ")[0]
                             offset_ms = float(val_str) * 1000.0
                             return {"offset_ms": round(offset_ms, 3), "status": "synced"}
                return {"offset_ms": 0, "status": "unknown"}
            except Exception as e:
                logger.error(f"Sync check failed: {e}")
                return {"offset_ms": 0, "status": "error"}
        else:
            # Mock sync
            return {"offset_ms": 0.02, "status": "mock_synced"}

sync_monitor = SyncService()
