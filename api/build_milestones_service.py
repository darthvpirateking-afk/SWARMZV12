import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from api.build_milestones_models import (
    BuildMilestonesPromoteResponse,
    BuildMilestonesStatusResponse,
    BuildStageExecutionRecord,
    BuildStageRecord,
)


class BuildMilestonesService:
    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._data_dir / "build_milestones_state.json"

    def get_status(self) -> BuildMilestonesStatusResponse:
        state = self._read_state()
        stages = [BuildStageRecord(**entry) for entry in state["stages"]]
        history = [BuildStageExecutionRecord(**entry) for entry in state.get("history", [])]
        return BuildMilestonesStatusResponse(
            ok=True,
            current_stage=int(state["current_stage"]),
            target_stage=int(state["target_stage"]),
            total_stages=30,
            stages=stages,
            history=history,
            generated_at=datetime.now(timezone.utc),
        )

    def promote(self, target_stage: int) -> BuildMilestonesPromoteResponse:
        bounded_target = max(1, min(int(target_stage), 30))
        state = self._read_state()
        current_stage = int(state["current_stage"])
        stages = state["stages"]
        history = state.get("history", [])

        applied_stages: List[BuildStageExecutionRecord] = []
        if bounded_target <= current_stage:
            return BuildMilestonesPromoteResponse(
                ok=True,
                current_stage=current_stage,
                target_stage=current_stage,
                applied_stages=[],
                message=f"BUILD already at stage {current_stage}.",
                generated_at=datetime.now(timezone.utc),
            )

        if bounded_target > current_stage:
            for stage in range(current_stage + 1, bounded_target + 1):
                index = stage - 1
                if 0 <= index < len(stages):
                    stages[index]["status"] = "implemented"

                executed = BuildStageExecutionRecord(
                    stage=stage,
                    title=f"BUILD {stage}",
                    status="implemented",
                    executed_at=datetime.now(timezone.utc),
                )
                history.append(executed.model_dump(mode="json"))
                applied_stages.append(executed)

        state["target_stage"] = bounded_target
        state["current_stage"] = bounded_target
        state["stages"] = stages
        state["history"] = history
        self._write_state(state)

        message = f"BUILD executed stage-by-stage: {applied_stages[0].stage} through {applied_stages[-1].stage}."

        return BuildMilestonesPromoteResponse(
            ok=True,
            current_stage=bounded_target,
            target_stage=bounded_target,
            applied_stages=applied_stages,
            message=message,
            generated_at=datetime.now(timezone.utc),
        )

    def _read_state(self) -> Dict[str, object]:
        if self._state_file.exists():
            try:
                payload = json.loads(self._state_file.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    current_stage = max(1, min(int(payload.get("current_stage", 30)), 30))
                    target_stage = max(current_stage, min(int(payload.get("target_stage", 30)), 30))
                    stages = payload.get("stages")
                    history = payload.get("history")
                    if isinstance(stages, list) and len(stages) == 30:
                        return {
                            "current_stage": current_stage,
                            "target_stage": target_stage,
                            "stages": stages,
                            "history": history if isinstance(history, list) else [],
                        }
                    return {
                        "current_stage": current_stage,
                        "target_stage": target_stage,
                        "stages": self._generate_stages(current_stage=current_stage),
                        "history": history if isinstance(history, list) else [],
                    }
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        default_state = {
            "current_stage": 5,
            "target_stage": 5,
            "stages": self._generate_stages(current_stage=5),
            "history": self._seed_history(),
        }
        self._write_state(default_state)
        return default_state

    def _write_state(self, state: Dict[str, object]) -> None:
        self._state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _generate_stages(self, current_stage: int) -> List[Dict[str, object]]:
        records: List[Dict[str, object]] = []
        for stage in range(1, 31):
            if stage <= current_stage:
                status = "implemented"
            else:
                status = "pending"
            records.append(
                {
                    "stage": stage,
                    "title": f"BUILD {stage}",
                    "status": status,
                }
            )
        return records

    def _seed_history(self) -> List[Dict[str, object]]:
        seeded: List[Dict[str, object]] = []
        for stage in range(1, 6):
            seeded.append(
                BuildStageExecutionRecord(
                    stage=stage,
                    title=f"BUILD {stage}",
                    status="implemented",
                    executed_at=datetime.now(timezone.utc),
                ).model_dump(mode="json")
            )
        return seeded
