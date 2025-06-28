import server
from aiohttp import web
from ..services.workflow_service import WorkflowService
from ..utils.openapi_utils import OpenAPISpecGenerator


class AppController:
    def __init__(self, manager: WorkflowService):
        self.manager = manager
        self.setup_routes()

    def setup_routes(self):
        """Setup API documentation and general routes"""
        
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
        async def openapi_spec(request):
            workflows = []
            names = await self.manager.list_workflows()
            for name in names:
                workflow = await self.manager.get_workflow(name)
                workflows.append(workflow)

            generator = OpenAPISpecGenerator(workflows)
            return web.json_response(generator.generate()) 