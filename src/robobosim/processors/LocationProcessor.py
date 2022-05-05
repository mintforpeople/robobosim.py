from robobosim.processors.AbstractProcessor import AbstractProcessor
from robobosim.utils.Message import Message

class LocationProcessor(AbstractProcessor):
    def __init__(self, state):
        super().__init__(state)

        self.locationCallback = None

        self.callbacklocks = {"location": False }
        self.callbacks = {"location": None }
        self.supportedMessages = ["SIM-LOCATION"]

    def process(self, status):
        name = status["name"]
        value = status["value"]

        if (name == "SIM-LOCATION"):  #
            robot_id = int(value["id"])
            if not robot_id in self.state.locations.keys():
                self.state.locations[robot_id] = {}
            self.state.locations[robot_id] = {
                "position" : {
                    "x" : float(value["tx"]),
                    "y" : float(value["ty"]),
                    "z" : float(value["tz"])
                },

                "rotation" : {
                    "x" : float(value["rx"]),
                    "y" : float(value["ry"]),
                    "z" : float(value["rz"])
                }
            }
            self.runCallback("location")
    
    def setRobotLocation(self, robot_id, position, rotation):
        name = "SIM-LOCATION-SET"
        values = {
            "id" : robot_id,
            "position" : {},
            "rotation" : {}
        }

        if (not position is None):
            values["position"]["x"] = position["x"]
            values["position"]["y"] = position["y"]
            values["position"]["z"] = position["z"]

        if (not rotation is None):
            x,y,z = rotation
            values["rotation"]["x"] = rotation["x"]
            values["rotation"]["y"] = rotation["y"]
            values["rotation"]["z"] = rotation["z"]
    
        id = self.state.getId()
        return Message(name, values, id)

