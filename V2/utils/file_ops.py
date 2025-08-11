import os
import logging

logger = logging.getLogger(__name__)

def cleanup_temp_files(temp_dir):
    try:
        for fname in os.listdir(temp_dir):
            if fname.startswith("temp_") or fname.startswith("processed_"):
                path = os.path.join(temp_dir, fname)
                os.remove(path)
        logger.info("Temporary files cleaned up.")
    except Exception as e:
        logger.error(f"Error cleaning temporary files: {e}")
