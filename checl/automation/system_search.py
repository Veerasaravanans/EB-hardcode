import pyautogui
import time
import logging

logger = logging.getLogger(__name__)

def open_system_search(system_name, shortcuts):
    try:
        if system_name not in shortcuts:
            logger.error(f"No shortcut defined for system {system_name}")
            return False

        shortcut = shortcuts[system_name]
        if isinstance(shortcut, list):
            pyautogui.hotkey(*shortcut)
        else:
            pyautogui.press(shortcut)

        time.sleep(1)
        logger.info(f"Opened system search for {system_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to open system search: {e}")
        return False
