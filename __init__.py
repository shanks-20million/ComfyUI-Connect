import server
from aiohttp import web
from .workflow_manager import WorkflowManager
from .config import config
from .openapi_spec_generator import OpenAPISpecGenerator
from .utils import connect_print
from .websocket_manager import WebSocketManager

WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
version = "V0.0.1"

connect_print(f"Loading: ComfyUI Connect ({version})")

manager = WorkflowManager()
websocket_manager = WebSocketManager(manager)

async def init_socketio(app):
    await websocket_manager.initialize(app)

server.PromptServer.instance.app.on_startup.append(init_socketio)

# ####################
# ROUTES
# ####################

@server.PromptServer.instance.routes.get("/connect")
async def index(request):
    return web.Response(text='''<!doctype html>
<html>

<head>
  <meta charset="utf-8">
  <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
</head>

<body>
  <rapi-doc
    spec-url="/api/connect/openapi.json"
    theme="dark"
    show-info = 'false'
    allow-authentication ='false'
    allow-server-selection = 'false'
    theme = 'dark'
    >
  </rapi-doc>
</body>

</html>''', content_type="text/html")


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
