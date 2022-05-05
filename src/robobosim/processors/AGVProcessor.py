from robobosim.processors.AbstractProcessor import AbstractProcessor
from robobosim.utils.Message import Message

class AGVProcessor(AbstractProcessor):
    def __init__(self, state):
        super().__init__(state)

        self.loadedCallback = None

        self.callbacklocks = {"loaded": False }
        self.callbacks = {"loaded": None }

        self.supportedMessages = ["SIM-LOADED-ITEM"]

    def process(self, status):
        name = status["name"]
        value = status["value"]

        if (name == "SIM-LOADED-ITEM"):  #
            robot_id = int(value["id"])
            if not robot_id in self.state.loaded.keys():
                self.state.loaded[robot_id] = {}
            self.state.loaded[robot_id] = {
                "loaded" : bool(value["loaded"])
            }
            self.runCallback("loaded")

    def loadItem(self, robot_id):
        name = "SIM-LOAD-ITEM"
        values = {
            "id" : robot_id
        }
        id = self.state.getId()
        return Message(name, values, id)
    
    def unloadItem(self, robot_id):
        name = "SIM-UNLOAD-ITEM"
        values = {
            "id" : robot_id
        }
        id = self.state.getId()
        return Message(name, values, id)
