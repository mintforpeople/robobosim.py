import json
import websocket
import threading
import time
import sys

from robobosim.State import State
from robobosim.utils.ConnectionState import ConnectionState

from robobosim.processors.ControlProcessor import ControlProcessor
from robobosim.processors.LocationProcessor import LocationProcessor
from robobosim.processors.ObjectLocationProcessor import ObjectLocationProcessor
from robobosim.processors.AGVProcessor import AGVProcessor


class Remote:
    def __init__(self, ip, port=50505):
        self.ip = ip
        self.port = int(port)
        self.ws = None
        self.password = "REMOTE-SIM"
        self.state = State()
        self.processors = {"CONTROL": ControlProcessor(self.state),
                           "LOCATION": LocationProcessor(self.state),
                           "AGV": AGVProcessor(self.state),
                           "OBJ-LOCATION": ObjectLocationProcessor(self.state)}

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
            print(f"ERROR: {error}")
            self.connectionState = ConnectionState.ERROR

        def on_close(ws, status_code, msg):
            self.connectionState = ConnectionState.DISCONNECTED
            if (status_code != None):
                print(f"### closed connection [{status_code}] {msg} ###")
            else:
                print("### closed connection ###")

        self.state.lockstep_status_received = False
        self.ws = websocket.WebSocketApp(f"ws://{self.ip}:{self.port}",
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

        # Wait briefly (up to 0.25s) for the initial LOCKSTEP-STATUS handshake
        # so sim.wait() knows immediately if the simulator is in Lockstep Mode.
        handshake_deadline = time.time() + 0.25
        while not self.state.lockstep_status_received and time.time() < handshake_deadline:
            time.sleep(0.005)

    def processMessage(self, msg):
        status = json.loads(msg)
        name = status["name"]
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

    def wait(self, seconds):
        if seconds <= 0:
            return
        if self.state.lockstep_mode and self.connectionState == ConnectionState.CONNECTED:
            msg = self.processors["CONTROL"].stepSimulation(seconds=seconds)
            self.state.step_lock = True
            self.sendMessage(msg)
            while self.state.step_lock and self.connectionState == ConnectionState.CONNECTED:
                time.sleep(0.002)
        else:
            time.sleep(seconds)

    def step(self, ticks=1):
        msg = self.processors["CONTROL"].stepSimulation(ticks=ticks)
        self.state.step_lock = True
        self.sendMessage(msg)
        while self.state.step_lock and self.connectionState == ConnectionState.CONNECTED:
            time.sleep(0.002)
        return self.state.last_step_telemetry

    def setLockstep(self, enabled=True):
        self.state.lockstep_mode = bool(enabled)
        msg = self.processors["CONTROL"].setLockstep(enabled=enabled)
        self.sendMessage(msg)

    def resetSimulation(self, seed=None):
        msg = self.processors["CONTROL"].resetSimulation(seed=seed)
        self.sendMessage(msg)

    def getRobots(self):
        try:
            return self.state.locations.keys()
        except KeyError as e:
            return None

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

    def getObjects(self):
        try:
            return self.state.object_locations.keys()
        except KeyError as e:
            return None

    def getObjectLocation(self, object_id):
        try:
            return self.state.object_locations[object_id]
        except KeyError as e:
            return None

    def setObjectLocation(self, object_id, position, rotation):
        try:
            msg = self.processors["OBJ-LOCATION"].setObjectLocation(object_id, position, rotation)
            self.sendMessage(msg)
        except KeyError as e:
            pass

    def loadItem(self, robot_id):
        try:
            msg = self.processors["AGV"].loadItem(robot_id)
            self.sendMessage(msg)
        except KeyError as e:
            pass

    def unloadItem(self, robot_id):
        try:
            msg = self.processors["AGV"].unloadItem(robot_id)
            self.sendMessage(msg)
        except KeyError as e:
            pass

    def isRobotLoaded(self, robot_id):
        try:
            return self.state.loaded[robot_id]["loaded"]
        except KeyError as e:
            return None

    def setLocationCallback(self, callback):
        self.processors["LOCATION"].callbacks["location"] = callback

    def setObjectLocationCallback(self, callback):
        self.processors["OBJ-LOCATION"].callbacks["object_location"] = callback
        self.processors["OBJ-LOCATION"].callbacks["object-location"] = callback

    def setLoadedCallback(self, callback):
        self.processors["AGV"].callbacks["loaded"] = callback
