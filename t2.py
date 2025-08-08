import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import time
import platform
import os
import json
import logging
from typing import List, Tuple, Dict, Optional
import threading
from concurrent.futures import ThreadPoolExecutor
import difflib

class AdvancedAppLauncher:
    def __init__(self, config_path: str = "launcher_config.json"):
        """
        Initialize the Advanced App Launcher
        
        Args:
            config_path: Path to configuration file (CHANGE THIS PATH IF NEEDED)
        """
        self.system = platform.system()
        self.config_path = config_path
        self.setup_logging()
        self.load_config()
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.config.get("automation_delay", 0.3)
        
        # Create directories for screenshots and templates
        self.ensure_directories()
        
        # Enhanced Tesseract configuration
        self.tesseract_config = (
            '--psm 6 --oem 3 -c tessedit_char_whitelist='
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            ' .,-:()[]{}!@#$%^&*+=|\\/?<>'
        )
        
        self.logger.info(f"Launcher initialized for {self.system}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('launcher.log'),  # CHANGE LOG PATH IF NEEDED
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Load configuration from JSON file with expanded app support"""
        default_config = {
            "screenshot_dir": "./screenshots/",  # CHANGE SCREENSHOT DIR PATH
            "template_dir": "./templates/",      # CHANGE TEMPLATE DIR PATH
            "temp_dir": "./temp/",              # CHANGE TEMP DIR PATH
            "ocr_confidence_threshold": 40,
            "template_match_threshold": 0.75,
            "automation_delay": 0.3,
            "max_search_time": 10,
            # EXPANDED APP ALIASES - ADD MORE APPS HERE
            "app_aliases": {
                # System Apps
                "settings": ["settings", "preferences", "system preferences", "control panel"],
                "calculator": ["calculator", "calc"],
                "notepad": ["notepad", "text editor", "textedit", "wordpad"],
                "paint": ["paint", "mspaint", "drawing"],
                "snipping": ["snipping tool", "snip", "screenshot tool"],
                "taskmanager": ["task manager", "taskmgr", "process manager"],
                "explorer": ["file explorer", "explorer", "files", "my computer"],
                "cmd": ["command prompt", "cmd", "terminal", "powershell"],
                
                # Browsers
                "chrome": ["chrome", "google chrome"],
                "firefox": ["firefox", "mozilla firefox"],
                "edge": ["edge", "microsoft edge"],
                "safari": ["safari"],
                "opera": ["opera"],
                
                # Media Apps
                "vlc": ["vlc", "vlc media player"],
                "spotify": ["spotify", "music"],
                "photos": ["photos", "gallery", "pictures"],
                "movies": ["movies", "films", "video player"],
                
                # Office Apps
                "word": ["word", "microsoft word", "ms word"],
                "excel": ["excel", "microsoft excel", "ms excel"],
                "powerpoint": ["powerpoint", "microsoft powerpoint", "ms powerpoint"],
                "outlook": ["outlook", "microsoft outlook", "mail"],
                "onenote": ["onenote", "microsoft onenote", "notes"],
                
                # Development Tools
                "vscode": ["visual studio code", "vscode", "vs code", "code"],
                "notepad++": ["notepad++", "notepad plus", "npp"],
                "git": ["git", "git bash"],
                "docker": ["docker", "docker desktop"],
                
                # Communication
                "teams": ["teams", "microsoft teams"],
                "zoom": ["zoom", "zoom meeting"],
                "skype": ["skype"],
                "discord": ["discord"],
                "slack": ["slack"],
                
                # Games and Entertainment
                "steam": ["steam", "steam client"],
                "epic": ["epic games", "epic games launcher"],
                "origin": ["origin", "ea origin"],
                
                # Utilities
                "7zip": ["7zip", "7-zip", "winrar", "zip"],
                "ccleaner": ["ccleaner", "cleaner"],
                "antivirus": ["antivirus", "windows defender", "defender"],
                
                # Adobe Suite
                "photoshop": ["photoshop", "adobe photoshop"],
                "illustrator": ["illustrator", "adobe illustrator"],
                "premiere": ["premiere", "adobe premiere"],
                "acrobat": ["acrobat", "adobe acrobat", "pdf reader"],
            },
            "system_shortcuts": {
                "Windows": "win",
                "Darwin": ["cmd", "space"],
                "Linux": ["alt", "f2"]
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            else:
                # Create default config file
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.logger.info(f"Created default config at {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
        
        self.config = default_config
    
    def ensure_directories(self):
        """Create necessary directories"""
        dirs_to_create = [
            self.config["screenshot_dir"],
            self.config["template_dir"], 
            self.config["temp_dir"]
        ]
        
        for directory in dirs_to_create:
            os.makedirs(directory, exist_ok=True)
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take an optimized screenshot"""
        if not filename:
            timestamp = int(time.time())
            filename = f"screen_{timestamp}.png"
        
        filepath = os.path.join(self.config["screenshot_dir"], filename)
        
        try:
            # Take screenshot with specific region if needed (full screen for now)
            screenshot = pyautogui.screenshot()
            
            # Optimize screenshot for OCR
            screenshot = screenshot.convert('RGB')
            screenshot.save(filepath, optimize=True, quality=85)
            
            self.logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    def preprocess_image_for_ocr(self, image_path: str, enhancement_level: int = 2) -> str:
        """Advanced image preprocessing for better OCR accuracy"""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Enhancement level 1: Basic
            if enhancement_level >= 1:
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
            
            # Enhancement level 2: Advanced
            if enhancement_level >= 2:
                # Convert to OpenCV format
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Convert to grayscale
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                
                # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                
                # Denoise
                gray = cv2.fastNlMeansDenoising(gray)
                
                # Morphological operations
                kernel = np.ones((2,2), np.uint8)
                gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
                
                # Convert back to PIL Image
                img = Image.fromarray(gray)
            
            # Save processed image
            processed_path = os.path.join(self.config["temp_dir"], "processed_" + os.path.basename(image_path))
            img.save(processed_path)
            
            return processed_path
        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {e}")
            return image_path
    
    def enhanced_ocr_search(self, image_path: str, target_text: str, fuzzy_match: bool = True) -> List[Dict]:
        """Advanced OCR with fuzzy matching and multiple preprocessing attempts"""
        matches = []
        
        # Try different preprocessing levels
        for enhancement_level in [0, 1, 2]:
            try:
                if enhancement_level == 0:
                    processed_path = image_path
                else:
                    processed_path = self.preprocess_image_for_ocr(image_path, enhancement_level)
                
                # Perform OCR
                data = pytesseract.image_to_data(
                    Image.open(processed_path),
                    output_type=pytesseract.Output.DICT,
                    config=self.tesseract_config
                )
                
                # Process OCR results
                for i, text in enumerate(data['text']):
                    if (len(text.strip()) > 0 and 
                        data['conf'][i] > self.config["ocr_confidence_threshold"]):
                        
                        # Direct match
                        if target_text.lower() in text.lower():
                            match_score = 100
                        # Fuzzy match
                        elif fuzzy_match:
                            match_score = difflib.SequenceMatcher(None, target_text.lower(), text.lower()).ratio() * 100
                        else:
                            match_score = 0
                        
                        if match_score > 70:  # 70% similarity threshold
                            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                            center_x, center_y = x + w // 2, y + h // 2
                            
                            matches.append({
                                'coordinates': (center_x, center_y),
                                'text': text,
                                'confidence': data['conf'][i],
                                'match_score': match_score,
                                'bbox': (x, y, w, h),
                                'enhancement_level': enhancement_level
                            })
                
                # Clean up temporary files
                if enhancement_level > 0 and os.path.exists(processed_path):
                    os.remove(processed_path)
                    
            except Exception as e:
                self.logger.error(f"OCR failed at enhancement level {enhancement_level}: {e}")
                continue
        
        # Sort by match score and confidence
        matches.sort(key=lambda x: (x['match_score'], x['confidence']), reverse=True)
        
        # Remove duplicates (nearby matches)
        unique_matches = []
        for match in matches:
            is_duplicate = False
            for unique in unique_matches:
                distance = np.sqrt((match['coordinates'][0] - unique['coordinates'][0])**2 + 
                                 (match['coordinates'][1] - unique['coordinates'][1])**2)
                if distance < 50:  # 50 pixel threshold for duplicates
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_matches.append(match)
        
        return unique_matches[:5]  # Return top 5 matches
    
    def detect_ui_elements(self, image_path: str) -> List[Dict]:
        """Detect various UI elements using computer vision"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            elements = []
            
            # Method 1: Contour detection for buttons/icons
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 20000:  # Filter by area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Classify element type
                    if 0.8 <= aspect_ratio <= 1.2 and 1000 <= area <= 5000:
                        element_type = "icon"
                    elif 2.0 <= aspect_ratio <= 10.0 and 1000 <= area <= 10000:
                        element_type = "button"
                    else:
                        element_type = "unknown"
                    
                    elements.append({
                        'type': element_type,
                        'coordinates': (x + w//2, y + h//2),
                        'bbox': (x, y, w, h),
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
            
            # Method 2: Edge detection for clickable areas
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    elements.append({
                        'type': 'clickable',
                        'coordinates': (x + w//2, y + h//2),
                        'bbox': (x, y, w, h),
                        'area': area
                    })
            
            return elements
            
        except Exception as e:
            self.logger.error(f"UI element detection failed: {e}")
            return []
    
    def template_match(self, screenshot_path: str, template_name: str) -> List[Tuple]:
        """Template matching for known UI elements"""
        template_path = os.path.join(self.config["template_dir"], f"{template_name}.png")
        
        if not os.path.exists(template_path):
            return []
        
        try:
            img = cv2.imread(screenshot_path, 0)
            template = cv2.imread(template_path, 0)
            
            if template is None:
                return []
            
            # Multi-scale template matching
            scales = [0.8, 0.9, 1.0, 1.1, 1.2]
            all_matches = []
            
            for scale in scales:
                if scale != 1.0:
                    w = int(template.shape[1] * scale)
                    h = int(template.shape[0] * scale)
                    scaled_template = cv2.resize(template, (w, h))
                else:
                    scaled_template = template
                
                res = cv2.matchTemplate(img, scaled_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(res >= self.config["template_match_threshold"])
                
                for pt in zip(*locations[::-1]):
                    center_x = pt[0] + scaled_template.shape[1] // 2
                    center_y = pt[1] + scaled_template.shape[0] // 2
                    confidence = res[pt[1], pt[0]]
                    all_matches.append((center_x, center_y, confidence))
            
            # Remove duplicate matches
            unique_matches = []
            for match in sorted(all_matches, key=lambda x: x[2], reverse=True):
                is_duplicate = False
                for unique in unique_matches:
                    distance = np.sqrt((match[0] - unique[0])**2 + (match[1] - unique[1])**2)
                    if distance < 50:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_matches.append(match)
            
            return unique_matches
            
        except Exception as e:
            self.logger.error(f"Template matching failed: {e}")
            return []
    
    def get_app_aliases(self, app_name: str) -> List[str]:
        """Get all possible aliases for an app"""
        aliases = [app_name.lower()]
        
        for key, value_list in self.config["app_aliases"].items():
            if app_name.lower() in [v.lower() for v in value_list] or app_name.lower() == key.lower():
                aliases.extend([v.lower() for v in value_list])
                aliases.append(key.lower())
        
        return list(set(aliases))  # Remove duplicates
    
    def find_app_comprehensive(self, screenshot_path: str, app_name: str) -> Optional[Tuple]:
        """Comprehensive app finding using multiple methods"""
        aliases = self.get_app_aliases(app_name)
        self.logger.info(f"Searching for app with aliases: {aliases}")
        
        all_results = []
        
        # Method 1: Enhanced OCR search for all aliases
        for alias in aliases:
            ocr_matches = self.enhanced_ocr_search(screenshot_path, alias)
            for match in ocr_matches:
                all_results.append({
                    'method': 'ocr',
                    'coordinates': match['coordinates'],
                    'score': match['match_score'] + match['confidence'] / 10,
                    'details': match
                })
        
        # Method 2: Template matching
        template_matches = self.template_match(screenshot_path, app_name)
        for match in template_matches:
            all_results.append({
                'method': 'template',
                'coordinates': (match[0], match[1]),
                'score': match[2] * 100,
                'details': match
            })
        
        # Method 3: UI element detection + OCR verification
        ui_elements = self.detect_ui_elements(screenshot_path)
        img = Image.open(screenshot_path)
        
        for element in ui_elements:
            if element['type'] in ['icon', 'button']:
                # Crop around element for OCR
                x, y, w, h = element['bbox']
                margin = 10
                crop_box = (max(0, x-margin), max(0, y-margin), 
                           min(img.width, x+w+margin), min(img.height, y+h+margin))
                
                cropped = img.crop(crop_box)
                temp_crop_path = os.path.join(self.config["temp_dir"], "temp_crop.png")
                cropped.save(temp_crop_path)
                
                # Check if cropped area contains target text
                for alias in aliases:
                    local_matches = self.enhanced_ocr_search(temp_crop_path, alias, fuzzy_match=True)
                    if local_matches:
                        all_results.append({
                            'method': 'ui_ocr',
                            'coordinates': element['coordinates'],
                            'score': local_matches[0]['match_score'] + 20,  # Bonus for UI detection
                            'details': {'ui_element': element, 'ocr_match': local_matches[0]}
                        })
                
                # Clean up
                if os.path.exists(temp_crop_path):
                    os.remove(temp_crop_path)
        
        # Sort all results by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        if all_results:
            best_match = all_results[0]
            self.logger.info(f"Best match found using {best_match['method']} with score {best_match['score']}")
            return best_match['coordinates']
        
        return None
    
    def open_system_search(self) -> bool:
        """Open system search with OS-specific shortcuts"""
        try:
            shortcuts = self.config["system_shortcuts"]
            
            if self.system in shortcuts:
                shortcut = shortcuts[self.system]
                if isinstance(shortcut, list):
                    pyautogui.hotkey(*shortcut)
                else:
                    pyautogui.press(shortcut)
                
                time.sleep(1)  # Wait for search to open
                self.logger.info(f"Opened system search for {self.system}")
                return True
            else:
                self.logger.error(f"No shortcut defined for {self.system}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to open system search: {e}")
            return False
    
    def safe_click(self, x: int, y: int, double_click: bool = False) -> bool:
        """Safe clicking with bounds checking"""
        try:
            screen_width, screen_height = pyautogui.size()
            
            if 0 <= x <= screen_width and 0 <= y <= screen_height:
                if double_click:
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.click(x, y)
                
                time.sleep(0.5)
                self.logger.info(f"Clicked at ({x}, {y})")
                return True
            else:
                self.logger.error(f"Click coordinates ({x}, {y}) out of bounds")
                return False
                
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False
    
    def safe_type(self, text: str) -> bool:
        """Safe typing with error handling"""
        try:
            pyautogui.write(text, interval=0.05)
            time.sleep(0.5)
            self.logger.info(f"Typed: {text}")
            return True
        except Exception as e:
            self.logger.error(f"Typing failed: {e}")
            return False
    
    def launch_app(self, app_name: str, max_attempts: int = 3) -> bool:
        """Main method to launch an application"""
        self.logger.info(f"Starting launch sequence for: {app_name}")
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_attempts}")
                
                # Step 1: Take initial screenshot
                initial_screenshot = self.take_screenshot(f"initial_{app_name}_{attempt}.png")
                if not initial_screenshot:
                    continue
                
                # Step 2: Search for app in current screen
                app_location = self.find_app_comprehensive(initial_screenshot, app_name)
                
                if app_location:
                    self.logger.info(f"Found {app_name} at {app_location}")
                    if self.safe_click(app_location[0], app_location[1], double_click=True):
                        time.sleep(2)  # Wait for app to launch
                        return True
                
                # Step 3: Open system search if app not found
                self.logger.info(f"{app_name} not found on screen, opening search...")
                
                if not self.open_system_search():
                    continue
                
                # Step 4: Take screenshot after opening search
                search_screenshot = self.take_screenshot(f"search_{app_name}_{attempt}.png")
                if not search_screenshot:
                    continue
                
                # Step 5: Type app name in search
                if self.safe_type(app_name):
                    time.sleep(1)  # Wait for search results
                    
                    # Step 6: Take screenshot of search results
                    results_screenshot = self.take_screenshot(f"results_{app_name}_{attempt}.png")
                    if not results_screenshot:
                        continue
                    
                    # Step 7: Find app in search results
                    app_in_results = self.find_app_comprehensive(results_screenshot, app_name)
                    
                    if app_in_results:
                        self.logger.info(f"Found {app_name} in search results")
                        if self.safe_click(app_in_results[0], app_in_results[1]):
                            time.sleep(2)
                            return True
                    else:
                        # Fallback: Press Enter to launch first result
                        self.logger.info("Pressing Enter to launch first search result")
                        pyautogui.press('enter')
                        time.sleep(2)
                        return True
                
                # If this attempt failed, press Escape to close search
                pyautogui.press('escape')
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                continue
        
        self.logger.error(f"Failed to launch {app_name} after {max_attempts} attempts")
        return False
    
    def list_available_apps(self) -> None:
        """Display all available apps that can be launched"""
        print("\n" + "="*60)
        print("AVAILABLE APPLICATIONS")
        print("="*60)
        
        categories = {
            "System Apps": ["settings", "calculator", "notepad", "paint", "snipping", "taskmanager", "explorer", "cmd"],
            "Browsers": ["chrome", "firefox", "edge", "safari", "opera"],
            "Media Apps": ["vlc", "spotify", "photos", "movies"],
            "Office Apps": ["word", "excel", "powerpoint", "outlook", "onenote"],
            "Development": ["vscode", "notepad++", "git", "docker"],
            "Communication": ["teams", "zoom", "skype", "discord", "slack"],
            "Games": ["steam", "epic", "origin"],
            "Utilities": ["7zip", "ccleaner", "antivirus"],
            "Adobe Suite": ["photoshop", "illustrator", "premiere", "acrobat"]
        }
        
        for category, apps in categories.items():
            print(f"\n{category}:")
            for app in apps:
                aliases = self.config["app_aliases"].get(app, [app])
                print(f"  • {app.title()} (aliases: {', '.join(aliases[:3])}{'...' if len(aliases) > 3 else ''})")
    
    def add_new_app(self, app_key: str, aliases: List[str]) -> bool:
        """Add a new app to the configuration"""
        try:
            # Add to current config
            self.config["app_aliases"][app_key.lower()] = [alias.lower() for alias in aliases]
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            print(f"✓ Added new app '{app_key}' with aliases: {aliases}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add new app: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = self.config["temp_dir"]
            for filename in os.listdir(temp_dir):
                if filename.startswith("temp_") or filename.startswith("processed_"):
                    file_path = os.path.join(temp_dir, filename)
                    os.remove(file_path)
            self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def interactive_mode(self):
        """Interactive mode for launching applications"""
        print("\n" + "="*60)
        print("ADVANCED APP LAUNCHER - INTERACTIVE MODE")
        print("="*60)
        print("Commands:")
        print("  • Type app name to launch (e.g., 'settings', 'chrome', 'calculator')")
        print("  • 'list' - Show all available apps")
        print("  • 'add' - Add a new app")
        print("  • 'help' - Show this help message")
        print("  • 'quit' or 'exit' - Exit the program")
        print("="*60)
        
        while True:
            try:
                user_input = input("\nEnter command or app name: ").strip()
                
                if not user_input:
                    continue
                
                command = user_input.lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif command == 'list':
                    self.list_available_apps()
                
                elif command == 'help':
                    print("\nCommands:")
                    print("  • Type app name to launch")
                    print("  • 'list' - Show available apps")
                    print("  • 'add' - Add new app")
                    print("  • 'quit' - Exit")
                
                elif command == 'add':
                    app_name = input("Enter app name (key): ").strip()
                    if app_name:
                        aliases_input = input(f"Enter aliases for '{app_name}' (comma-separated): ").strip()
                        if aliases_input:
                            aliases = [alias.strip() for alias in aliases_input.split(',')]
                            aliases.append(app_name)  # Include the app name itself
                            self.add_new_app(app_name, aliases)
                        else:
                            print("No aliases provided.")
                    else:
                        print("No app name provided.")
                
                else:
                    # Try to launch the app
                    print(f"Attempting to launch: {user_input}")
                    success = self.launch_app(user_input)
                    
                    if success:
                        print(f"✓ Successfully launched {user_input}")
                    else:
                        print(f"✗ Failed to launch {user_input}")
                        print("Tip: Use 'list' to see available apps or 'add' to add new apps")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

# Updated main execution
if __name__ == "__main__":
    # Initialize the launcher
    launcher = AdvancedAppLauncher()
    
    # Start interactive mode
    try:
        launcher.interactive_mode()
    finally:
        # Cleanup temporary files before exit
        launcher.cleanup_temp_files()