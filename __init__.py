import server
from aiohttp import web
import socketio
import asyncio
import json, os
import folder_paths

from .workflow_manager import WorkflowManager
from .config import config
from .openapi_spec_generator import OpenAPISpecGenerator

# Custom print function for standardized logging
def connect_print(message):
    """Print with standardized format for ComfyUI-Connect logs"""
    plugin_name = "ComfyUI-Connect"
    print(f"⚡ {plugin_name} | {message}")

WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
version = "V0.0.1"

connect_print(f"Loading: ComfyUI Connect ({version})")

manager = WorkflowManager()

# ####################
# SOCKET IO
# ####################

sio = socketio.AsyncClient()


@sio.event
async def connect():
    connect_print("SocketIO client connected")


@sio.event
async def disconnect():
    connect_print("SocketIO client disconnected")


@sio.on("run")
async def on_run(data):
    connect_print(f"Received run event with data: {data}")
    taskId = data.get("taskId")
    name = data.get("name")
    params = data.get("params")
    result = await manager.execute_workflow(name, params)
    await sio.emit("return", {"taskId": taskId, "name": name, "result": result})


async def start_socketio():
    settings_path = os.path.join(os.path.dirname(folder_paths.__file__), "user", "default", "comfy.settings.json")
    try:
        if not os.path.exists(settings_path):
            connect_print(f"Settings file not found at: {settings_path}")
            connect_print(f"Gateway is disabled")
            return
            
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        connect_print(f"Error parsing settings file {settings_path}: {e}")
        connect_print(f"Gateway is disabled")
        return
    except Exception as e:
        connect_print(f"Error loading {settings_path}: {e}")
        connect_print(f"Gateway is disabled")
        return

    socket_server_url = settings.get("Connect.Gateway")
    if not socket_server_url:
        connect_print("Connect.Gateway not configured in comfy.settings.json. Disabling SocketIO.")
        return

    await sio.connect(socket_server_url)
    connect_print(f"Connected to SocketIO server at {socket_server_url}")
    await sio.wait()


async def init_socketio(app):
    asyncio.create_task(start_socketio())


server.PromptServer.instance.app.on_startup.append(init_socketio)

# ####################
# ROUTES
# ####################


@server.PromptServer.instance.routes.get("/connect")
async def index(request):
    index = f"{config.COMFY_PATH}/custom_nodes/ComfyUI-Connect/www/index.html"

    with open(index, "r") as file:
        html = file.read()

    return web.Response(text=html, content_type="text/html")


@server.PromptServer.instance.routes.get("/connect/openapi.json")
async def index(request):
    workflows = []
    names = await manager.list_workflows()
    for name in names:
        workflow = await manager.get_workflow(name)
        workflows.append(workflow)

    generator = OpenAPISpecGenerator(workflows)
    return web.json_response(generator.generate())


@server.PromptServer.instance.routes.put("/connect/workflows")
async def save_workflow(request):
    data = await request.json()
    workflow = data["workflow"]
    name = data["name"]

    connect_print(f"PUT /connect/workflows - Saving workflow {name}")
    await manager.save_workflow(name, workflow)
    return web.json_response(
        {"status": "success", "message": f"Workflow '{name}' saved."}
    )


@server.PromptServer.instance.routes.delete("/connect/workflows/{name}")
async def delete_workflow(request):
    name = request.match_info["name"]

    connect_print(f"DELETE /connect/workflows/{name} - Deleting the workflow ...")
    await manager.delete_workflow(name)
    return web.json_response(
        {"status": "success", "message": f"Workflow '{name}' deleted."}
    )


@server.PromptServer.instance.routes.post("/connect/workflows/{name}")
async def execute_workflow(request):
    params = await request.json()
    name = request.match_info["name"]

    connect_print(f"POST /connect/workflows/{name} - Running workflow ...")
    result = await manager.execute_workflow(name, params)
    return web.json_response({"status": "success", "workflow": name, "result": result})


@server.PromptServer.instance.routes.get("/connect/workflow/cache_nodes")
async def get_workflow(request):
    cached_nodes = manager.get_workflows_cached_nodes()
    return web.json_response({"status": "success", "nodes": cached_nodes})


@server.PromptServer.instance.routes.get("/connect/workflows/{name}")
async def get_workflow(request):
    name = request.match_info["name"]
    result = await manager.get_workflow(name)
    return web.json_response(
        {"status": "success", "workflow": name, "workflow": result}
    )
