class State:
    def __init__(self):
        self.id = 0

        self.locations = {}
        self.object_locations = {}
        self.loaded = {}

        # Lockstep / True Deterministic Mode state
        self.lockstep_mode = False
        self.lockstep_status_received = False
        self.step_lock = False
        self.current_tick = 0
        self.fixed_delta_time = 0.02
        self.seed = 42
        self.last_step_telemetry = {}

    def getId(self):
        retId = self.id
        self.id += 1
        return retId
