import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def detect_ui_elements(image_path: str):
    """
    Detect UI elements such as icons and buttons using contour and edge detection.

    Args:
      image_path: Path to the screenshot image file.

    Returns:
      A list of dictionaries representing detected UI elements with keys:
      'type', 'coordinates', 'bbox', 'area', 'aspect_ratio'
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image for detect_ui_elements: {image_path}")
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elements = []

        # Threshold and find contours for UI components
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 500 < area < 20000:  # Filter by size
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / h if h > 0 else 0

                if 0.8 <= aspect_ratio <= 1.2 and 1000 <= area <= 5000:
                    element_type = "icon"
                elif 2.0 <= aspect_ratio <= 10.0 and 1000 <= area <= 10000:
                    element_type = "button"
                else:
                    element_type = "unknown"

                elements.append({
                    'type': element_type,
                    'coordinates': (x + w // 2, y + h // 2),
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio
                })

        # Also apply edge detection for clickable areas
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(cnt)
                elements.append({
                    'type': 'clickable',
                    'coordinates': (x + w // 2, y + h // 2),
                    'bbox': (x, y, w, h),
                    'area': area
                })

        return elements

    except Exception as e:
        logger.error(f"UI element detection error: {e}")
        return []
