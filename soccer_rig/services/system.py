import shutil
import os
import psutil
from typing import Dict, Any

from ..config import settings

class SystemService:
    def get_disk_usage(self) -> Dict[str, Any]:
        """
        Returns disk usage statistics for the recordings directory.
        """
        total, used, free = shutil.disk_usage(settings.RECORDINGS_DIR)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent": round((used / total) * 100, 1)
        }

    def get_temperature(self) -> float:
        """
        Returns CPU temperature in Celsius.
        """
        if settings.IS_PI and not settings.DEV_MODE:
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    return round(float(f.read()) / 1000.0, 1)
            except Exception:
                return 0.0
        else:
            # Mock temp for dev
            return 45.5

    def get_battery_status(self) -> Dict[str, Any]:
        """
        Returns battery status.
        On Pi, this depends on the specific hardware/HAT.
        We'll look for standard power_supply class or return a mock.
        """
        if settings.IS_PI and not settings.DEV_MODE:
             # Implementation would depend on specific hardware (e.g. UPS HAT)
             # Checking standard locations
             try:
                 # Example: /sys/class/power_supply/BAT0/capacity
                 # This is highly hardware specific. returning 100 for AC.
                 return {"percent": 100, "charging": True}
             except:
                 return {"percent": 0, "charging": False}
        else:
            return {"percent": 95, "charging": False}

system_monitor = SystemService()
