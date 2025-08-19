import pyautogui
import os
import time
import logging

logger = logging.getLogger(__name__)

def take_screenshot(save_dir, filename=None):
    try:
        os.makedirs(save_dir, exist_ok=True)
        if filename is None:
            filename = f"screen_{int(time.time())}.png"
        # Clean filename of spaces and special chars
        import re
        filename = re.sub(r'[^a-zA-Z0-9_.\-]', '_', filename)
        path = os.path.join(save_dir, filename)
        img = pyautogui.screenshot()
        img.save(path)
        time.sleep(0.05)
        if os.path.exists(path):
            logger.info(f"Screenshot saved at {path}")
            return path
        logger.error(f"Screenshot not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return None


# mobile ui

import os
import time

def take_mobile_screenshot(save_dir, filename=None, adb_path='adb'):
    os.makedirs(save_dir, exist_ok=True)
    if filename is None:
        filename = f"mobile_screen_{int(time.time())}.png"
    local_path = os.path.join(save_dir, filename)
    device_temp_path = f"/sdcard/{filename}"
    # Capture screenshot on device
    os.system(f"{adb_path} shell screencap -p {device_temp_path}")
    # Pull screenshot to local
    os.system(f"{adb_path} pull {device_temp_path} {local_path}")
    # Optionally remove device screenshot
    os.system(f"{adb_path} shell rm {device_temp_path}")
    return local_path
