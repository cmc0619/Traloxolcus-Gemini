import asyncio
import logging
import subprocess
from ..config import settings

logger = logging.getLogger(__name__)

class BluetoothService:
    def __init__(self):
        self.current_alias = "SoccerCam"

    async def set_beacon_name(self, status: str):
        """
        Updates the Bluetooth Alias to reflect system status.
        E.g. "CamL-MESH" or "CamL-HOME-ERR".
        Visible to any phone scanning for BLE devices.
        """
        node_id = settings.NODE_ID.replace("soccer-cam-", "").replace("CAM_", "")
        alias = f"{node_id}-{status}"
        
        if alias == self.current_alias:
            return

        logger.info(f"Setting Bluetooth Beacon Name: {alias}")
        
        if settings.IS_PI and not settings.DEV_MODE:
            try:
                # Use bluetoothctl to set alias
                # echo "system-alias <name>" | bluetoothctl
                cmd = f"echo \"system-alias {alias}\" | bluetoothctl"
                
                # Also reset advertising to ensure name update propagates
                # echo "advertise off" | bluetoothctl
                # echo "advertise on" | bluetoothctl
                # (Active advertising might be needed)
                
                proc = await asyncio.create_subprocess_shell(cmd)
                await proc.wait()
                
                # Make discoverable
                cmd_disc = "echo \"discoverable on\" | bluetoothctl"
                await (await asyncio.create_subprocess_shell(cmd_disc)).wait()
                
                self.current_alias = alias
            except Exception as e:
                logger.error(f"Bluetooth beacon failed: {e}")
        else:
            logger.info(f"[Mock] Bluetooth Name set to: {alias}")

bluetooth_service = BluetoothService()
