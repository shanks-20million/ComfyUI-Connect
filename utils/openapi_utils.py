from ..config import config

class OpenAPISpecGenerator:
    def __init__(self, workflows: list):
        """
        Initialize the instance with the list of workflows.
        """
        self.workflows = workflows

    def map_type_to_openapi(self, type_str: str) -> dict:
        """
        Convert an internal type string ('int', 'str', 'float', 'list', etc.)
        into a dictionary describing the OpenAPI type.
        """
        mapping = {
            "int": {"type": "integer"},
            "str": {"type": "string"},
            "float": {"type": "number"},
            "list": {"type": "array", "items": {"type": "string"}},
        }
        # By default, return "string" if the type is unknown
        return mapping.get(type_str, {"type": "string"})

    def generate(self) -> dict:
        """
        Generate and return a dictionary representing the OpenAPI 3.0 specification
        based on the list of workflows passed to the constructor.
        """
        # Basic OpenAPI structure
        openapi_spec = {
            "openapi": config.OPENAPI_VERSION,
            "info": {"title": config.API_TITLE, "version": config.API_VERSION},
            "paths": {},
        }

        # For each workflow, create a route (POST) and describe its inputs/outputs
        for workflow in self.workflows:
            workflow_name = workflow["name"]

            # Build the input schema (requestBody)
            request_properties = {}
            required_inputs = []

            # Each key in "inputs" is a group (e.g. sampler, checkpoint, etc.)
            for group_name, fields in workflow["inputs"].items():
                group_properties = {}
                group_required = []

                # fields is a dict (e.g. {"seed": "int", "steps": "int", "cfg": "int"})
                for field_name, field_type in fields.items():
                    group_properties[field_name] = self.map_type_to_openapi(field_type)
                    group_required.append(field_name)

                # Schéma de l'objet (group) classique
                group_object_schema = {"type": "object", "properties": group_properties}
                if group_required:
                    group_object_schema["required"] = group_required

                # On autorise soit un objet, soit "false"
                group_schema = {
                    "oneOf": [group_object_schema, {"type": "boolean", "enum": [False]}]
                }

                request_properties[group_name] = group_schema
                required_inputs.append(group_name)

            request_schema = {"type": "object", "properties": request_properties}
            if required_inputs:
                request_schema["required"] = required_inputs

            # Build the output schema (outputs)
            response_properties = {}
            for output_name in workflow.get("outputs", []):
                response_properties[output_name] = {
                    "type": "array",
                    "items": {"type": "string"},
                }

            response_schema = {"type": "object", "properties": response_properties}

            # Add an entry to the OpenAPI "paths"
            openapi_spec["paths"][f"/api/connect/workflows/{workflow_name}"] = {
                "post": {
                    "summary": f"{workflow_name}",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": request_schema}},
                    },
                    "responses": {
                        "200": {
                            "description": "Success response",
                            "content": {
                                "application/json": {"schema": response_schema}
                            },
                        }
                    },
                }
            }

        return openapi_spec
