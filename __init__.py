import server
from .config import config
from .services.workflow_service import WorkflowService
from .controllers.websocket_controller import WebSocketController
from .controllers.workflow_controller import WorkflowController
from .controllers.app_controller import AppController
from .utils.helpers import connect_print

WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
version = "V0.0.1"

connect_print(f"Loading: ComfyUI Connect ({version})")

# Initialize services
manager = WorkflowService()

# Initialize controllers
websocket_controller = WebSocketController(manager)
workflow_controller = WorkflowController(manager)
app_controller = AppController(manager)

async def init_socketio(app):
    await websocket_controller.initialize(app)

server.PromptServer.instance.app.on_startup.append(init_socketio)
