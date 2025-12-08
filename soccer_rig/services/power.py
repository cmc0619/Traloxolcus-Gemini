import asyncio
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class PowerService:
    async def shutdown(self):
        logger.warning("Initiating System Shutdown...")
        if settings.IS_PI and not settings.DEV_MODE:
            cmd = "sudo shutdown -h now"
            await asyncio.create_subprocess_shell(cmd)
        else:
            logger.info("Mock Shutdown executed")

    async def reboot(self):
        logger.warning("Initiating System Reboot...")
        if settings.IS_PI and not settings.DEV_MODE:
            cmd = "sudo reboot"
            await asyncio.create_subprocess_shell(cmd)
        else:
            logger.info("Mock Reboot executed")

power_service = PowerService()
