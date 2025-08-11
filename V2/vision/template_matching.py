import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

def template_match(screenshot_path: str, template_dir: str, template_name: str, match_threshold: float = 0.75):
    """
    Perform multi-scale template matching to find given template in the screenshot.

    Args:
        screenshot_path: Path to the screenshot image file.
        template_dir: Directory where template images are stored.
        template_name: Name of the template image file (without extension).
        match_threshold: Minimum normalized correlation threshold.

    Returns:
        A list of tuples (center_x, center_y, confidence) for matches.
    """
    template_path = os.path.join(template_dir, f"{template_name}.png")
    if not os.path.exists(template_path):
        logger.warning(f"Template image {template_path} does not exist.")
        return []

    try:
        img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

        if template is None or img is None:
            logger.error("Failed to load image or template in template_match.")
            return []

        all_matches = []
        # Multi-scale matching to handle different sizes of UI elements
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]

        for scale in scales:
            if scale != 1.0:
                w = int(template.shape[1] * scale)
                h = int(template.shape[0] * scale)
                if w < 1 or h < 1:
                    continue
                scaled_template = cv2.resize(template, (w, h))
            else:
                scaled_template = template

            res = cv2.matchTemplate(img, scaled_template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= match_threshold)

            for pt in zip(*loc[::-1]):
                center_x = pt[0] + scaled_template.shape[1] // 2
                center_y = pt[1] + scaled_template.shape[0] // 2
                confidence = res[pt[1], pt[0]]
                all_matches.append((center_x, center_y, confidence))

        # Remove duplicates by spatial proximity
        unique_matches = []
        for match in sorted(all_matches, key=lambda x: x[2], reverse=True):
            is_duplicate = False
            for um in unique_matches:
                dist = np.sqrt((match[0] - um[0])**2 + (match[1] - um[1])**2)
                if dist < 50:  # Threshold in pixels
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_matches.append(match)

        return unique_matches

    except Exception as e:
        logger.error(f"Template matching failed: {e}")
        return []
