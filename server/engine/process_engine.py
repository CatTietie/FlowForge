import operator
import re
from typing import Optional


class ProcessEngineError(Exception):
    pass


_OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

_CONDITION_RE = re.compile(r"^(\w+)\s*(>=|<=|!=|==|>|<)\s*(.+)$")


def _evaluate_condition(expression: str, form_data: dict) -> bool:
    m = _CONDITION_RE.match(expression.strip())
    if not m:
        raise ProcessEngineError(f"Invalid condition expression: {expression}")
    field, op_str, raw_value = m.group(1), m.group(2), m.group(3).strip()

    field_value = form_data.get(field)
    try:
        compare_value: float | str = float(raw_value)
        field_value = float(field_value) if field_value is not None else 0
    except (ValueError, TypeError):
        compare_value = raw_value.strip("'\"")
        field_value = str(field_value) if field_value is not None else ""

    return _OPS[op_str](field_value, compare_value)


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

    def _resolve_condition_branch(self, node_id: str, form_data: dict) -> str:
        """Evaluate outgoing edges from a condition node and return the first matching target."""
        outgoing = [e for e in self.edges if e["source"] == node_id]
        if not outgoing:
            raise ProcessEngineError(f"Condition node '{node_id}' has no outgoing edges")

        for edge in outgoing:
            condition = edge.get("condition")
            if condition and _evaluate_condition(condition, form_data):
                return edge["target"]

        # Fall through to the edge without condition (default path)
        for edge in outgoing:
            if not edge.get("condition"):
                return edge["target"]

        raise ProcessEngineError(f"No condition matched and no default edge for node '{node_id}'")

    def advance(
        self,
        current_node_id: str,
        decision: Optional[str] = None,
        form_data: Optional[dict] = None,
    ) -> tuple[str, str]:
        """
        Advance the process from current node.
        Returns (next_node_id, new_status).
        Status is "running", "completed", "rejected", or "returned".
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
            if decision == "return":
                start_id = self.get_start_node_id()
                return start_id, "returned"
            if decision != "approve":
                raise ProcessEngineError(f"Invalid decision: {decision}")

        if current_node["type"] == "condition":
            if form_data is None:
                raise ProcessEngineError("Condition node requires form_data")
            next_node_id = self._resolve_condition_branch(current_node_id, form_data)
        else:
            next_node_id = self.get_next_node_id(current_node_id)

        if next_node_id is None:
            raise ProcessEngineError(f"No outgoing edge from node '{current_node_id}'")

        next_node = self.nodes.get(next_node_id)
        if not next_node:
            raise ProcessEngineError(f"Target node '{next_node_id}' not found")

        # Auto-advance through condition nodes recursively
        if next_node["type"] == "condition":
            if form_data is None:
                raise ProcessEngineError("Condition node requires form_data")
            return self.advance(next_node_id, form_data=form_data)

        if next_node["type"] == "end":
            return next_node_id, "completed"

        return next_node_id, "running"

    def get_current_assignee(self, node_id: str) -> Optional[str]:
        node = self.nodes.get(node_id)
        if node and node["type"] == "approval":
            return node.get("assignee")
        return None

    def advance_with_path(
        self,
        current_node_id: str,
        decision: Optional[str] = None,
        form_data: Optional[dict] = None,
    ) -> tuple[str, str, list[str]]:
        """
        Same as advance() but also returns a list of intermediate condition node IDs traversed.
        Returns (next_node_id, new_status, condition_nodes_traversed).
        """
        path = []
        result_node, result_status = self._advance_tracking(current_node_id, decision, form_data, path)
        return result_node, result_status, path

    def _advance_tracking(
        self,
        current_node_id: str,
        decision: Optional[str],
        form_data: Optional[dict],
        path: list[str],
    ) -> tuple[str, str]:
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
            if decision == "return":
                start_id = self.get_start_node_id()
                return start_id, "returned"
            if decision != "approve":
                raise ProcessEngineError(f"Invalid decision: {decision}")

        if current_node["type"] == "condition":
            if form_data is None:
                raise ProcessEngineError("Condition node requires form_data")
            next_node_id = self._resolve_condition_branch(current_node_id, form_data)
        else:
            next_node_id = self.get_next_node_id(current_node_id)

        if next_node_id is None:
            raise ProcessEngineError(f"No outgoing edge from node '{current_node_id}'")

        next_node = self.nodes.get(next_node_id)
        if not next_node:
            raise ProcessEngineError(f"Target node '{next_node_id}' not found")

        if next_node["type"] == "condition":
            if form_data is None:
                raise ProcessEngineError("Condition node requires form_data")
            path.append(next_node_id)
            return self._advance_tracking(next_node_id, None, form_data, path)

        if next_node["type"] == "end":
            return next_node_id, "completed"

        return next_node_id, "running"
