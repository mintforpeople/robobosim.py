from robobosim.processors.AbstractProcessor import AbstractProcessor
from robobosim.utils.Message import Message

class ControlProcessor(AbstractProcessor):
    def __init__(self, state):
        super().__init__(state)

    def process(self, status):
        name = status["name"]
        value = status["value"]

    def resetSimulation(self):
        name = "RESET-SIM"
        values = {}
        id = self.state.getId()
        return Message(name, values, id)
