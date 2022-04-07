import json
import websocket
import threading
import time
import sys

from robobosim.State import State
from robobosim.utils.ConnectionState import ConnectionState

from robobosim.processors.ControlProcessor import ControlProcessor
from robobosim.processors.LocationProcessor import LocationProcessor

class Remote:
    def __init__(self, ip):
        self.ip = ip
        self.ws = None
        self.password = "REMOTE-SIM"
        self.state = State()
        self.processors = {"CONTROL": ControlProcessor(self.state),
                           "LOCATION": LocationProcessor(self.state)}

        self.wsDaemon = None
        self.connectionState = ConnectionState.DISCONNECTED

        self.timeout = 3

    def disconnect(self):
        self.ws.close()
        self.connectionState = ConnectionState.DISCONNECTED

    def wsStartup(self):
        def on_open(ws):
            print("### connection established ###")
            ws.send("PASSWORD: " + self.password)
            self.connectionState = ConnectionState.CONNECTED

        def on_message(ws, message):
            self.processMessage(message)

        def on_error(ws, error):
            print(error)
            self.connectionState = ConnectionState.ERROR

        def on_close(ws):
            self.connectionState = ConnectionState.DISCONNECTED
            print("### closed connection ###")

        self.ws = websocket.WebSocketApp('ws://' + self.ip + ":50505",
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)

        self.ws.on_open = on_open

        def runWS():
            self.ws.run_forever()

        self.wsDaemon = threading.Thread(target=runWS, name='wsDaemon')
        self.wsDaemon.setDaemon(True)
        self.wsDaemon.start()

        print("Connecting to SIM")
        self.connectionState = ConnectionState.CONNECTING

        while self.connectionState == ConnectionState.CONNECTING:
            print("wait")
            time.sleep(0.5)

    def processMessage(self, msg):
        status = json.loads(msg)
        name = status["name"]
        #print(name)
        #print(status)
        value = status["value"]
        processed = False
        for key in self.processors.keys():
            if self.processors[key].canProcess(name):
                self.processors[key].process(status)
                processed = True
                break

    def sendMessage(self, msg):
        if self.connectionState == ConnectionState.CONNECTED:
            self.ws.send(msg.encode())
        else:
            sys.exit("\nError: Establish connection before sending a message")

    def resetSimulation(self):
        msg = self.processors["CONTROL"].resetSimulation()
        self.sendMessage(msg)
    
    def getRobotLocation(self, robot_id):
        try:
            return self.state.locations[robot_id]
        except KeyError as e:
            return None
    
    def setRobotLocation(self, robot_id, position, rotation):
        try:
            msg = self.processors["LOCATION"].setRobotLocation(robot_id, position, rotation)
            self.sendMessage(msg)
        except KeyError as e:
            pass

    def setLocationCallback(self, callback):
        self.processors["LOCATION"].callbacks["location"] = callback

