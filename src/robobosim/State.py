class State:
    def __init__(self):
        self.id = 0

        self.locations = {}
        self.loaded = {}

    def getId(self):
        retId = self.id
        self.id += 1
        return retId
