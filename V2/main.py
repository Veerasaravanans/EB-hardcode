# import os
# import platform
# import time
# from config import load_config
# from logging_utils import setup_logger
# from automation.process_control import get_running_processes, get_new_processes
# from automation.pyautogui_utils import safe_click, safe_type
# from automation.system_search import open_system_search
# from vision.screenshot import take_screenshot
# from vision.ocr_utils import enhanced_ocr_search
# from utils.file_ops import cleanup_temp_files

# class AdvancedAppLauncher:
#     def __init__(self):
#         self.config = load_config()
#         self.logger = setup_logger()
#         self.system = platform.system()
#         self.launched_apps = {}
#         # Ensure directories exist
#         for d in [self.config['screenshot_dir'], self.config['template_dir'], self.config['temp_dir']]:
#             os.makedirs(d, exist_ok=True)

#     def get_aliases(self, app_name):
#         return self.config["app_aliases"].get(app_name.lower(), [app_name])

#     def launch_app(self, app_name):
#         self.logger.info(f"Launching: {app_name}")
#         aliases = self.get_aliases(app_name)
#         max_attempts = 3

#         for attempt in range(max_attempts):
#             # 1. Screenshot desktop/screen
#             screenshot_path = take_screenshot(self.config['screenshot_dir'], f"desktop_{app_name}_{attempt}.png")
#             if not screenshot_path or not os.path.exists(screenshot_path):
#                 self.logger.error("Failed to capture desktop screenshot.")
#                 continue

#             # 2. Try OCR for all known aliases
#             location_found = None
#             for alias in aliases:
#                 ocr_results = enhanced_ocr_search(
#                     screenshot_path,
#                     alias,
#                     self.config['temp_dir'],
#                     fuzzy_match=True,
#                     config_threshold=self.config["ocr_confidence_threshold"]
#                 )
#                 if ocr_results:
#                     location_found = ocr_results[0]['coordinates']
#                     self.logger.info(f"Found '{alias}' at {location_found} on desktop.")
#                     break

#             if location_found:
#                 if safe_click(*location_found, double_click=True):
#                     print(f"Launched '{app_name}' by direct screen click.")
#                     return True
#             else:
#                 self.logger.info(f"{app_name} NOT found on desktop; opening system search.")

#                 # 3. Fallback: Open search and type
#                 opened = open_system_search(self.system, self.config.get("system_shortcuts", {}))
#                 if not opened:
#                     self.logger.error("Could not open system search!")
#                     continue

#                 safe_type(app_name)
#                 time.sleep(1.3)

#                 search_path = take_screenshot(self.config['screenshot_dir'], f"search_{app_name}_{attempt}.png")
#                 if not search_path or not os.path.exists(search_path):
#                     self.logger.error("Failed to capture search screenshot.")
#                     continue

#                 # OCR search results for aliases
#                 location_found = None
#                 for alias in aliases:
#                     ocr_results = enhanced_ocr_search(
#                         search_path,
#                         alias,
#                         self.config['temp_dir'],
#                         fuzzy_match=True,
#                         config_threshold=self.config["ocr_confidence_threshold"]
#                     )
#                     if ocr_results:
#                         location_found = ocr_results[0]['coordinates']
#                         self.logger.info(f"Found '{alias}' in search results at {location_found}.")
#                         break

#                 if location_found:
#                     if safe_click(*location_found):
#                         print(f"Launched '{app_name}' via search result click.")
#                         return True
#                 else:
#                     import pyautogui
#                     pyautogui.press('enter')
#                     print(f"Launched '{app_name}' by pressing Enter (fallback).")
#                     return True

#         print(f"Failed to launch '{app_name}' after {max_attempts} attempts.")
#         return False

#     def interactive_mode(self):
#         print("Welcome to Advanced App Launcher!")
#         while True:
#             cmd = input("Enter app name or 'list', or 'quit': ").strip().lower()
#             if cmd in {"quit", "exit", "q"}:
#                 print("Exiting.")
#                 break
#             elif cmd == "list":
#                 print("Apps/aliases:")
#                 for k,v in self.config["app_aliases"].items():
#                     print(f"- {k}: {v}")
#             elif cmd:
#                 self.launch_app(cmd)

#     def cleanup(self):
#         cleanup_temp_files(self.config['temp_dir'])

# if __name__ == "__main__":
#     launcher = AdvancedAppLauncher()
#     try:
#         launcher.interactive_mode()
#     finally:
#         launcher.cleanup()

