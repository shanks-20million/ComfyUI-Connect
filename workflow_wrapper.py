import re


class WorkflowWrapper(dict):
    """
    A workflow wrapper that extends a dictionary of nodes to provide
    additional functionalities such as tagging, filtering, and bypassing nodes.
    """

    def __init__(self, workflow: dict):
        super().__init__(workflow)

    def get_tagged_nodes(self, tag: str = None):
        """
        Returns a list of nodes that have at least one tag in their _meta.title.
        Each item in the result is a dict containing:
          {
            "id": <node_id>,
            "node": <node_data>,
            "tags": [list_of_detected_tags]
          }

        If a specific tag is provided, only nodes containing that tag are returned.
        """
        tagged_nodes = []
        # Regex to detect tags and capture the base tag name only (without parentheses and content)
        pattern = r"(\$[a-zA-Z0-9_-]+|#[a-zA-Z0-9_-]+|![a-zA-Z0-9_-]+)(?:\([^)]*\))?"

        for node_id, node_data in self.items():
            title = node_data.get("_meta", {}).get("title", "")
            if not title:
                continue

            found_tags = re.findall(pattern, title)
            if found_tags:
                tagged_nodes.append(
                    {"id": node_id, "node": node_data, "tags": found_tags}
                )

        if tag:
            tagged_nodes = [n for n in tagged_nodes if tag in n["tags"]]

        return tagged_nodes

    def get_node_tags(self, node_id: str):
        """
        Returns all tags for a given node, identified by node_id.
        If the node has no tags, an empty list is returned.
        """
        for tagged_node in self.get_tagged_nodes():
            if tagged_node["id"] == node_id:
                return tagged_node["tags"]
        return []

    def get_tagged_inputs(self):
        """
        Collects inputs keyed by tag_name for tags of type `$`.

        The returned dictionary has the shape:
            {
              "tag_name": {
                "input_key": "type_of_input",
                ...
              },
              ...
            }

        Parentheses logic for `$tag`:
          - $tag         => include all inputs
          - $tag()       => include none
          - $tag(a, b)   => include only 'a' and 'b'
        """
        inputs_by_tag = {}
        for tagged_node in self.get_tagged_nodes():
            node = tagged_node["node"]
            tags = tagged_node["tags"]

            for raw_tag in tags:
                tag_type, tag_name, filters, has_parentheses = self._parse_tag(raw_tag)

                if tag_type != "input":
                    continue

                if tag_name not in inputs_by_tag:
                    inputs_by_tag[tag_name] = {}

                node_inputs = node.get("inputs", {})

                # (1) No parentheses => all inputs
                if not has_parentheses:
                    for input_key, input_value in node_inputs.items():
                        inputs_by_tag[tag_name][input_key] = type(input_value).__name__

                # (2) Empty parentheses => no inputs
                elif has_parentheses and filters == []:
                    continue

                # (3) Parentheses with content => only listed inputs
                else:
                    for input_key, input_value in node_inputs.items():
                        if input_key in filters:
                            inputs_by_tag[tag_name][input_key] = type(
                                input_value
                            ).__name__

        return inputs_by_tag

    def get_tagged_outputs(self):
        """
        Returns a list of unique output tags (prefixed by '#') that have no parentheses.
        Example: #my_output is valid, but #my_output() or #my_output(a, b) is ignored.
        """
        outputs_found = set()

        for tagged_node in self.get_tagged_nodes():
            tags = tagged_node["tags"]
            for raw_tag in tags:
                tag_type, tag_name, _, has_parentheses = self._parse_tag(raw_tag)
                if tag_type == "output" and not has_parentheses:
                    outputs_found.add(tag_name)

        return list(outputs_found)

    def update_tagged_nodes_input(
        self, tag: str, input_key: str, new_value: any
    ) -> None:
        """
        Updates the value of a specific input for all nodes that have the given $tag.
        If the tag or the input_key doesn't exist, a ValueError is raised.
        """
        tagged_inputs = self.get_tagged_inputs()

        if tag not in tagged_inputs:
            raise ValueError(
                f"No inputs available for tag '{tag}'. "
                f"Ensure this tag exists and is not excluded (e.g. with '!')."
            )

        if input_key not in tagged_inputs[tag]:
            raise ValueError(
                f"The input '{input_key}' does not exist for tag '{tag}' "
                f"(possibly not in the filtered list?)."
            )

        tagged_nodes = self.get_tagged_nodes("$" + tag)
        if not tagged_nodes:
            raise ValueError(f"Could not update node: no node with tag '{tag}' found.")

        for tagged_node in tagged_nodes:
            node_id = tagged_node["id"]
            node = self[node_id]
            node_inputs = node.get("inputs", {})

            if input_key not in node_inputs:
                raise ValueError(
                    f"Could not update node: no input '{input_key}' in node with tag "
                    f"'{tag}' (node found at id {node_id})."
                )

            node_inputs[input_key] = new_value

    def bypass_nodes(self, tag: str) -> None:
        """
        Removes nodes that match a given tag (e.g., !bypass)
        and attempts to reconnect neighboring inputs/outputs in place of the removed node.
        """
        tagged_nodes = self.get_tagged_nodes(tag)

        for skip_node_data in tagged_nodes:
            skip_node_id = skip_node_data["id"]
            if not skip_node_id:
                continue

            skip_node = self[skip_node_id]

            # Remove the node from the workflow
            del self[skip_node_id]

            # Find any node that references the skipped node as an input
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

            # Re-wire the target node if possible
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
        """
        Classifies a given tag string into:
          (tag_type, tag_name, filters, has_parentheses)

        tag_type can be:
          - "internal" for !something
          - "input" for $something
          - "output" for #something
          - "invalid" for anything else

        filters contains a list of items (e.g., from $tag(a, b))
        or [] for $tag() or None if no parentheses.

        has_parentheses is a boolean indicating if parentheses were detected in the raw string.
        """
        if tag_str.startswith("!"):
            return "internal", None, [], False

        if tag_str.startswith("$"):
            tag_type = "input"
            inner_str = tag_str[1:]
        elif tag_str.startswith("#"):
            tag_type = "output"
            inner_str = tag_str[1:]
        else:
            return "invalid", None, [], False

        match = re.match(r"^([^(\s]+)(?:\(([^)]*)\))?$", inner_str)
        if not match:
            return "invalid", None, [], False

        tag_name = match.group(1)
        filters_str = match.group(2)
        has_parentheses = "(" in tag_str and ")" in tag_str

        if tag_type == "input":
            if filters_str is None:
                # $tag -> no parentheses
                return "input", tag_name, None, False
            elif filters_str == "":
                # $tag() -> empty parentheses
                return "input", tag_name, [], True
            else:
                # $tag(a, b) -> filters
                filters = [f.strip() for f in filters_str.split(",") if f.strip()]
                return "input", tag_name, filters, True

        if tag_type == "output":
            # #tag(...) -> invalid, ignore later
            if has_parentheses:
                return "invalid", None, [], False
            # #tag -> valid, no parentheses
            return "output", tag_name, None, False

        return "invalid", None, [], False
