import cv2
import numpy as np
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

def create_close_button_templates():
    templates = {}
    try:
        x_template = np.zeros((20,20), dtype=np.uint8)
        for i in range(20):
            x_template[i,i] = 255
            x_template[i,19-i] = 255
        templates['x_pattern'] = x_template

        square_x_template = np.zeros((24,24), dtype=np.uint8)
        cv2.rectangle(square_x_template, (2,2), (21,21), 255, 1)
        for i in range(6,18):
            square_x_template[i,i] = 255
            square_x_template[i,23-i] = 255
        templates['square_x'] = square_x_template

        circle_x_template = np.zeros((22,22), dtype=np.uint8)
        cv2.circle(circle_x_template, (11,11), 9, 255, 1)
        for i in range(5,17):
            circle_x_template[i,i] = 255
            circle_x_template[i,21-i] = 255
        templates['circle_x'] = circle_x_template

    except Exception as e:
        logger.error(f"Error creating templates: {e}")
    return templates

def remove_duplicate_close_buttons(buttons):
    unique_buttons = []
    for btn in buttons:
        if not any(np.linalg.norm(np.array(btn['coordinates']) - np.array(other['coordinates'])) < 30 for other in unique_buttons):
            unique_buttons.append(btn)
        else:
            for other in unique_buttons:
                dist = np.linalg.norm(np.array(btn['coordinates']) - np.array(other['coordinates']))
                if dist < 30 and btn['confidence'] > other['confidence']:
                    unique_buttons.remove(other)
                    unique_buttons.append(btn)
                    break
    return unique_buttons

def detect_close_button_by_shape(image_path, search_area=0.3, size_range=(10,50)):
    try:
        img = cv2.imread(image_path)
        height, width = img.shape[:2]

        search_height = int(height * search_area)
        top_img = img[0:search_height, :]

        gray = cv2.cvtColor(top_img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(top_img, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_size, max_size = size_range

        close_buttons = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_size * min_size < area < max_size * max_size:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w/h if h > 0 else 0
                if 0.7 <= aspect_ratio <= 1.3 and x > width * 0.7:
                    close_buttons.append({'coordinates': (x + w//2, y + h//2), 'confidence': 85, 'method': 'red_color_detection', 'bbox': (x, y, w, h), 'area': area})

        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_size * min_size < area < max_size * max_size:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w/h if h > 0 else 0
                if 0.8 <= aspect_ratio <= 1.2 and x > width * 0.8 and y < search_height * 0.5:
                    close_buttons.append({'coordinates': (x + w//2, y + h//2), 'confidence': 70, 'method': 'edge_detection', 'bbox': (x, y, w, h), 'area': area})

        templates = create_close_button_templates()
        for name, template in templates.items():
            if template is not None:
                res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                locs = np.where(res >= 0.6)
                for pt in zip(*locs[::-1]):
                    x, y = pt
                    h_t, w_t = template.shape
                    if x > width * 0.7:
                        close_buttons.append({'coordinates': (x + w_t//2, y + h_t//2), 'confidence': res[y, x] * 100, 'method': f'template_{name}', 'bbox': (x, y, w_t, h_t), 'area': w_t*h_t})
        unique = remove_duplicate_close_buttons(close_buttons)
        unique.sort(key=lambda b: b['confidence'], reverse=True)
        return unique
    except Exception as e:
        logger.error(f"Shape-based close button detection failed: {e}")
        return []

# For OCR close button detection, you can call enhanced_ocr_search with symbols on a cropped top region; integrate with your launcher class accordingly.
