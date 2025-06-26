import os
import folder_paths
from .comfyui_client import ComfyUIClient


class Config:
    COMFY_ENDPOINT: str = "127.0.0.1:8000"
    WORKFLOWS_PATH: str = os.path.abspath(os.path.join(folder_paths.get_user_directory(), 'default', 'ComfyUI-Connect', 'workflows'))
    INPUT_PATH: str = os.path.abspath(folder_paths.get_input_directory())
    OUTPUT_PATH: str = os.path.abspath(folder_paths.get_output_directory())
    CLIENT = None

    async def client(self):
        if not self.CLIENT:
            self.CLIENT = ComfyUIClient(self.COMFY_ENDPOINT)
            await self.CLIENT.connect()

        return self.CLIENT


config = Config()