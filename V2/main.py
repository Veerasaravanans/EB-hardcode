import os
import platform
import time
from config import load_config
from logging_utils import setup_logger
from automation.process_control import get_running_processes, get_new_processes
from automation.pyautogui_utils import safe_click, safe_type
from automation.system_search import open_system_search
from vision.screenshot import take_screenshot
from vision.ocr_utils import enhanced_ocr_search
from utils.file_ops import cleanup_temp_files

class AdvancedAppLauncher:
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logger()
        self.system = platform.system()
        self.launched_apps = {}
        # Ensure directories exist
        for d in [self.config['screenshot_dir'], self.config['template_dir'], self.config['temp_dir']]:
            os.makedirs(d, exist_ok=True)

    def get_aliases(self, app_name):
        return self.config["app_aliases"].get(app_name.lower(), [app_name])

    def launch_app(self, app_name):
        self.logger.info(f"Launching: {app_name}")
        aliases = self.get_aliases(app_name)
        max_attempts = 3

        for attempt in range(max_attempts):
            # 1. Screenshot desktop/screen
            screenshot_path = take_screenshot(self.config['screenshot_dir'], f"desktop_{app_name}_{attempt}.png")
            if not screenshot_path or not os.path.exists(screenshot_path):
                self.logger.error("Failed to capture desktop screenshot.")
                continue

            # 2. Try OCR for all known aliases
            location_found = None
            for alias in aliases:
                ocr_results = enhanced_ocr_search(
                    screenshot_path,
                    alias,
                    self.config['temp_dir'],
                    fuzzy_match=True,
                    config_threshold=self.config["ocr_confidence_threshold"]
                )
                if ocr_results:
                    location_found = ocr_results[0]['coordinates']
                    self.logger.info(f"Found '{alias}' at {location_found} on desktop.")
                    break

            if location_found:
                if safe_click(*location_found, double_click=True):
                    print(f"Launched '{app_name}' by direct screen click.")
                    return True
            else:
                self.logger.info(f"{app_name} NOT found on desktop; opening system search.")

                # 3. Fallback: Open search and type
                opened = open_system_search(self.system, self.config.get("system_shortcuts", {}))
                if not opened:
                    self.logger.error("Could not open system search!")
                    continue

                safe_type(app_name)
                time.sleep(1.3)

                search_path = take_screenshot(self.config['screenshot_dir'], f"search_{app_name}_{attempt}.png")
                if not search_path or not os.path.exists(search_path):
                    self.logger.error("Failed to capture search screenshot.")
                    continue

                # OCR search results for aliases
                location_found = None
                for alias in aliases:
                    ocr_results = enhanced_ocr_search(
                        search_path,
                        alias,
                        self.config['temp_dir'],
                        fuzzy_match=True,
                        config_threshold=self.config["ocr_confidence_threshold"]
                    )
                    if ocr_results:
                        location_found = ocr_results[0]['coordinates']
                        self.logger.info(f"Found '{alias}' in search results at {location_found}.")
                        break

                if location_found:
                    if safe_click(*location_found):
                        print(f"Launched '{app_name}' via search result click.")
                        return True
                else:
                    import pyautogui
                    pyautogui.press('enter')
                    print(f"Launched '{app_name}' by pressing Enter (fallback).")
                    return True

        print(f"Failed to launch '{app_name}' after {max_attempts} attempts.")
        return False

    def interactive_mode(self):
        print("Welcome to Advanced App Launcher!")
        while True:
            cmd = input("Enter app name or 'list', or 'quit': ").strip().lower()
            if cmd in {"quit", "exit", "q"}:
                print("Exiting.")
                break
            elif cmd == "list":
                print("Apps/aliases:")
                for k,v in self.config["app_aliases"].items():
                    print(f"- {k}: {v}")
            elif cmd:
                self.launch_app(cmd)

    def cleanup(self):
        cleanup_temp_files(self.config['temp_dir'])

if __name__ == "__main__":
    launcher = AdvancedAppLauncher()
    try:
        launcher.interactive_mode()
    finally:
        launcher.cleanup()
