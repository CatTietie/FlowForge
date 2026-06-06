from typing import Optional


class ProcessEngineError(Exception):
    pass


class ProcessEngine:
    """Parses process definition JSON and drives state transitions."""

    def __init__(self, definition: dict):
        self.nodes = {n["id"]: n for n in definition["nodes"]}
        self.edges = definition["edges"]
        self._validate_definition()

    def _validate_definition(self):
        start_nodes = [n for n in self.nodes.values() if n["type"] == "start"]
        if len(start_nodes) != 1:
            raise ProcessEngineError("Process must have exactly one start node")
        end_nodes = [n for n in self.nodes.values() if n["type"] == "end"]
        if len(end_nodes) < 1:
            raise ProcessEngineError("Process must have at least one end node")

    def get_start_node_id(self) -> str:
        for node in self.nodes.values():
            if node["type"] == "start":
                return node["id"]
        raise ProcessEngineError("No start node found")

    def get_next_node_id(self, current_node_id: str) -> Optional[str]:
        for edge in self.edges:
            if edge["source"] == current_node_id:
                return edge["target"]
        return None

    def advance(self, current_node_id: str, decision: Optional[str] = None) -> tuple[str, str]:
        """
        Advance the process from current node.
        Returns (next_node_id, new_status).
        Status is "running", "completed", or "rejected".
        """
        current_node = self.nodes.get(current_node_id)
        if not current_node:
            raise ProcessEngineError(f"Node '{current_node_id}' not found")

        if current_node["type"] == "end":
            raise ProcessEngineError("Cannot advance past end node")

        if current_node["type"] == "approval":
            if decision is None:
                raise ProcessEngineError("Approval node requires a decision")
            if decision == "reject":
                return current_node_id, "rejected"
            if decision != "approve":
                raise ProcessEngineError(f"Invalid decision: {decision}")

        next_node_id = self.get_next_node_id(current_node_id)
        if next_node_id is None:
            raise ProcessEngineError(f"No outgoing edge from node '{current_node_id}'")

        next_node = self.nodes.get(next_node_id)
        if not next_node:
            raise ProcessEngineError(f"Target node '{next_node_id}' not found")

        if next_node["type"] == "end":
            return next_node_id, "completed"

        return next_node_id, "running"

    def get_current_assignee(self, node_id: str) -> Optional[str]:
        node = self.nodes.get(node_id)
        if node and node["type"] == "approval":
            return node.get("assignee")
        return None
