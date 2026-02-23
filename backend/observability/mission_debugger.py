from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json
import time


@dataclass
class TraceEvent:
    event_type: str
    function: str
    module: str
    timestamp: float = field(default_factory=time.time)
    args: dict[str, Any] = field(default_factory=dict)
    return_value: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    exception: str = ""
    duration_ms: float = 0.0


class MissionDebugger:
    def __init__(self, mission_id: str, patience: int, protectiveness: int):
        self.mission_id = mission_id
        self.active = False
        self.trace: list[TraceEvent] = []
        self.depth_limit = 3 if patience < 50 else 10
        self.capture_variables = protectiveness >= 50

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def record(self, event: TraceEvent) -> None:
        if self.active:
            self.trace.append(event)

    def get_call_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        last_call = None
        for event in self.trace:
            node = f"{event.module}.{event.function}"
            if event.event_type == "call":
                if last_call is not None:
                    graph.setdefault(last_call, []).append(node)
                graph.setdefault(node, [])
                last_call = node
        return graph

    def get_decision_trace(self, decision_point: str) -> list[TraceEvent]:
        key = (decision_point or "").lower()
        return [
            event
            for event in self.trace
            if key in event.function.lower() or key in event.module.lower()
        ]

    def export_trace(self, path: str | None = None) -> str:
        out_path = Path(path or f"data/debug/{self.mission_id}_trace.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(event) for event in self.trace]
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(out_path)


def get_debugger_config(patience: int, protectiveness: int) -> dict[str, Any]:
    return {
        "enabled": True,
        "auto_activate_on_fail": protectiveness >= 60,
        "trace_depth": 3 if patience < 50 else 10,
        "capture_variables": protectiveness >= 50,
        "capture_llm_prompts": protectiveness >= 70,
        "timeline_in_cockpit": True,
        "export_trace": True,
        "trace_path": "/data/debug/{mission_id}_trace.json",
    }
