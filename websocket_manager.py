import socketio
import asyncio
import json
import os
import folder_paths
import time

from .utils import connect_print
from .gpu_info import get_gpu_info, log_gpu_info
from .config import config

class WebSocketManager:
    def __init__(self, workflow_manager):
        self.sio = socketio.AsyncClient()
        self.workflow_manager = workflow_manager
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        """Configure les gestionnaires d'événements SocketIO"""
        
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
            result = await self.workflow_manager.execute_workflow(name, params)
            await self.sio.emit("return", {"taskId": taskId, "name": name, "result": result})
    
    async def send_gpu_info(self):
        """Tâche pour envoyer périodiquement les infos GPU"""
        while True:
            if self.sio.connected:
                gpu_info = get_gpu_info()
                # log_gpu_info(gpu_info)
                await self.sio.emit("gpu_info", gpu_info)
            await asyncio.sleep(config.GPU_INFO_INTERVAL)
    
    async def start_socket_connection(self):
        """Démarre la connexion SocketIO au serveur de passerelle"""
        settings_path = os.path.join(os.path.dirname(folder_paths.__file__), "user", "default", config.SETTINGS_FILENAME)
        try:
            if not os.path.exists(settings_path):
                connect_print(f"Fichier de paramètres non trouvé à: {settings_path}")
                connect_print(f"Passerelle désactivée")
                return
                
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            connect_print(f"Erreur lors de l'analyse du fichier de paramètres {settings_path}: {e}")
            connect_print(f"Passerelle désactivée")
            return
        except Exception as e:
            connect_print(f"Erreur lors du chargement de {settings_path}: {e}")
            connect_print(f"Passerelle désactivée")
            return

        socket_server_url = settings.get("Connect.Gateway")
        if not socket_server_url:
            connect_print("Connect.Gateway non configuré dans comfy.settings.json. Désactivation de SocketIO.")
            return

        await self.sio.connect(socket_server_url)
        connect_print(f"Connecté au serveur SocketIO à {socket_server_url}")
        await self.sio.wait()
    
    async def initialize(self, app):
        """Initialise les tâches SocketIO lorsque l'application démarre"""
        asyncio.create_task(self.start_socket_connection())
        asyncio.create_task(self.send_gpu_info()) 