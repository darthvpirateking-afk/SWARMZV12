class OperatorLink:
    def __init__(self, avatar_matrix=None):
        self.avatar_matrix = avatar_matrix
        self.state = "link_idle"
        self.channels = {
            "identity_sync": False,
            "mission_sync": False,
            "cosmology_sync": False,
            "swarm_sync": False,
        }

    def initiate_link(self, state):
        if state in [
            "link_idle",
            "link_sync",
            "link_focus",
            "link_overclock",
            "link_shadow",
        ]:
            self.state = state
            return f"Link state set to {state}"
        raise ValueError("Invalid link state")

    def update_channel(self, channel, status):
        if channel in self.channels:
            self.channels[channel] = status
            return f"Channel {channel} updated to {status}"
        raise ValueError("Invalid channel")

    def get_link_state(self):
        return {
            "state": self.state,
            "channels": self.channels,
        }

    def attach_matrix(self, avatar_matrix) -> None:
        self.avatar_matrix = avatar_matrix

    def execute_command(self, command: str) -> dict:
        if self.avatar_matrix is None:
            return {"ok": False, "error": "avatar matrix unavailable"}

        cmd = str(command or "").strip()
        upper = cmd.upper()
        if not upper:
            return {"ok": False, "error": "command required"}

        if upper in {"ASCEND", "SOVEREIGN", "MONARCH", "RETURN"}:
            transitioned = self.avatar_matrix.evolution.operator_trigger(upper)
            self.avatar_matrix.current_form = self.avatar_matrix.evolution.current_form
            return {
                "ok": True,
                "command": upper,
                "transitioned": transitioned,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper.startswith("CHIP "):
            chip_id = cmd.split(" ", 1)[1].strip()
            if not chip_id:
                return {"ok": False, "error": "chip id required"}
            chip_result = self.avatar_matrix.battle_chip_engine.execute_chip(chip_id)
            return {
                "ok": bool(chip_result.get("ok")),
                "command": f"CHIP {chip_id}",
                "executed": bool(chip_result.get("executed")),
                "chip_result": chip_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper == "BURST":
            chip_result = self.avatar_matrix.battle_chip_engine.burst()
            return {
                "ok": bool(chip_result.get("ok")),
                "command": upper,
                "executed": bool(chip_result.get("executed")),
                "chip_result": chip_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper == "CHAIN":
            chip_result = self.avatar_matrix.battle_chip_engine.chain()
            return {
                "ok": bool(chip_result.get("ok")),
                "command": upper,
                "executed": bool(chip_result.get("executed")),
                "chip_result": chip_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper.startswith("SUMMON "):
            summon_id = cmd.split(" ", 1)[1].strip()
            if not summon_id:
                return {"ok": False, "error": "summon id required"}
            summon_result = self.avatar_matrix.summons.spawn(summon_id)
            return {
                "ok": bool(summon_result.get("ok")),
                "command": f"SUMMON {summon_id}",
                "executed": bool(summon_result.get("executed")),
                "summon_result": summon_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper.startswith("DISMISS "):
            summon_id = cmd.split(" ", 1)[1].strip()
            if not summon_id:
                return {"ok": False, "error": "summon id required"}
            summon_result = self.avatar_matrix.summons.dismiss(summon_id)
            return {
                "ok": bool(summon_result.get("ok")),
                "command": f"DISMISS {summon_id}",
                "executed": bool(summon_result.get("executed")),
                "summon_result": summon_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper == "LEGION":
            summon_result = self.avatar_matrix.summons.legion()
            return {
                "ok": bool(summon_result.get("ok")),
                "command": upper,
                "executed": bool(summon_result.get("executed")),
                "summon_result": summon_result,
                "current_form": self.avatar_matrix.current_form,
            }

        if upper in {"GUARD", "HUNT"}:
            summon_result = self.avatar_matrix.summons.command_all(upper)
            return {
                "ok": bool(summon_result.get("ok")),
                "command": upper,
                "executed": bool(summon_result.get("executed")),
                "summon_result": summon_result,
                "current_form": self.avatar_matrix.current_form,
            }

        return {"ok": False, "error": f"unsupported command '{cmd}'"}
