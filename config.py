import os
import json
import folder_paths


class Config:
    # Path configuration
    WORKFLOWS_PATH: str = os.path.abspath(
        os.path.join(
            folder_paths.get_user_directory(), "default", "ComfyUI-Connect", "workflows"
        )
    )
    INPUT_PATH: str = os.path.abspath(folder_paths.get_input_directory())
    OUTPUT_PATH: str = os.path.abspath(folder_paths.get_output_directory())
    
    # Workflow configuration
    CACHED_NODE_KEY_START: int = 1000
    
    # WebSocket configuration
    GPU_INFO_INTERVAL: float = 0.5  # seconds
    SETTINGS_FILENAME: str = "comfy.settings.json"
    
    # GPU monitoring configuration
    POWER_CONVERSION_FACTOR: float = 1000.0  # mW to W conversion
    
    # OpenAPI configuration
    OPENAPI_VERSION: str = "3.0.0"
    API_TITLE: str = "Workflow API Documentation"
    API_VERSION: str = "1.0.0"
    
    def __init__(self):
        self._user_settings = None
        self._settings_loaded = False
    
    @property
    def user_settings(self):
        """Lazy loading of user settings from comfy.settings.json"""
        if not self._settings_loaded:
            self._load_user_settings()
        return self._user_settings
    
    def _load_user_settings(self):
        """Load user settings from comfy.settings.json file"""
        self._settings_loaded = True
        settings_path = os.path.join(
            folder_paths.get_user_directory(), 
            "default", 
            self.SETTINGS_FILENAME
        )
        
        try:
            if not os.path.exists(settings_path):
                self._user_settings = {}
                return
                
            with open(settings_path, "r", encoding="utf-8") as f:
                self._user_settings = json.load(f)
        except (json.JSONDecodeError, Exception):
            self._user_settings = {}


config = Config()
