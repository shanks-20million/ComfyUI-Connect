import os
import folder_paths
from .comfyui_client import ComfyUIClient


class Config:
    # Network configuration
    COMFY_ENDPOINT: str = "127.0.0.1:8000"
    
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
    
    CLIENT = None

    async def client(self):
        if not self.CLIENT:
            self.CLIENT = ComfyUIClient(self.COMFY_ENDPOINT)
            await self.CLIENT.connect()

        return self.CLIENT


config = Config()
