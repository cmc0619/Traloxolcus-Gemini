import logging
import time
from .ingest import run_ingest
from .stitcher import run_stitcher
from .analysis import run_analysis

# Setup common logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Workflow")

def run_workflow():
    """
    Main entry point for the Soccer Bench Processing Station.
    """
    start_time = time.time()
    
    logger.info("=== STEP 1: INGEST ===")
    try:
        run_ingest()
    except Exception as e:
        logger.error(f"Ingest failed: {e}. Continue? Yes, for existing files.")

    logger.info("=== STEP 2: STITCH ===")
    try:
        run_stitcher()
    except Exception as e:
        logger.error(f"Stitching failed: {e}")

    logger.info("=== STEP 3: ANALYZE ===")
    try:
        run_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        
    logger.info("=== STEP 4: UPLOAD (Pending) ===")
    logger.info("Upload skipped (Platform not ready).")

    duration = time.time() - start_time
    logger.info(f"Workflow Complete in {duration:.2f} seconds.")

if __name__ == "__main__":
    run_workflow()
