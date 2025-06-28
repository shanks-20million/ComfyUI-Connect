import socketio
import asyncio
import json
import os
import folder_paths
import time

from ..utils.helpers import connect_print
from ..utils.gpu_utils import get_gpu_info, log_gpu_info
from ..config import config


class WebSocketController:
    """
    WebSocket controller for handling real-time communication.
    Routes WebSocket events to appropriate services, similar to HTTP controllers.
    """

    def __init__(self, workflow_service):
        self.sio = socketio.AsyncClient()
        self.workflow_service = workflow_service
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Configure WebSocket event handlers (like HTTP routes)"""

        @self.sio.event
        async def connect():
            connect_print("Client SocketIO connecté")

        @self.sio.event
        async def disconnect():
            connect_print("Client SocketIO déconnecté")

        @self.sio.on("run")
        async def on_run(data):
            connect_print(f"Événement 'run' reçu avec les données: {data}")
            taskId = data.get("taskId")
            name = data.get("name")
            params = data.get("params")
            result = await self.workflow_service.execute_workflow(name, params)
            await self.sio.emit(
                "return", {"taskId": taskId, "name": name, "result": result}
            )

    async def send_gpu_info(self):
        """Background task to send periodic GPU information"""
        while True:
            if self.sio.connected:
                gpu_info = get_gpu_info()
                # log_gpu_info(gpu_info)
                await self.sio.emit("gpu_info", gpu_info)
            await asyncio.sleep(config.GPU_INFO_INTERVAL)

    async def start_socket_connection(self):
        """Initialize WebSocket connection to gateway server"""
        socket_server_url = config.user_settings.get("Connect.GatewayEndpoint")
        if not socket_server_url:
            connect_print(
                "Connect.GatewayEndpoint non configuré dans comfy.settings.json. Désactivation de SocketIO."
            )
            return

        await self.sio.connect(socket_server_url)
        connect_print(f"Connecté au serveur SocketIO à {socket_server_url}")
        await self.sio.wait()

    async def initialize(self, app):
        """Initialize WebSocket tasks when application starts"""
        asyncio.create_task(self.start_socket_connection())
        asyncio.create_task(self.send_gpu_info())
