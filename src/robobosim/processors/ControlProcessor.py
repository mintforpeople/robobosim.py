from robobosim.processors.AbstractProcessor import AbstractProcessor
from robobosim.utils.Message import Message


class ControlProcessor(AbstractProcessor):
    def __init__(self, state):
        super().__init__(state)
        self.supportedMessages = ["LOCKSTEP-STATUS", "STEP-COMPLETE"]

    def process(self, status):
        name = status["name"]
        value = status["value"]

        if name == "LOCKSTEP-STATUS":
            enabled_str = str(value.get("enabled", "False")).lower()
            self.state.lockstep_mode = enabled_str in ("true", "1", "yes")
            if "currentTick" in value:
                try:
                    self.state.current_tick = int(value["currentTick"])
                except ValueError:
                    pass
            if "fixedDeltaTime" in value:
                try:
                    self.state.fixed_delta_time = float(value["fixedDeltaTime"])
                except ValueError:
                    pass
            if "seed" in value:
                try:
                    self.state.seed = int(value["seed"])
                except ValueError:
                    pass
            self.state.lockstep_status_received = True

        elif name == "STEP-COMPLETE":
            if "tick" in value:
                try:
                    self.state.current_tick = int(value["tick"])
                except ValueError:
                    pass
            self.state.last_step_telemetry = dict(value)
            self.state.step_lock = False

    def resetSimulation(self, seed=None):
        name = "RESET-SIM"
        values = {}
        if seed is not None:
            values["seed"] = str(int(seed))
        id = self.state.getId()
        return Message(name, values, id)

    def stepSimulation(self, ticks=None, seconds=None):
        name = "STEP"
        id = self.state.getId()
        values = {"stepId": str(id)}
        if ticks is not None:
            values["ticks"] = str(max(1, int(ticks)))
        elif seconds is not None:
            fdt = self.state.fixed_delta_time if self.state.fixed_delta_time > 0 else 0.02
            computed_ticks = max(1, int(round(float(seconds) / fdt)))
            values["ticks"] = str(computed_ticks)
            values["time"] = str(float(seconds))
        else:
            values["ticks"] = "1"
        return Message(name, values, id)

    def setLockstep(self, enabled=True):
        name = "SET-LOCKSTEP"
        values = {"enabled": "true" if enabled else "false"}
        id = self.state.getId()
        return Message(name, values, id)
