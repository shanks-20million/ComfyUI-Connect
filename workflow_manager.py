import os
import json
import aiofiles
import base64
import requests
from .workflow_wrapper import WorkflowWrapper
from .config import config


class WorkflowManager:
    def __init__(
        self,
    ):
        self.workflows = {}
        self.workflows_cached_nodes = []

        os.makedirs(config.WORKFLOWS_PATH, exist_ok=True)
        os.makedirs(config.INPUT_PATH, exist_ok=True)

        for filename in os.listdir(config.WORKFLOWS_PATH):
            if filename.endswith(".json"):
                file_path = os.path.join(config.WORKFLOWS_PATH, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        name = os.path.splitext(filename)[0]
                        self.workflows[name] = data
                except Exception as e:
                    print(f"Error loading file '{filename}': {e}")

        self.refresh_workflows_cached_nodes()

    def refresh_workflows_cached_nodes(self):
        workflows_cached_nodes = []

        for workflow_name, workflow_data in self.workflows.items():
            wrapper = WorkflowWrapper(workflow_data)
            cached_nodes = wrapper.get_tagged_nodes("!cache")

            for node in cached_nodes:
                workflows_cached_nodes.append(
                    {"workflow_name": workflow_name, "node": node["node"]}
                )

        self.workflows_cached_nodes = workflows_cached_nodes

    def get_cached_nodes_except(self, name: str) -> list:
        return [
            item["node"]
            for item in self.workflows_cached_nodes
            if item["workflow_name"] != name
        ]

    def get_workflows_cached_nodes(self):
        return self.workflows_cached_nodes

    async def save_workflow(self, name: str, workflow: dict) -> None:
        file_path = os.path.join(config.WORKFLOWS_PATH, f"{name}.json")
        async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
            await file.write(json.dumps(workflow))
        self.workflows[name] = workflow
        self.refresh_workflows_cached_nodes()

    async def delete_workflow(self, name: str) -> None:
        file_path = os.path.join(config.WORKFLOWS_PATH, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        self.workflows.pop(name, None)
        self.refresh_workflows_cached_nodes()

    async def execute_workflow(self, name: str, params: dict) -> dict:
        if name not in self.workflows:
            raise FileNotFoundError(f"Workflow '{name}' not found.")

        workflow = WorkflowWrapper(self.workflows[name])

        workflow.bypass_nodes("!bypass")

        key = 1000
        for node in self.get_cached_nodes_except(name):
            key += 1
            workflow[key] = node

        for tag, payload in (params or {}).items():
            if payload is False:
                workflow.bypass_nodes(tag)
            else:
                for input_name, value in payload.items():
                    if isinstance(value, dict):
                        if value.get("type") == "file":
                            try:
                                if "content" in value and value["content"]:
                                    filename = value.get("name")
                                    if not filename:
                                        raise ValueError(
                                            "File name is required with content."
                                        )

                                    file_content = base64.b64decode(value["content"])
                                    with open(
                                        os.path.join(config.INPUT_PATH, filename), "wb"
                                    ) as f:
                                        f.write(file_content)

                                elif "url" in value and value["url"]:
                                    filename = value.get("name")
                                    if not filename:
                                        filename = value["url"].split("/")[-1]

                                    response = requests.get(value["url"])
                                    response.raise_for_status()
                                    with open(
                                        os.path.join(config.INPUT_PATH, filename), "wb"
                                    ) as f:
                                        f.write(response.content)
                                else:
                                    print(
                                        f"No valid content/url for {filename}"
                                    )
                                    continue

                                workflow.update_tagged_nodes_input(
                                    tag, input_name, filename
                                )

                            except Exception as e:
                                print(
                                    f"Error writing file {filename} : {e}"
                                )
                        else:
                            # Other types ?
                            pass
                    else:
                        # Other values ?
                        pass

        images = await (await config.client()).run(workflow)
        response = {}

        for node_id, node_images in images.items():
            tags = workflow.get_node_tags(node_id)
            for tag in tags:
                response[tag] = node_images

        return response

    async def list_workflows(self) -> list:
        return list(self.workflows.keys())

    async def get_workflow(self, name: str) -> dict:
        wrapper = WorkflowWrapper(self.workflows[name])
        return {"name": name, "params": wrapper.get_tagged_inputs()}
