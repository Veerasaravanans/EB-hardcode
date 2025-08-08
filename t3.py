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
import psutil

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
        
        # Store launched app information for closing
        self.launched_apps = {}
        
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
            "auto_close_delay": 3,  # Auto-close delay in seconds
            "enable_auto_close": True,  # Enable/disable auto-close feature
            "close_button_search_area": 0.3,  # Search in top 30% of screen for close buttons
            "close_button_size_range": (10, 50),  # Min and max size for close buttons
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
            },
            # App process name mappings for tracking processes
            "app_process_names": {
                "calculator": ["calc.exe", "Calculator.exe", "calculator"],
                "notepad": ["notepad.exe", "Notepad.exe"],
                "chrome": ["chrome.exe", "Google Chrome"],
                "firefox": ["firefox.exe", "Firefox"],
                "edge": ["msedge.exe", "Microsoft Edge"],
                "vscode": ["Code.exe", "code"],
                "spotify": ["Spotify.exe", "spotify"],
                "vlc": ["vlc.exe", "VLC media player"],
                "paint": ["mspaint.exe", "Paint"],
                "cmd": ["cmd.exe", "conhost.exe"],
                "settings": ["SystemSettings.exe", "Settings"],
                "taskmanager": ["Taskmgr.exe", "Task Manager"],
                "explorer": ["explorer.exe", "File Explorer"],
                # Add more app process mappings as needed
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
    
    def get_running_processes_before_launch(self) -> set:
        """Get list of running processes before launching app"""
        try:
            processes = set()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    processes.add((proc.info['pid'], proc.info['name'].lower()))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
            return set()
    
    def get_new_processes(self, before_processes: set) -> List[Tuple]:
        """Get new processes that started after launch"""
        try:
            current_processes = set()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    current_processes.add((proc.info['pid'], proc.info['name'].lower()))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            new_processes = current_processes - before_processes
            return list(new_processes)
        except Exception as e:
            self.logger.error(f"Error getting new processes: {e}")
            return []
    
    def detect_close_button_by_shape(self, image_path: str) -> List[Dict]:
        """Detect close buttons using shape and color detection"""
        try:
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            
            # Focus on the top portion of the screen where close buttons usually are
            search_height = int(height * self.config["close_button_search_area"])
            top_region = img[0:search_height, :]
            
            # Convert to different color spaces for better detection
            gray = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(top_region, cv2.COLOR_BGR2HSV)
            
            close_buttons = []
            
            # Method 1: Red close button detection (common in many apps)
            # Define range for red colors in HSV
            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            # Find contours in red regions
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            min_size, max_size = self.config["close_button_size_range"]
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_size * min_size < area < max_size * max_size:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Close buttons are usually square-ish
                    if 0.7 <= aspect_ratio <= 1.3:
                        # Check if it's in the top-right area of the search region
                        if x > width * 0.7:  # Right side of screen
                            close_buttons.append({
                                'coordinates': (x + w//2, y + h//2),
                                'confidence': 85,
                                'method': 'red_color_detection',
                                'bbox': (x, y, w, h),
                                'area': area
                            })
            
            # Method 2: Edge detection for button-like shapes
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_size * min_size < area < max_size * max_size:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Look for square shapes in top-right area
                    if 0.8 <= aspect_ratio <= 1.2 and x > width * 0.8 and y < search_height * 0.5:
                        close_buttons.append({
                            'coordinates': (x + w//2, y + h//2),
                            'confidence': 70,
                            'method': 'edge_detection',
                            'bbox': (x, y, w, h),
                            'area': area
                        })
            
            # Method 3: Template matching for common close button patterns
            # Create simple close button templates
            templates = self.create_close_button_templates()
            
            for template_name, template in templates.items():
                if template is not None:
                    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                    locations = np.where(res >= 0.6)  # Lower threshold for template matching
                    
                    for pt in zip(*locations[::-1]):
                        x, y = pt
                        h, w = template.shape
                        
                        # Check if it's in the expected area
                        if x > width * 0.7:  # Right side
                            close_buttons.append({
                                'coordinates': (x + w//2, y + h//2),
                                'confidence': res[pt[1], pt[0]] * 100,
                                'method': f'template_{template_name}',
                                'bbox': (x, y, w, h),
                                'area': w * h
                            })
            
            # Remove duplicates and sort by confidence
            unique_buttons = self.remove_duplicate_close_buttons(close_buttons)
            unique_buttons.sort(key=lambda x: x['confidence'], reverse=True)
            
            return unique_buttons
            
        except Exception as e:
            self.logger.error(f"Close button shape detection failed: {e}")
            return []
    
    def create_close_button_templates(self) -> Dict[str, np.ndarray]:
        """Create template images for common close button patterns"""
        templates = {}
        
        try:
            # Template 1: Simple X pattern
            x_template = np.zeros((20, 20), dtype=np.uint8)
            # Draw an X
            for i in range(20):
                x_template[i, i] = 255  # Diagonal line
                x_template[i, 19-i] = 255  # Other diagonal
            templates['x_pattern'] = x_template
            
            # Template 2: Square with X
            square_x_template = np.zeros((24, 24), dtype=np.uint8)
            # Draw border
            cv2.rectangle(square_x_template, (2, 2), (21, 21), 255, 1)
            # Draw X inside
            for i in range(6, 18):
                square_x_template[i, i] = 255
                square_x_template[i, 23-i] = 255
            templates['square_x'] = square_x_template
            
            # Template 3: Circle with X
            circle_x_template = np.zeros((22, 22), dtype=np.uint8)
            cv2.circle(circle_x_template, (11, 11), 9, 255, 1)
            # Draw X
            for i in range(5, 17):
                circle_x_template[i, i] = 255
                circle_x_template[i, 21-i] = 255
            templates['circle_x'] = circle_x_template
            
        except Exception as e:
            self.logger.error(f"Template creation failed: {e}")
        
        return templates
    
    def remove_duplicate_close_buttons(self, buttons: List[Dict]) -> List[Dict]:
        """Remove duplicate close button detections"""
        if not buttons:
            return []
        
        unique_buttons = []
        
        for button in buttons:
            is_duplicate = False
            for unique in unique_buttons:
                # Calculate distance between button centers
                dist = np.sqrt((button['coordinates'][0] - unique['coordinates'][0])**2 + 
                              (button['coordinates'][1] - unique['coordinates'][1])**2)
                
                # If buttons are close to each other, keep the one with higher confidence
                if dist < 30:  # 30 pixel threshold
                    is_duplicate = True
                    if button['confidence'] > unique['confidence']:
                        unique_buttons.remove(unique)
                        unique_buttons.append(button)
                    break
            
            if not is_duplicate:
                unique_buttons.append(button)
        
        return unique_buttons
    
    def detect_close_button_by_ocr(self, image_path: str) -> List[Dict]:
        """Detect close buttons using OCR to find X symbols"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Focus on top portion of screen
            search_height = int(height * self.config["close_button_search_area"])
            top_region = img.crop((0, 0, width, search_height))
            
            # Save cropped region for OCR
            temp_crop_path = os.path.join(self.config["temp_dir"], "close_search_crop.png")
            top_region.save(temp_crop_path)
            
            close_buttons = []
            
            # Look for various close button symbols
            close_symbols = ['×', '✕', 'X', 'x', '⨯', '✖', '☓']
            
            for symbol in close_symbols:
                matches = self.enhanced_ocr_search(temp_crop_path, symbol, fuzzy_match=False)
                
                for match in matches:
                    x, y = match['coordinates']
                    
                    # Adjust coordinates back to full screen
                    full_screen_x = x
                    full_screen_y = y
                    
                    # Check if it's in the right area (top-right portion)
                    if full_screen_x > width * 0.7 and full_screen_y < search_height * 0.6:
                        close_buttons.append({
                            'coordinates': (full_screen_x, full_screen_y),
                            'confidence': match['confidence'] + match['match_score'],
                            'method': f'ocr_{symbol}',
                            'bbox': match['bbox'],
                            'symbol': symbol,
                            'area': match['bbox'][2] * match['bbox'][3]
                        })
            
            # Clean up temp file
            if os.path.exists(temp_crop_path):
                os.remove(temp_crop_path)
            
            # Remove duplicates and sort
            unique_buttons = self.remove_duplicate_close_buttons(close_buttons)
            unique_buttons.sort(key=lambda x: x['confidence'], reverse=True)
            
            return unique_buttons
            
        except Exception as e:
            self.logger.error(f"OCR close button detection failed: {e}")
            return []
    
    def find_and_click_close_button(self) -> bool:
        """Find and click the close button using multiple detection methods"""
        try:
            # Take screenshot for close button detection
            screenshot_path = self.take_screenshot("close_button_detection.png")
            if not screenshot_path:
                return False
            
            self.logger.info("Searching for close button...")
            
            all_close_buttons = []
            
            # Method 1: Shape and color detection
            shape_buttons = self.detect_close_button_by_shape(screenshot_path)
            all_close_buttons.extend(shape_buttons)
            self.logger.info(f"Found {len(shape_buttons)} buttons using shape detection")
            
            # Method 2: OCR detection
            ocr_buttons = self.detect_close_button_by_ocr(screenshot_path)
            all_close_buttons.extend(ocr_buttons)
            self.logger.info(f"Found {len(ocr_buttons)} buttons using OCR detection")
            
            # Remove duplicates across all methods
            unique_buttons = self.remove_duplicate_close_buttons(all_close_buttons)
            
            if not unique_buttons:
                self.logger.warning("No close buttons found")
                return False
            
            # Sort by confidence and try clicking the best candidates
            unique_buttons.sort(key=lambda x: x['confidence'], reverse=True)
            
            self.logger.info(f"Found {len(unique_buttons)} unique close button candidates")
            
            # Try clicking the top 3 candidates
            for i, button in enumerate(unique_buttons[:3]):
                x, y = button['coordinates']
                confidence = button['confidence']
                method = button['method']
                
                self.logger.info(f"Attempting to click close button #{i+1} at ({x}, {y}) "
                               f"with confidence {confidence:.1f} (method: {method})")
                
                if self.safe_click(x, y):
                    # Wait a moment to see if window closed
                    time.sleep(1)
                    
                    # Take another screenshot to verify if window closed
                    verify_screenshot = self.take_screenshot("verify_close.png")
                    if verify_screenshot:
                        # Simple verification - if the close button area changed significantly,
                        # the window likely closed
                        verification_buttons = self.detect_close_button_by_shape(verify_screenshot)
                        
                        # If we find significantly fewer close buttons, assume success
                        if len(verification_buttons) < len(unique_buttons) * 0.7:
                            self.logger.info(f"✓ Successfully closed window using {method}")
                            return True
                        
                        # Clean up verification screenshot
                        try:
                            os.remove(verify_screenshot)
                        except:
                            pass
                
                # If first attempt didn't work, try double-click
                if i == 0:
                    self.logger.info("Trying double-click on the same button...")
                    if self.safe_click(x, y, double_click=True):
                        time.sleep(1)
                        self.logger.info("✓ Successfully closed window using double-click")
                        return True
            
            self.logger.warning("Failed to close window by clicking close buttons")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in find_and_click_close_button: {e}")
            return False
    
    def close_app_by_process_name(self, app_name: str) -> bool:
        """Close app by killing its process (fallback method)"""
        try:
            process_names = self.config["app_process_names"].get(app_name.lower(), [])
            if not process_names:
                # Fallback: try common process name patterns
                process_names = [f"{app_name}.exe", app_name.lower(), app_name.title()]
            
            killed_any = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if any(pname.lower() in proc_name.lower() for pname in process_names):
                        proc.terminate()
                        self.logger.info(f"Terminated process: {proc_name} (PID: {proc.info['pid']})")
                        killed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return killed_any
        except Exception as e:
            self.logger.error(f"Error closing app by process name: {e}")
            return False
    
    def close_app_by_pid(self, pids: List[int]) -> bool:
        """Close app by killing specific PIDs (fallback method)"""
        try:
            killed_any = False
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                    proc.terminate()
                    self.logger.info(f"Terminated process: {proc_name} (PID: {pid})")
                    killed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return killed_any
        except Exception as e:
            self.logger.error(f"Error closing app by PID: {e}")
            return False
    
    def auto_close_app(self, app_name: str, launch_info: Dict):
        """Auto-close app after specified delay using close button detection"""
        def close_after_delay():
            try:
                delay = self.config.get("auto_close_delay", 3)
                self.logger.info(f"Auto-close scheduled for {app_name} in {delay} seconds...")
                time.sleep(delay)
                
                self.logger.info(f"Attempting to auto-close {app_name}...")
                
                # Method 1: Find and click the X close button (PRIMARY METHOD)
                if self.find_and_click_close_button():
                    self.logger.info(f"✓ Successfully closed {app_name} by clicking close button")
                    return
                
                # Method 2: Try to close by new PIDs (fallback)
                if 'new_pids' in launch_info and launch_info['new_pids']:
                    if self.close_app_by_pid(launch_info['new_pids']):
                        self.logger.info(f"✓ Successfully closed {app_name} using PID method (fallback)")
                        return
                
                # Method 3: Try to close by process name (fallback)
                if self.close_app_by_process_name(app_name):
                    self.logger.info(f"✓ Successfully closed {app_name} using process name method (fallback)")
                    return
                
                self.logger.warning(f"Failed to auto-close {app_name} using all available methods")
                
            except Exception as e:
                self.logger.error(f"Error in auto-close thread for {app_name}: {e}")
        
        # Start the auto-close in a separate thread
        if self.config.get("enable_auto_close", True):
            threading.Thread(target=close_after_delay, daemon=True).start()
    
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
        """Main method to launch an application with auto-close feature"""
        self.logger.info(f"Starting launch sequence for: {app_name}")
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_attempts}")
                
                # Get processes before launching app
                processes_before = self.get_running_processes_before_launch()
                
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
                        
                        # Get new processes after launch
                        new_processes = self.get_new_processes(processes_before)
                        new_pids = [pid for pid, name in new_processes]
                        
                        # Store launch info and schedule auto-close
                        launch_info = {
                            'new_pids': new_pids,
                            'launch_time': time.time(),
                            'launch_method': 'direct_click'
                        }
                        self.launched_apps[app_name] = launch_info
                        
                        # Schedule auto-close
                        self.auto_close_app(app_name, launch_info)
                        
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
                            
                            # Get new processes after launch
                            new_processes = self.get_new_processes(processes_before)
                            new_pids = [pid for pid, name in new_processes]
                            
                            # Store launch info and schedule auto-close
                            launch_info = {
                                'new_pids': new_pids,
                                'launch_time': time.time(),
                                'launch_method': 'search_result_click'
                            }
                            self.launched_apps[app_name] = launch_info
                            
                            # Schedule auto-close
                            self.auto_close_app(app_name, launch_info)
                            
                            return True
                    else:
                        # Fallback: Press Enter to launch first result
                        self.logger.info("Pressing Enter to launch first search result")
                        pyautogui.press('enter')
                        time.sleep(2)
                        
                        # Get new processes after launch
                        new_processes = self.get_new_processes(processes_before)
                        new_pids = [pid for pid, name in new_processes]
                        
                        # Store launch info and schedule auto-close
                        launch_info = {
                            'new_pids': new_pids,
                            'launch_time': time.time(),
                            'launch_method': 'enter_key'
                        }
                        self.launched_apps[app_name] = launch_info
                        
                        # Schedule auto-close
                        self.auto_close_app(app_name, launch_info)
                        
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
    
    def toggle_auto_close(self) -> None:
        """Toggle the auto-close feature on/off"""
        current_state = self.config.get("enable_auto_close", True)
        self.config["enable_auto_close"] = not current_state
        
        # Save to config file
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            status = "enabled" if self.config["enable_auto_close"] else "disabled"
            print(f"✓ Auto-close feature {status}")
        except Exception as e:
            self.logger.error(f"Failed to save auto-close setting: {e}")
    
    def set_auto_close_delay(self, delay: int) -> None:
        """Set the auto-close delay in seconds"""
        if delay < 1:
            print("Error: Delay must be at least 1 second")
            return
        
        self.config["auto_close_delay"] = delay
        
        # Save to config file
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            print(f"✓ Auto-close delay set to {delay} seconds")
        except Exception as e:
            self.logger.error(f"Failed to save auto-close delay: {e}")
    
    def manual_close_app(self, app_name: str) -> bool:
        """Manually close a specific app using close button detection"""
        self.logger.info(f"Attempting to manually close {app_name}...")
        
        # Try close button method first
        if self.find_and_click_close_button():
            if app_name in self.launched_apps:
                del self.launched_apps[app_name]
            print(f"✓ Manually closed {app_name} by clicking close button")
            return True
        
        # Fallback to process methods
        if app_name in self.launched_apps:
            launch_info = self.launched_apps[app_name]
            
            # Try to close by PID
            if 'new_pids' in launch_info and launch_info['new_pids']:
                if self.close_app_by_pid(launch_info['new_pids']):
                    del self.launched_apps[app_name]
                    print(f"✓ Manually closed {app_name} by PID")
                    return True
        
        # Final fallback: close by process name
        if self.close_app_by_process_name(app_name):
            if app_name in self.launched_apps:
                del self.launched_apps[app_name]
            print(f"✓ Manually closed {app_name} by process name")
            return True
        
        print(f"✗ Failed to close {app_name}")
        return False
    
    def show_status(self) -> None:
        """Show current launcher status and settings"""
        print("\n" + "="*60)
        print("LAUNCHER STATUS")
        print("="*60)
        print(f"Auto-close enabled: {self.config.get('enable_auto_close', True)}")
        print(f"Auto-close delay: {self.config.get('auto_close_delay', 3)} seconds")
        print(f"Close button search area: {int(self.config.get('close_button_search_area', 0.3) * 100)}% of screen height")
        print(f"Close button size range: {self.config.get('close_button_size_range', (10, 50))} pixels")
        print(f"Currently tracked apps: {len(self.launched_apps)}")
        
        if self.launched_apps:
            print("\nActive apps:")
            for app_name, info in self.launched_apps.items():
                launch_time = time.strftime("%H:%M:%S", time.localtime(info['launch_time']))
                print(f"  • {app_name} (launched at {launch_time} via {info['launch_method']})")
    
    def test_close_button_detection(self) -> None:
        """Test close button detection on current screen"""
        print("Testing close button detection on current screen...")
        
        # Take screenshot
        screenshot_path = self.take_screenshot("test_close_detection.png")
        if not screenshot_path:
            print("✗ Failed to take screenshot")
            return
        
        # Test shape detection
        shape_buttons = self.detect_close_button_by_shape(screenshot_path)
        print(f"Shape detection found {len(shape_buttons)} potential close buttons:")
        for i, button in enumerate(shape_buttons[:5]):  # Show top 5
            x, y = button['coordinates']
            confidence = button['confidence']
            method = button['method']
            print(f"  {i+1}. Position: ({x}, {y}), Confidence: {confidence:.1f}, Method: {method}")
        
        # Test OCR detection
        ocr_buttons = self.detect_close_button_by_ocr(screenshot_path)
        print(f"\nOCR detection found {len(ocr_buttons)} potential close buttons:")
        for i, button in enumerate(ocr_buttons[:5]):  # Show top 5
            x, y = button['coordinates']
            confidence = button['confidence']
            symbol = button.get('symbol', 'unknown')
            print(f"  {i+1}. Position: ({x}, {y}), Confidence: {confidence:.1f}, Symbol: '{symbol}'")
        
        # Test combined detection
        all_buttons = shape_buttons + ocr_buttons
        unique_buttons = self.remove_duplicate_close_buttons(all_buttons)
        unique_buttons.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"\nCombined detection found {len(unique_buttons)} unique close buttons:")
        for i, button in enumerate(unique_buttons[:3]):  # Show top 3
            x, y = button['coordinates']
            confidence = button['confidence']
            method = button['method']
            print(f"  {i+1}. Position: ({x}, {y}), Confidence: {confidence:.1f}, Method: {method}")
        
        if unique_buttons:
            response = input(f"\nWould you like to test clicking the best candidate at ({unique_buttons[0]['coordinates'][0]}, {unique_buttons[0]['coordinates'][1]})? (y/n): ")
            if response.lower() == 'y':
                x, y = unique_buttons[0]['coordinates']
                if self.safe_click(x, y):
                    print("✓ Test click completed")
                else:
                    print("✗ Test click failed")
        else:
            print("\n✗ No close buttons detected to test")
    
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
        """Interactive mode for launching applications with auto-close features"""
        print("\n" + "="*60)
        print("ADVANCED APP LAUNCHER - INTERACTIVE MODE")
        print("="*60)
        print("Commands:")
        print("  • Type app name to launch (e.g., 'settings', 'chrome', 'calculator')")
        print("  • 'list' - Show all available apps")
        print("  • 'add' - Add a new app")
        print("  • 'status' - Show launcher status and settings")
        print("  • 'toggle' - Toggle auto-close feature on/off")
        print("  • 'delay <seconds>' - Set auto-close delay (e.g., 'delay 5')")
        print("  • 'close <app>' - Manually close a specific app")
        print("  • 'test' - Test close button detection on current screen")
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
                
                elif command == 'status':
                    self.show_status()
                
                elif command == 'toggle':
                    self.toggle_auto_close()
                
                elif command == 'test':
                    self.test_close_button_detection()
                
                elif command.startswith('delay '):
                    try:
                        delay_str = command.split(' ')[1]
                        delay = int(delay_str)
                        self.set_auto_close_delay(delay)
                    except (IndexError, ValueError):
                        print("Error: Use format 'delay <seconds>' (e.g., 'delay 5')")
                
                elif command.startswith('close '):
                    try:
                        app_name = command.split(' ', 1)[1]
                        self.manual_close_app(app_name)
                    except IndexError:
                        print("Error: Use format 'close <app_name>' (e.g., 'close calculator')")
                
                elif command == 'help':
                    print("\nCommands:")
                    print("  • Type app name to launch")
                    print("  • 'list' - Show available apps")
                    print("  • 'add' - Add new app")
                    print("  • 'status' - Show launcher status")
                    print("  • 'toggle' - Toggle auto-close")
                    print("  • 'delay <seconds>' - Set auto-close delay")
                    print("  • 'close <app>' - Manually close app")
                    print("  • 'test' - Test close button detection")
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
                    
                    auto_close_status = "enabled" if self.config.get("enable_auto_close", True) else "disabled"
                    delay = self.config.get("auto_close_delay", 3)
                    print(f"Auto-close: {auto_close_status} (delay: {delay}s) - Will close by clicking X button")
                    
                    success = self.launch_app(user_input)
                    
                    if success:
                        if self.config.get("enable_auto_close", True):
                            print(f"✓ Successfully launched {user_input} (will auto-close in {delay} seconds by clicking close button)")
                        else:
                            print(f"✓ Successfully launched {user_input} (auto-close disabled)")
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