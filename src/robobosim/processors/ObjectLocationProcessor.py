from robobosim.processors.AbstractProcessor import AbstractProcessor
from robobosim.utils.Message import Message

class ObjectLocationProcessor(AbstractProcessor):
    def __init__(self, state):
        super().__init__(state)

        self.objectLocationCallback = None

        self.callbacklocks = {"object_location": False }
        self.callbacks = {"object_location": None }
        self.supportedMessages = ["SIM-OBJECT-LOCATION"]

    def process(self, status):
        name = status["name"]
        value = status["value"]

        if (name == "SIM-OBJECT-LOCATION"):  #
            object_id = value["object-id"]
            if not object_id in self.state.object_locations.keys():
                self.state.object_locations[object_id] = {}
            self.state.object_locations[object_id] = {
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
            self.runCallback("object_location")
    
    def setObjectLocation(self, object_id, position, rotation):
        name = "SIM-OBJECT-LOCATION-SET"
        values = {
            "object-id" : object_id,
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

