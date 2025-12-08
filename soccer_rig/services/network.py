import subprocess
import logging
import asyncio
from typing import Dict

from ..config import settings

logger = logging.getLogger(__name__)

class NetworkService:
    def __init__(self):
        self.ap_mode_active = False

    async def get_status(self) -> Dict[str, str]:
        """
        Get current network status (SSID, IP).
        """
        if settings.IS_PI and not settings.DEV_MODE:
             # Run nmcli -t -f active,ssid dev wifi
             # This is a bit complex to parse reliably without a library, 
             # but we'll try a simple check.
             try:
                 # Check current connection
                 cmd = "nmcli -t -f NAME connection show --active"
                 proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                 stdout, _ = await proc.communicate()
                 ssid = stdout.decode().strip()
                 
                 # Check IP
                 cmd_ip = "hostname -I"
                 proc_ip = await asyncio.create_subprocess_shell(cmd_ip, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                 stdout_ip, _ = await proc_ip.communicate()
                 ip = stdout_ip.decode().strip().split(" ")[0]
                 
                 return {"ssid": ssid, "ip": ip, "ap_mode": self.ap_mode_active}
             except Exception as e:
                 logger.error(f"Network check failed: {e}")
                 return {"ssid": "error", "ip": "0.0.0.0", "ap_mode": self.ap_mode_active}
        else:
            return {"ssid": "MOCK_WIFI", "ip": "192.168.1.10", "ap_mode": self.ap_mode_active}

    async def enable_ap_mode(self):
        """
        Switch to Access Point mode.
        """
        logger.info("Switching to AP Mode...")
        if settings.IS_PI and not settings.DEV_MODE:
            # Command to bring up Hotspot connection
            # Assuming a connection named 'Hotspot' is pre-configured or created here.
            # strict implementation of creating one:
            # nmcli con add type wifi ifname wlan0 con-name Hotspot autoconnect yes ssid SOCCER_CAM_X
            # nmcli con modify Hotspot 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
            # nmcli con up Hotspot
            try:
                cmd = f"nmcli con up Hotspot"
                proc = await asyncio.create_subprocess_shell(cmd)
                await proc.wait()
                self.ap_mode_active = True
                return True
            except Exception as e:
                logger.error(f"Failed to switch to AP: {e}")
                return False
        else:
            self.ap_mode_active = True
            logger.info("Mock AP Mode Enabled")
            return True

network_service = NetworkService()
