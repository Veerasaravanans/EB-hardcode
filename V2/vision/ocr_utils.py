import pytesseract
from PIL import Image, ImageEnhance
import os
import difflib
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Whitelist characters can be adapted
TESSERACT_CONFIG = (
    '--psm 6 --oem 3 -c tessedit_char_whitelist='
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,-:()[]{}!@#$%^&*+=|\\/?<>'
)

def preprocess_image_for_ocr(image_path, temp_dir, enhancement_level=2):
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if enhancement_level >= 1:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)

        if enhancement_level >= 2:
            import cv2
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            gray = cv2.fastNlMeansDenoising(gray)
            kernel = np.ones((2,2), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            img = Image.fromarray(gray)

        processed_path = os.path.join(temp_dir, "processed_" + os.path.basename(image_path))
        img.save(processed_path)
        return processed_path
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        return image_path

def enhanced_ocr_search(image_path, target_text, temp_dir=None, fuzzy_match=True, config_threshold=40):
    matches = []
    for lvl in [0, 1, 2]:
        try:
            processed_path = image_path if lvl == 0 else preprocess_image_for_ocr(image_path, temp_dir, lvl)
            data = pytesseract.image_to_data(
                Image.open(processed_path),
                output_type=pytesseract.Output.DICT,
                config=TESSERACT_CONFIG
            )

            for i, text in enumerate(data['text']):
                print(f"Detected: '{text}' (conf: {data['conf'][i]})")
                conf = int(data['conf'][i])
                if conf > config_threshold and text.strip():
                    if target_text.lower() in text.lower():
                        score = 100
                    elif fuzzy_match:
                        score = difflib.SequenceMatcher(None, target_text.lower(), text.lower()).ratio() * 100
                    else:
                        score = 0

                    if score > 70:
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        cx, cy = x + w // 2, y + h // 2
                        matches.append({
                            'coordinates': (cx, cy),
                            'text': text,
                            'confidence': conf,
                            'match_score': score,
                            'bbox': (x, y, w, h),
                            'enhancement_level': lvl,
                        })

            if lvl > 0 and processed_path and os.path.exists(processed_path):
                os.remove(processed_path)
        except Exception as e:
            logger.error(f"OCR failed at enhancement level {lvl}: {e}")
            continue

    # Remove duplicates within 50 pixels
    unique_matches = []
    for match in matches:
        if not any(np.linalg.norm(np.array(match['coordinates']) - np.array(uniq['coordinates'])) < 50 for uniq in unique_matches):
            unique_matches.append(match)

    unique_matches.sort(key=lambda x: (x['match_score'], x['confidence']), reverse=True)
    return unique_matches[:5]
