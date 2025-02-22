import os
import folder_paths
from .comfyui_client import ComfyUIClient


class Config:
    COMFY_ENDPOINT: str = "127.0.0.1:8188"
    COMFY_PATH: str = os.path.dirname(folder_paths.__file__)
    WORKFLOWS_PATH: str = os.path.join(
        os.path.dirname(folder_paths.__file__),
        "user",
        "default",
        "ComfyUI-Fast-API",
        "workflows",
    )
    INPUT_PATH: str = os.path.join(os.path.dirname(folder_paths.__file__), "input")
    CLIENT = None

    async def client(self):
        if not self.CLIENT:
            self.CLIENT = ComfyUIClient(self.COMFY_ENDPOINT)
            await self.CLIENT.connect()

        return self.CLIENT


config = Config()
