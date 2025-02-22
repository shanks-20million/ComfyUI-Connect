import re


class WorkflowWrapper(dict):
    def __init__(self, workflow: dict):
        super().__init__(workflow)

    def get_tagged_nodes(self, tag: str = None):
        tagged_nodes = []

        for node_id, node_data in self.items():
            title = node_data.get("_meta", {}).get("title", "")
            if title:
                found_tags = re.findall(r"\[(.*?)\]", title)
                if found_tags:
                    tagged_nodes.append(
                        {"id": node_id, "node": node_data, "tags": found_tags}
                    )

        if tag:
            tagged_nodes = [n for n in tagged_nodes if tag in n["tags"]]

        return tagged_nodes

    def get_node_tags(self, node_id: str):
        tagged_nodes = self.get_tagged_nodes()
        for tagged_node in tagged_nodes:
            if tagged_node["id"] == node_id:
                return tagged_node["tags"]

        return []

    def get_tagged_inputs(self):
        inputs_by_tag = {}
        tagged_nodes = self.get_tagged_nodes()

        for tagged_node in tagged_nodes:
            node = tagged_node["node"]
            tags = tagged_node["tags"]

            for raw_tag in tags:
                if raw_tag.startswith("!"):
                    continue

                tag_name, filters = self._parse_tag(raw_tag)

                if tag_name not in inputs_by_tag:
                    inputs_by_tag[tag_name] = {}

                node_inputs = node.get("inputs", {})
                for input_key, input_value in node_inputs.items():
                    if not filters or input_key in filters:
                        inputs_by_tag[tag_name][input_key] = type(input_value).__name__

        return inputs_by_tag

    def update_tagged_nodes_input(
        self, tag: str, input_key: str, new_value: any
    ) -> None:
        tagged_inputs = self.get_tagged_inputs()

        if tag not in tagged_inputs:
            raise ValueError(
                f"No inputs available for tag [{tag}]. Tag does not exist, or is excluded with '!'."
            )

        if input_key not in tagged_inputs[tag]:
            raise ValueError(
                f"The input '{input_key}' does not exist for tag [{tag}] "
                f"(perhaps it's not in the filtered list?)."
            )

        tagged_nodes = self.get_tagged_nodes(tag)
        if not tagged_nodes:
            raise ValueError(f"Could not update node, no node with tag [{tag}] found.")

        for tagged_node in tagged_nodes:
            node_id = tagged_node["id"]
            node = self[node_id]
            node_inputs = node.get("inputs", {})

            if input_key not in node_inputs:
                raise ValueError(
                    f"Could not update node, no input '{input_key}' in node with tag "
                    f"[{tag}] (node found at id {node_id})."
                )

            node_inputs[input_key] = new_value

    def bypass_nodes(self, tag: str) -> None:
        tagged_nodes = self.get_tagged_nodes(tag)

        for skip_node_data in tagged_nodes:
            skip_node_id = skip_node_data["id"]
            if not skip_node_id:
                continue

            skip_node = self[skip_node_id]

            # Supprime le noeud du workflow
            del self[skip_node_id]

            target_node_id = None
            for node_id, node_data in self.items():
                for input_value in node_data.get("inputs", {}).values():
                    if isinstance(input_value, list) and len(input_value) > 0:
                        if input_value[0] == skip_node_id:
                            target_node_id = node_id
                            break
                if target_node_id:
                    break

            if not target_node_id:
                continue

            target_node = self[target_node_id]
            for target_input_key in target_node.get("inputs", {}):
                singular_input_key = target_input_key[:-1]

                if singular_input_key in skip_node.get("inputs", {}):
                    target_node["inputs"][target_input_key] = skip_node["inputs"][
                        singular_input_key
                    ]
                    break

    @staticmethod
    def _parse_tag(tag_str: str):
        if ":" in tag_str:
            parts = tag_str.split(":", 1)
            tag_name = parts[0].strip()
            filters_str = parts[1].strip()
            filters = [f.strip() for f in filters_str.split(",") if f.strip()]
        else:
            tag_name = tag_str.strip()
            filters = []
        return tag_name, filters