# mobile ui 
import os
import time
from PIL import Image
from config import load_config
from logging_utils import setup_logger
from vision.ocr_utils import enhanced_ocr_search
from utils.mobile_adb import adb_screenshot, adb_tap
from utils.file_ops import cleanup_temp_files
from utils.pdf_reader import extract_app_names_from_pdf
from fuzzywuzzy import fuzz

DEVICE_WIDTH, DEVICE_HEIGHT = 1080, 2340  # As returned by adb shell wm size

class MobileAppLauncher:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logger()
        self.screenshot_path = os.path.join(self.config['temp_dir'], "mobile_screen.png")
        os.makedirs(self.config['temp_dir'], exist_ok=True)

    def get_aliases(self, app_name):
        return self.config.get("app_aliases", {}).get(app_name.lower(), [app_name])

    def tap_icon_center(self, x_ocr, y_ocr):
        img_width, img_height = Image.open(self.screenshot_path).size
        x_dev = int(x_ocr * DEVICE_WIDTH / img_width)
        y_dev = int(y_ocr * DEVICE_HEIGHT / img_height)
        # Try multiple vertical offsets to hit the icon center above the label
        for delta in [0, 80, 120]:
            y_biased = max(y_dev - delta, 0)
            self.logger.info(f"Tapping device at ({x_dev}, {y_biased}) [bias={delta}]")
            adb_tap(x_dev, y_biased)
            time.sleep(0.2)

    def find_and_tap_app(self, app_name):
        aliases = self.get_aliases(app_name)
        max_attempts = 3
        fuzzy_threshold = 70

        for attempt in range(max_attempts):
            success = adb_screenshot(self.screenshot_path)
            if not success:
                print("Failed to get mobile screenshot via ADB. Is your device connected?")
                continue

            ocr_results = []
            for alias in aliases:
                ocr_results.extend(enhanced_ocr_search(
                    self.screenshot_path,
                    alias,
                    self.config['temp_dir'],
                    fuzzy_match=True,
                    config_threshold=self.config.get("ocr_confidence_threshold", 40)
                ))

            best_result = None
            best_score = 0
            for r in ocr_results:
                for alias in aliases:
                    fscore = fuzz.token_set_ratio(alias.lower(), r.get('text', '').lower())
                    if fscore > best_score and fscore >= fuzzy_threshold:
                        best_score = fscore
                        best_result = r

            if best_result:
                x, y = best_result['coordinates']
                self.logger.info(f"OCR match: '{best_result['text']}' (score: {best_score}) at ({x},{y})")
                self.tap_icon_center(x, y)
                print(f"Tapped app '{app_name}' at ({x}, {y}) [scaled to device].")
                return True
            else:
                print(f"No good OCR match found for '{app_name}' (attempt {attempt+1}). Retrying...")
                time.sleep(1)

        print(f"Failed to find/tap '{app_name}' after {max_attempts} screenshot attempts.")
        return False
    
# without pdf
    def interactive_mode(self):
        print("Welcome to MOBILE App Launcher! (Type 'quit' to exit)")
        while True:
            cmd = input("App name? ").strip().lower()
            if cmd in {"quit", "exit", "q"}:
                break
            elif cmd:
                self.find_and_tap_app(cmd)

#with pdf
    # def launch_from_pdf(self, pdf_path):
    #     app_names = extract_app_names_from_pdf(pdf_path)
    #     print(f"Extracted app names from PDF: {app_names}")
    #     for app_name in app_names:
    #         print(f"\nLaunching app '{app_name}' from PDF ...")
    #         self.find_and_tap_app(app_name)
    #         time.sleep(2)  # Brief pause between actions

    # def interactive_mode(self):
    #     print("Welcome to MOBILE App Launcher! (Type 'quit' to exit)")
    #     print("Type 'pdf <file_path>' to launch from PDF.")
    #     while True:
    #         cmd = input("App name? ").strip()
    #         if not cmd:
    #             continue
    #         if cmd.lower() in {"quit", "exit", "q"}:
    #             break
    #         elif cmd.lower().startswith('pdf '):
    #             pdf_path = cmd[4:].strip()
    #             if not os.path.exists(pdf_path):
    #                 print("File not found!")
    #             else:
    #                 self.launch_from_pdf(pdf_path)
    #         else:
    #             self.find_and_tap_app(cmd)

    # def cleanup(self):
    #     cleanup_temp_files(self.config['temp_dir'])

if __name__ == "__main__":
    launcher = MobileAppLauncher()
    try:
        launcher.interactive_mode()
    finally:
        launcher.cleanup()
