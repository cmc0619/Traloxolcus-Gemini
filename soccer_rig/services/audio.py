import asyncio
import logging
import os
from ..config import settings

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        # Ensure we have a beep sound file? 
        # For simplicity, we can generate one or assume it exists.
        # Or use `speaker-test` for a tone if no file.
        pass

    async def play_beep(self, pattern: str = "default"):
        """
        Plays notification sounds.
        Patterns:
        - default/sync: 1 beep (1kHz, 0.5s)
        - success: 3 short beeps
        - switching: 2 medium beeps
        - error: 1 long beep (2s)
        """
        logger.info(f"Playing Audio: {pattern}")
        
        cmd = ""
        if pattern == "success":
             # 3 beeps: 800Hz
             cmd = "speaker-test -t sine -f 800 -l 3 -s 1 > /dev/null 2>&1"
        elif pattern == "switching":
             # 2 beeps
             cmd = "speaker-test -t sine -f 600 -l 2 -s 1 > /dev/null 2>&1"
        elif pattern == "error":
             # Long low beep
             cmd = "speaker-test -t sine -f 200 -l 1 -s 1 > /dev/null 2>&1" # How to stretch duration? speaker-test is limited.
             # Alternatively, call it multiple times for "error" feel.
        else:
             cmd = "speaker-test -t sine -f 1000 -l 1 -s 1 > /dev/null 2>&1"

        if settings.IS_PI and not settings.DEV_MODE:
            try:
                # Fire and forget or wait? Better wait to not overlap.
                proc = await asyncio.create_subprocess_shell(cmd)
                await proc.wait()
            except Exception as e:
                logger.error(f"Audio failed: {e}")
        else:
            # Windows/Mock beep
            if settings.IS_WINDOWS:
                import winsound
                try:
                    freq = 1000
                    dur = 200
                    if pattern == "success": 
                        winsound.Beep(800, 100); winsound.Beep(800, 100); winsound.Beep(800, 100)
                    elif pattern == "error":
                        winsound.Beep(200, 1000)
                    else:
                        winsound.Beep(freq, dur)
                except:
                    pass
            logger.info(f"Mock Beep ({pattern}) Played")

audio_service = AudioService()
