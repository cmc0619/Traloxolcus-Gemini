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
            logger.info("Mock AP Mode Enabled")
            return True

            logger.info(f"Mock: Connected to {ssid}")
            await audio_service.play_beep(pattern="success")
            return True

    async def connect_to_wifi(self, ssid: str, psk: str):
        """
        Connect to a specific Wi-Fi network (Client Mode).
        Uses nmcli to create/up a connection.
        Includes SAFEGUARD: If connection fails after 30s, revert to Hotspot.
        """
        from .audio import audio_service # Local import to avoid circular dependency if any
        
        logger.info(f"Connecting to Wi-Fi: {ssid}...")
        await audio_service.play_beep(pattern="switching") # Beep 1
        
        if settings.IS_PI and not settings.DEV_MODE:
            try:
                # 1. Delete existing 'HomeWifi' connection if any
                await asyncio.create_subprocess_shell("nmcli con delete HomeWifi")
                
                # 2. Add new connection
                cmd_add = f"nmcli con add type wifi ifname wlan0 con-name HomeWifi ssid \"{ssid}\""
                await (await asyncio.create_subprocess_shell(cmd_add)).wait()
                
                cmd_sec = f"nmcli con modify HomeWifi wifi-sec.key-mgmt wpa-psk wifi-sec.psk \"{psk}\""
                await (await asyncio.create_subprocess_shell(cmd_sec)).wait()
                
                # 3. Up with Timeout
                cmd_up = "nmcli con up HomeWifi"
                logger.info("Bringing up connection...")
                
                # Wait up to 30 seconds
                try:
                     proc = await asyncio.wait_for(asyncio.create_subprocess_shell(cmd_up), timeout=30.0)
                     await proc.wait()
                     
                     if proc.returncode == 0:
                         logger.info("Connection Success!")
                         await audio_service.play_beep(pattern="success") # Triple Beep
                         self.ap_mode_active = False
                         return True
                     else:
                         logger.error("nmcli failed to connect.")
                         raise Exception("nmcli exit code non-zero")
                
                except (asyncio.TimeoutError, Exception) as e:
                     logger.error(f"Connection Failed ({e}). REVERTING TO AP MODE...")
                     await audio_service.play_beep(pattern="error") # Long Beep
                     await self.enable_ap_mode()
                     return False
                     
            except Exception as e:
                logger.error(f"Failed to connect to WiFi: {e}")
                await self.enable_ap_mode()
                return False
        else:
            logger.info(f"Mock: Connected to {ssid}")
            await audio_service.play_beep(pattern="success")
            return True

network_service = NetworkService()
