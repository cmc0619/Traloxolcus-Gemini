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

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def calculate_checksum(file_path, algo="sha256", chunk_size=4096):
    """Calculates SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_file(url, dest_path):
    """Downloads a file with a progress bar."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f, tqdm(
                desc=os.path.basename(dest_path),
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    bar.update(size)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path) # Cleanup partial
        return False

def process_node(base_url, target_dir):
    """Syncs recordings from a single node."""
    node_name = base_url.replace("http://", "").replace(":8000", "")
    logger.info(f"Checking node: {node_name} ({base_url})")

    try:
        # Get List
        resp = requests.get(f"{base_url}/api/v1/recordings", timeout=3)
        if resp.status_code != 200:
            logger.warning(f"Node {node_name} unreachable or error: {resp.status_code}")
            return

        files = resp.json().get("files", [])
        manifests = [f for f in files if f.endswith(".json")]
        
        if not manifests:
            logger.info(f"No recordings found on {node_name}")
            return

        logger.info(f"Found {len(manifests)} sessions on {node_name}")

        for man_file in manifests:
            # 1. Download Manifest
            man_url = f"{base_url}/static/{man_file}"
            local_man_path = os.path.join(target_dir, man_file)
            
            if not os.path.exists(local_man_path):
                logger.info(f"Downloading manifest: {man_file}")
                if not download_file(man_url, local_man_path):
                    continue

            # 2. Parse Manifest
            # We need to know the video filename and checksum
            # For now, let's just assume sidecar .mp4 if we can't parse easily without loading json model
            # But we should parse it to get the checksum.
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
                     logger.info(f"Skipping {man_file} (Already Marked Offloaded)")
                     continue

            except Exception as e:
                logger.error(f"Failed to parse manifest {local_man_path}: {e}")
                continue

            # 3. Download Video
            video_url = f"{base_url}/static/{video_file}"
            local_video_path = os.path.join(target_dir, video_file)
            
            if not os.path.exists(local_video_path):
                logger.info(f"Downloading video: {video_file}")
                if not download_file(video_url, local_video_path):
                    continue
            else:
                logger.info(f"Video {video_file} already exists locally. Verifying...")

            # 4. Verify Checksum
            if settings.VERIFY_CHECKSUMS and expected_checksum:
                logger.info(f"Verifying checksum for {video_file}...")
                algo = expected_checksum.get("algo", "sha256")
                ref_val = expected_checksum.get("value")
                
                calc_val = calculate_checksum(local_video_path, algo)
                if calc_val != ref_val:
                    logger.error(f"CHECKSUM MISMATCH for {video_file}!")
                    logger.error(f"Expected: {ref_val}, Got: {calc_val}")
                    # Rename bad file?
                    os.rename(local_video_path, local_video_path + ".bad")
                    continue
                else:
                    logger.info("Checksum Verified OK.")

            # 5. Confirm Offload
            logger.info(f"Confirming offload to {node_name}...")
            confirm_payload = {
                "session_id": session_id,
                "camera_id": camera_id,
                "file": video_file,
                "checksum": expected_checksum
            }
            try:
                c_resp = requests.post(f"{base_url}/api/v1/recordings/confirm", json=confirm_payload)
                if c_resp.status_code == 200:
                    logger.info(f"Successfully confirmed offload for {video_file}")
                else:
                    logger.error(f"Failed to confirm offload: {c_resp.text}")
            except Exception as e:
                 logger.error(f"Error calling confirm endpoint: {e}")

    except Exception as e:
        logger.error(f"Error accessing node {node_name}: {e}")

def run_ingest():
    logger.info("Starting Ingest Process...")
    ensure_dir(settings.RAW_STORAGE_DIR)
    
    for node in settings.NODES:
        process_node(node, settings.RAW_STORAGE_DIR)
        
    logger.info("Ingest Complete.")

if __name__ == "__main__":
    run_ingest()
