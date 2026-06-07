from typing import Optional

from engine.process_engine import ProcessEngine, ProcessEngineError, _evaluate_condition, _CONDITION_RE


class ProcessSimulator:
    """Runs a process definition in memory without any DB writes.

    Delegates all state transitions to ProcessEngine.advance(), recording
    step snapshots and condition evaluation details for frontend display.
    """

    def __init__(self, definition: dict, form_data: dict,
                 decisions: list[dict] | None = None,
                 auto_approve: bool = False):
        self.engine = ProcessEngine(definition)
        self.form_data = form_data
        self.decisions = decisions or []
        self.auto_approve = auto_approve
        self.steps: list[dict] = []
        self.visited: set[str] = set()
        self._decision_index = 0

    def run(self) -> dict:
        start_id = self.engine.get_start_node_id()
        self._record_step(start_id, "running")

        current_id, status = self._do_advance(start_id)

        if status == "completed":
            self._record_step(current_id, "completed")
            return self._build_response()

        while True:
            node = self.engine.nodes[current_id]

            if node["type"] == "end":
                self._record_step(current_id, "completed")
                break

            if node["type"] == "approval":
                decision = self._get_decision(current_id)
                if decision is None:
                    self._record_step(current_id, "waiting_for_decision")
                    break

                self._record_step(current_id, "running", decision_made=decision)

                next_id, status = self._do_advance(current_id, decision=decision)

                if status == "rejected":
                    self._record_step(next_id, "rejected", decision_made=decision)
                    break
                if status == "returned":
                    self._record_step(next_id, "returned")
                    break
                if status == "completed":
                    self._record_step(next_id, "completed")
                    break

                current_id = next_id

            elif node["type"] == "condition":
                condition_evals = self._evaluate_condition_node(current_id)
                self._record_step(current_id, "running", condition_evaluations=condition_evals)

                next_id, status = self._do_advance(current_id)

                if status == "completed":
                    self._record_step(next_id, "completed")
                    break

                current_id = next_id

            else:
                self._record_step(current_id, "running")
                next_id, status = self._do_advance(current_id)

                if status == "completed":
                    self._record_step(next_id, "completed")
                    break

                current_id = next_id

        return self._build_response()

    def _do_advance(self, node_id: str, decision: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """Call engine.advance() and record any condition nodes traversed along the way.

        Before calling advance, traces the path for condition nodes that the
        engine will auto-skip, recording their evaluation details. Then delegates
        the actual branch decision to the engine.

        Raises ProcessEngineError for genuine definition errors (e.g. malformed
        condition expressions) so the API layer can return 400.
        """
        node = self.engine.nodes[node_id]

        if node["type"] != "condition":
            self._record_intermediate_conditions(node_id)

        next_id, status = self.engine.advance(
            node_id, decision=decision, form_data=self.form_data
        )

        self.visited.add(next_id)
        return next_id, status

    def _record_intermediate_conditions(self, from_node_id: str):
        """Detect and record condition nodes that engine.advance() will auto-skip.

        Walks outgoing edges from from_node_id. If the immediate target is a
        condition node, records its evaluation details, then follows the branch
        the engine would take recursively until a non-condition node is found.
        """
        immediate_target = self.engine.get_next_node_id(from_node_id)
        if immediate_target is None:
            return

        current = immediate_target
        while True:
            node = self.engine.nodes.get(current)
            if not node or node["type"] != "condition":
                break

            condition_evals = self._evaluate_condition_node(current)
            self._record_step(current, "running", condition_evaluations=condition_evals)

            try:
                next_target = self.engine._resolve_condition_branch(current, self.form_data)
            except ProcessEngineError:
                break

            current = next_target

    def _evaluate_condition_node(self, node_id: str) -> list[dict]:
        """Evaluate all outgoing condition edges and return evaluation details for display."""
        outgoing = [e for e in self.engine.edges if e["source"] == node_id]
        results = []
        for edge in outgoing:
            condition = edge.get("condition")
            if not condition:
                continue
            m = _CONDITION_RE.match(condition.strip())
            if not m:
                results.append({
                    "expression": condition,
                    "field_name": "",
                    "field_value": None,
                    "compare_value": None,
                    "operator": "",
                    "result": False,
                })
                continue

            field_name = m.group(1)
            op_str = m.group(2)
            raw_value = m.group(3).strip()
            field_value = self.form_data.get(field_name)

            try:
                result = _evaluate_condition(condition, self.form_data)
            except ProcessEngineError:
                result = False

            try:
                compare_value = float(raw_value)
            except (ValueError, TypeError):
                compare_value = raw_value.strip("'\"")

            results.append({
                "expression": condition,
                "field_name": field_name,
                "field_value": field_value,
                "compare_value": compare_value,
                "operator": op_str,
                "result": result,
            })
        return results

    def _get_decision(self, node_id: str) -> Optional[str]:
        if self.auto_approve:
            return "approve"
        if self._decision_index < len(self.decisions):
            d = self.decisions[self._decision_index]
            if d["node_id"] == node_id:
                self._decision_index += 1
                return d["decision"]
        return None

    def _record_step(self, node_id: str, status: str, *,
                     decision_made: Optional[str] = None,
                     condition_evaluations: list[dict] | None = None):
        node = self.engine.nodes.get(node_id, {})
        self.visited.add(node_id)
        self.steps.append({
            "step_index": len(self.steps),
            "node_id": node_id,
            "node_type": node.get("type", "unknown"),
            "assignee": node.get("assignee"),
            "status": status,
            "decision_made": decision_made,
            "condition_evaluations": condition_evaluations or [],
            "form_data": dict(self.form_data),
        })

    def _build_response(self) -> dict:
        all_ids = list(self.engine.nodes.keys())
        visited_ids = list(self.visited)
        unvisited_ids = [nid for nid in all_ids if nid not in self.visited]
        coverage = (len(self.visited) / len(all_ids) * 100) if all_ids else 0

        final_status = self.steps[-1]["status"] if self.steps else "unknown"

        return {
            "steps": self.steps,
            "final_status": final_status,
            "visited_node_ids": visited_ids,
            "all_node_ids": all_ids,
            "unvisited_node_ids": unvisited_ids,
            "coverage_percent": round(coverage, 1),
        }
