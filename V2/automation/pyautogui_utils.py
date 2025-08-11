import pyautogui
import time
import logging

logger = logging.getLogger(__name__)

def safe_click(x, y, double_click=False):
    screen_w, screen_h = pyautogui.size()
    if 0 <= x <= screen_w and 0 <= y <= screen_h:
        try:
            if double_click:
                pyautogui.doubleClick(x, y)
            else:
                pyautogui.click(x, y)
            logger.info(f"Clicked at ({x}, {y})")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Click error: {e}")
    else:
        logger.error(f"Click out of bounds ({x}, {y})")
    return False

def safe_type(text):
    try:
        pyautogui.write(text, interval=0.05)
        logger.info(f"Typed text: {text}")
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"Typing error: {e}")
        return False
