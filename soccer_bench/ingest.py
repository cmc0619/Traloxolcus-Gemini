import os
import requests
import hashlib
import time
import logging
from tqdm import tqdm
from .config import settings

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IngestAgent")

class IngestService:
    def __init__(self):
        self.status = "idle" # idle, scanning, downloading
        self.current_node = None
        self.current_file = None
        self.progress = 0
        self.total_bytes = 0
        self.downloaded_bytes = 0
        
    def get_status(self):
        return {
            "status": self.status,
            "node": self.current_node,
            "file": self.current_file,
            "progress": self.progress
        }

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def calculate_checksum(self, file_path, algo="sha256", chunk_size=4096):
        """Calculates SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def download_file(self, url, dest_path):
        """Downloads a file with progress tracking."""
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                self.total_bytes = total_size
                self.downloaded_bytes = 0
                
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        self.downloaded_bytes += size
                        if total_size > 0:
                            self.progress = int((self.downloaded_bytes / total_size) * 100)
                            
            return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path) # Cleanup partial
            return False

    def process_node(self, base_url, target_dir):
        """Syncs recordings from a single node."""
        node_name = base_url.replace("http://", "").replace(":8000", "")
        self.current_node = node_name
        logger.info(f"Checking node: {node_name} ({base_url})")

        try:
            # Get List
            try:
                resp = requests.get(f"{base_url}/api/v1/recordings", timeout=3)
            except requests.exceptions.RequestException:
                return # Skip offline node silently-ish

            if resp.status_code != 200:
                logger.warning(f"Node {node_name} unreachable or error: {resp.status_code}")
                return

            files = resp.json().get("files", [])
            manifests = [f for f in files if f.endswith(".json")]
            
            if not manifests:
                return

            logger.info(f"Found {len(manifests)} sessions on {node_name}")

            for man_file in manifests:
                # 1. Download Manifest
                man_url = f"{base_url}/static/{man_file}"
                local_man_path = os.path.join(target_dir, man_file)
                
                if not os.path.exists(local_man_path):
                    self.status = "downloading_manifest"
                    self.current_file = man_file
                    self.progress = 0
                    
                    logger.info(f"Downloading manifest: {man_file}")
                    if not self.download_file(man_url, local_man_path):
                        continue

                # 2. Parse Manifest
                import json
                try:
                    with open(local_man_path, 'r') as f:
                        data = json.load(f)
                        
                    video_file = data.get("file")
                    expected_checksum = data.get("checksum", {})
                    session_id = data.get("session_id")
                    camera_id = data.get("camera_id")
                    
                    # Check if already offloaded
                    if data.get("offloaded", False):
                         # logger.info(f"Skipping {man_file} (Already Marked Offloaded)")
                         continue

                except Exception as e:
                    logger.error(f"Failed to parse manifest {local_man_path}: {e}")
                    continue

                # 3. Download Video
                video_url = f"{base_url}/static/{video_file}"
                local_video_path = os.path.join(target_dir, video_file)
                
                if not os.path.exists(local_video_path):
                    self.status = "downloading_video"
                    self.current_file = video_file
                    self.progress = 0
                    
                    logger.info(f"Downloading video: {video_file}")
                    if not self.download_file(video_url, local_video_path):
                        continue
                else:
                    pass # Already exists

                # 4. Verify Checksum
                if settings.VERIFY_CHECKSUMS and expected_checksum:
                    self.status = "verifying"
                    logger.info(f"Verifying checksum for {video_file}...")
                    algo = expected_checksum.get("algo", "sha256")
                    ref_val = expected_checksum.get("value")
                    
                    calc_val = self.calculate_checksum(local_video_path, algo)
                    if calc_val != ref_val:
                        logger.error(f"CHECKSUM MISMATCH for {video_file}!")
                        os.rename(local_video_path, local_video_path + ".bad")
                        continue

                # 5. Confirm Offload
                self.status = "confirming"
                logger.info(f"Confirming offload to {node_name}...")
                confirm_payload = {
                    "session_id": session_id,
                    "camera_id": camera_id,
                    "file": video_file,
                    "checksum": expected_checksum
                }
                try:
                    requests.post(f"{base_url}/api/v1/recordings/confirm", json=confirm_payload)
                except Exception as e:
                     logger.error(f"Error calling confirm endpoint: {e}")

        except Exception as e:
            logger.error(f"Error accessing node {node_name}: {e}")
        finally:
            self.current_node = None
            self.current_file = None
            self.status = "scanning"

    def running_loop(self):
        logger.info("Starting Ingest Loop...")
        self.ensure_dir(settings.RAW_STORAGE_DIR)
        
        while True:
            self.status = "scanning"
            for node in settings.NODES:
                self.progress = 0
                self.process_node(node, settings.RAW_STORAGE_DIR)
            
            self.status = "idle"
            time.sleep(10) # Wait 10s before next scan

ingest_service = IngestService()

