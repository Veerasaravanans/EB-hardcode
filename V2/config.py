import os
import json
import logging

DEFAULT_CONFIG = {
    "screenshot_dir": "./screenshots/",
    "template_dir": "./templates/",
    "temp_dir": "./temp/",
    "ocr_confidence_threshold": 40,
    "template_match_threshold": 0.75,
    "automation_delay": 0.3,
    "max_search_time": 10,
    "auto_close_delay": 3,
    "enable_auto_close": True,
    "close_button_search_area": 0.3,
    "close_button_size_range": (10, 50),
    "app_aliases": {
        # [Same as your code, abbreviated for brevity]
        "notepad": ["notepad", "text editor", "wordpad"],
        "chrome": ["chrome", "google chrome"],
        # ...
    },
    "system_shortcuts": {
        "Windows": "win",
        "Darwin": ["cmd", "space"],
        "Linux": ["alt", "f2"]
    }
}

def load_config(config_path="launcher_config.json"):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
    else:
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logging.info(f"Created default config at {config_path}")
        except Exception as e:
            logging.error(f"Error creating config: {e}")
    return config

def save_config(config, config_path="launcher_config.json"):
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return False
