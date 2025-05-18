import uuid
import json
import urllib.request
import urllib.parse
import aiohttp
import base64
import asyncio
from typing import Dict, List


class ComfyUIClient:

    def __init__(self, COMFY_ENDPOINT):
        self.CLIENT_ID = str(uuid.uuid4())
        self.COMFY_ENDPOINT = COMFY_ENDPOINT
        self.ws = None
        self.session = None
        self._message_queue = asyncio.Queue()
        self._prompt_events: Dict[str, asyncio.Event] = {}
        self._listener_task = None

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(
            f"ws://{self.COMFY_ENDPOINT}/ws?clientId={self.CLIENT_ID}"
        )
        # Start the global websocket listener
        self._listener_task = asyncio.create_task(self._listen_websocket())

    async def _listen_websocket(self):
        try:
            while True:
                message = await self.ws.receive()
                if message.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(message.data)
                    # Put the message in the queue
                    await self._message_queue.put(data)
                    # If it's an executing message with no node, it means the prompt is done
                    if (
                        data["type"] == "executing"
                        and data["data"]["node"] is None
                        and "prompt_id" in data["data"]
                    ):
                        prompt_id = data["data"]["prompt_id"]
                        if prompt_id in self._prompt_events:
                            self._prompt_events[prompt_id].set()
        except Exception as e:
            print(f"WebSocket listener error: {e}")
            # Restart the listener if it fails
            self._listener_task = asyncio.create_task(self._listen_websocket())

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    async def queue_prompt(self, prompt):
        payload = {"prompt": prompt, "client_id": self.CLIENT_ID}
        data = json.dumps(payload).encode("utf-8")
        async with self.session.post(
            f"http://{self.COMFY_ENDPOINT}/prompt", data=data
        ) as response:
            return await response.json()

    async def get_image(self, filename, subfolder, folder_type):
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(params)
        async with self.session.get(
            f"http://{self.COMFY_ENDPOINT}/view?{url_values}"
        ) as response:
            image_binary = await response.read()
            image_base64 = base64.b64encode(image_binary).decode("utf-8")
            return image_base64

    async def get_history(self, prompt_id):
        async with self.session.get(
            f"http://{self.COMFY_ENDPOINT}/history/{prompt_id}"
        ) as response:
            return await response.json()

    async def run(self, prompt):
        # Create an event for this prompt
        prompt_id = (await self.queue_prompt(prompt))["prompt_id"]
        self._prompt_events[prompt_id] = asyncio.Event()

        try:
            # Wait for the prompt completion event
            await self._prompt_events[prompt_id].wait()

            output_images = {}
            history = (await self.get_history(prompt_id))[prompt_id]
            for node_id, node_output in history["outputs"].items():
                images_output = []
                if "images" in node_output:
                    for image in node_output["images"]:
                        image_data = await self.get_image(
                            image["filename"], image.get("subfolder", ""), image["type"]
                        )
                        images_output.append(image_data)
                output_images[node_id] = images_output

            return output_images
        finally:
            # Clean up the event
            del self._prompt_events[prompt_id]
