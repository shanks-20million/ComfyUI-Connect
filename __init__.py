import server
from aiohttp import web

from .workflow_manager import WorkflowManager

WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
version = "V0.0.1"

print(f"⚡⚡⚡ Loading: FAST API ({version})")

manager = WorkflowManager()


@server.PromptServer.instance.routes.post("/fast_api/workflows")
async def save_workflow(request):
    try:
        data = await request.json()
        workflow = data["workflow"]
        name = data["name"]
        await manager.save_workflow(name, workflow)
        return web.json_response(
            {"status": "success", "message": f"Workflow '{name}' saved."}
        )
    except KeyError as e:
        return web.json_response(
            {"status": "error", "message": f"Missing key: {str(e)}"}, status=400
        )
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


@server.PromptServer.instance.routes.delete("/fast_api/workflows/{name}")
async def delete_workflow(request):
    name = request.match_info["name"]
    try:
        await manager.delete_workflow(name)
        return web.json_response(
            {"status": "success", "message": f"Workflow '{name}' deleted."}
        )
    except FileNotFoundError:
        return web.json_response(
            {"status": "error", "message": f"Workflow '{name}' not found."}, status=404
        )
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


@server.PromptServer.instance.routes.post("/workflows/{name}")
async def execute_workflow(request):
    params = await request.json()
    name = request.match_info["name"]
    try:
        result = await manager.execute_workflow(name, params)
        return web.json_response(
            {"status": "success", "workflow": name, "result": result}
        )
    except FileNotFoundError:
        return web.json_response(
            {"status": "error", "message": f"Workflow '{name}' not found."}, status=404
        )
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


@server.PromptServer.instance.routes.get("/workflows")
async def list_workflows(request):
    try:
        workflows = await manager.list_workflows()
        return web.json_response({"status": "success", "workflows": workflows})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


@server.PromptServer.instance.routes.get("/workflow/cache_nodes")
async def get_workflow(request):
    try:
        cached_nodes = manager.get_workflows_cached_nodes()
        return web.json_response({"status": "success", "nodes": cached_nodes})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


@server.PromptServer.instance.routes.get("/workflows/{name}")
async def get_workflow(request):
    name = request.match_info["name"]
    try:
        result = await manager.get_workflow(name)
        return web.json_response(
            {"status": "success", "workflow": name, "workflow": result}
        )
    except FileNotFoundError:
        return web.json_response(
            {"status": "error", "message": f"Workflow '{name}' not found."}, status=404
        )
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)
