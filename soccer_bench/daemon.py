import time
import logging
import requests
from .config import settings
from .workflow import run_workflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [DAEMON] - %(levelname)s - %(message)s')
logger = logging.getLogger("BenchDaemon")

def check_cameras():
    """
    Returns True if at least one configured camera is online.
    """
    online_count = 0
    for node_url in settings.NODES:
        try:
            # Short timeout ping
            requests.get(f"{node_url}/api/v1/status", timeout=1)
            online_count += 1
        except:
            pass
    
    return online_count > 0

def run_daemon():
    logger.info("Starting Zero-Touch Daemon. Waiting for cameras...")
    
    while True:
        try:
            if check_cameras():
                logger.info("Cameras detected! Starting Workflow...")
                # Run the workflow (Ingest -> Stitch -> Analyze -> Upload)
                run_workflow()
                
                # Wait a bit before polling again to avoid rapid loops if cameras stay online
                # (Ingest handles 'already downloaded' checks, so it's safe to re-run, 
                # but we should sleep to save cycles)
                logger.info("Workflow finished. Sleeping for 60s...")
                time.sleep(60)
            else:
                # No cameras, sleep and retry
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Stopping Daemon.")
            break
        except Exception as e:
            logger.error(f"Daemon Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_daemon()
