import asyncio
import logging
import httpx
from typing import List

from ..config import settings

logger = logging.getLogger(__name__)

class MeshService:
    def __init__(self):
        # Hardcoded topology based on spec
        self.topology = {
            "CAM_L": "soccer-cam-l.local",
            "CAM_C": "soccer-cam-c.local",
            "CAM_R": "soccer-cam-r.local"
        }

    def get_peers(self) -> List[str]:
        """
        Returns a list of peer URLs based on current Node ID.
        Excludes self.
        """
        current_id = settings.NODE_ID
        peers = []
        
        for node_id, hostname in self.topology.items():
            if node_id == current_id:
                continue # Skip self
            
            # Construct peer URL
            # stored hostname or IP?
            # We assume mDNS works as per spec.
            url = f"http://{hostname}:8000/api/v1"
            peers.append(url)
            
        return peers

    async def broadcast_start(self, session_id: str):
        """
        Signal all peers to start recording.
        """
        peers = self.get_peers()
        if not peers:
            logger.info("No peers defined/detected for mesh broadcast.")
            return

        logger.info(f"Broadcasting START {session_id} to {len(peers)} peers...")
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for peer_url in peers:
                tasks.append(self._send_command(client, peer_url, "record/start", {"session_id": session_id}))
            
            await asyncio.gather(*tasks)

    async def get_mesh_status(self):
        """
        Queries all peers for their status.
        Returns: { "CAM_L": {status...}, "CAM_R": {status...} }
        """
        peers = self.get_peers()
        results = {}
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            for url in peers:
                node_id = "Unknown"
                # Infer ID from URL?
                # URL: http://soccer-cam-l.local:8000/api/v1
                if "cam-l" in url: node_id = "CAM_L"
                elif "cam-r" in url: node_id = "CAM_R"
                elif "cam-c" in url: node_id = "CAM_C"
                
                try:
                    resp = await client.get(f"{url}/status")
                    if resp.status_code == 200:
                        results[node_id] = resp.json()
                        results[node_id]["online"] = True
                    else:
                        results[node_id] = {"online": False, "error": resp.status_code}
                except Exception as e:
                    results[node_id] = {"online": False, "error": str(e)}
        return results

    async def broadcast_stop(self):
        """
        Signal all peers to stop recording.
        """
        peers = self.get_peers()
        if not peers:
            return

        logger.info(f"Broadcasting STOP to {len(peers)} peers...")
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for peer_url in peers:
                tasks.append(self._send_command(client, peer_url, "record/stop", {}))
            
            await asyncio.gather(*tasks)

    async def _send_command(self, client: httpx.AsyncClient, base_url: str, endpoint: str, json_data: dict):
        url = f"{base_url}/{endpoint}"
        try:
            # We use 'mesh_trigger'=True param or similar to prevent infinite loops 
            # if peers echo back.
            # Ideally API accepts a flag "source=mesh"
            json_data["source"] = "mesh" 
            
            await client.post(url, json=json_data)
            logger.info(f"Sent {endpoint} to {base_url} - OK")
        except Exception as e:
            logger.warning(f"Failed to signal peer {base_url}: {e}")

    async def broadcast_uplink_switch(self, ssid: str, psk: str):
        """
        Tell peers to switch to Uplink Wi-Fi.
        """
        peers = self.get_peers()
        logger.info(f"Broadcasting UPLINK SWITCH to {len(peers)} peers...")
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for peer_url in peers:
                payload = {"ssid": ssid, "psk": psk, "source": "mesh"}
                tasks.append(client.post(f"{peer_url}/system/network/uplink", json=payload))
            
            await asyncio.gather(*tasks)

    async def broadcast_shutdown(self):
        """
        Command all peers to shutdown.
        """
        peers = self.get_peers()
        logger.info(f"Broadcasting SHUTDOWN to {len(peers)} peers...")
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for peer_url in peers:
                # Assuming /system/shutdown exists on peers
                tasks.append(client.post(f"{peer_url}/system/shutdown"))
            await asyncio.gather(*tasks)

            await asyncio.gather(*tasks)

    async def broadcast_reboot(self):
        """
        Command all peers to reboot.
        """
        peers = self.get_peers()
        logger.info(f"Broadcasting REBOOT to {len(peers)} peers...")
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for peer_url in peers:
                tasks.append(client.post(f"{peer_url}/system/reboot"))
            await asyncio.gather(*tasks)

mesh_service = MeshService()
