import requests
import logging
import os
from typing import Dict, Any

from ..config import settings

logger = logging.getLogger(__name__)

class UpdaterService:
    GITHUB_REPO = "user/soccer_rig" # Placeholder
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Query GitHub for latest release.
        Uses Tag Name for version comparison.
        """
        try:
            # url = f"https://api.github.com/repos/{self.GITHUB_REPO}/releases/latest"
            # res = requests.get(url, timeout=5)
            # data = res.json()
            # latest_tag = data["tag_name"] # e.g. "v1.2.1"
            
            # Mocking response
            latest_tag = "v1.3.0" 
            current_version = f"v{settings.VERSION}" if not settings.VERSION.startswith("v") else settings.VERSION
            
            # Simple Semver Logic (Remove 'v')
            def parse_ver(v_str):
                return [int(x) for x in v_str.lstrip("v").split(".")]

            try:
                is_newer = parse_ver(latest_tag) > parse_ver(current_version)
            except:
                # Fallback
                is_newer = latest_tag != current_version

            return {
                "current_version": current_version,
                "latest_version": latest_tag,
                "update_available": is_newer,
                "release_url": f"https://github.com/{self.GITHUB_REPO}/releases/tag/{latest_tag}"
            }
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return {"error": str(e)}

    async def apply_update(self, version: str):
        """
        Download and apply update.
        """
        logger.info(f"Applying update to version {version}")
        # Real impl:
        # 1. Download tarball
        # 2. Extract
        # 3. Stop services
        # 4. Swap files
        # 5. Restart services
        
        # Mock impl:
        if settings.DEV_MODE:
            logger.info("Mock update applied.")
            return True
            
        return False

updater_service = UpdaterService()
