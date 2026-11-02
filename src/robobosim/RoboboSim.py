import time
from robobosim.remotelib import Remote


class RoboboSim:
    def __init__(self, ip, port=50505):
        """
        Creates a new Robobo Sim library instance.

        :param ip: The IP address of the machine running RoboboSim.
        :type ip: string
        :param port: Optional WebSocket port of RoboboSim (default 50505).
        :type port: int
        """

        self.rem = Remote(ip, port=port)

    def connect(self):
        """
        Establishes a remote connection with the Robobo Sim indicated by the IP address associated to this instance.
        """

        self.rem.wsStartup()

    def disconnect(self):
        """
        Disconnects the library from the Robobo Sim.
        """

        self.rem.disconnect()

    def wait(self, seconds):
        """
        Pauses the program for the specified simulation time.
        In True Deterministic / Lockstep Mode, this advances the simulator by the exact number
        of fixed physics ticks corresponding to `seconds` and waits for STEP-COMPLETE.
        In normal free-running mode, this falls back to `time.sleep(seconds)`.

        :param seconds: Time to wait in seconds (>0). Decimals like 0.2 are allowed.
        :type seconds: float
        """

        self.rem.wait(seconds)

    def step(self, ticks=1):
        """
        Advances the simulation by an exact number of fixed physics ticks in Lockstep Mode
        and blocks until the step completes.

        :param ticks: Number of fixed physics steps to advance (default 1 = 20ms).
        :type ticks: int
        :return: Telemetry dictionary reported by STEP-COMPLETE.
        :rtype: dict
        """

        return self.rem.step(ticks=ticks)

    def setLockstep(self, enabled=True):
        """
        Enables or disables Lockstep (True Deterministic) stepping mode in the simulator at runtime.

        :param enabled: True to enable lockstep mode, False to return to free-running mode.
        :type enabled: bool
        """

        self.rem.setLockstep(enabled=enabled)

    def resetSimulation(self, seed=None):
        """
        Resets the state of the current simulation running on RoboboSim.

        :param seed: Optional deterministic RNG seed for the new episode.
        :type seed: int
        """

        self.rem.resetSimulation(seed=seed)

    def getRobots(self):
        """
        Returns the list of available robots in the scene
        """

        return self.rem.getRobots()

    def getRobotLocation(self, robot_id):
        """
        Returns the location in world coordinates of the Robot specified by the index

        :param robot_id: The ID of the specified robot. Incremental, starting by 0.

        :type robot_id: int
        """

        return self.rem.getRobotLocation(robot_id)

    def setRobotLocation(self, robot_id, position=None, rotation=None):
        """
        Sets the location in world coordinates of the Robot specified by the index

        :param robot_id: The ID of the specified robot. Incremental, starting by 0.

        :type robot_id: int

        :param position: Optional. Dict (x,y,z) of the target global position for the robot. If not specified robot will retain position.

        :type position: dict

        :param rotation: Optional. Dict (x,y,z) of the target global rotation of the robot. If not specified robot will retain rotation.

        :type rotation: dict
        """

        self.rem.setRobotLocation(robot_id, position, rotation)

    def onNewLocation(self, callback):
        """
        Configures the callback that is called when location data is received.

        :param callback: The callback function to be called.

        :type callback: fun
        """

        self.rem.setLocationCallback(callback)

    def getObjects(self):
        """
        Returns the list of available objects in the scene
        """

        return self.rem.getObjects()

    def getObjectLocation(self, object_id):
        """
        Returns the location in world coordinates of the object specified by the ID

        :param object_id: The ID of the specified object

        :type object_id: string
        """

        return self.rem.getObjectLocation(object_id)

    def setObjectLocation(self, object_id, position=None, rotation=None):
        """
        Sets the location in world coordinates of the Object specified by the ID

        :param object_id: The ID of the specified object.

        :type object_id: string

        :param position: Optional. Dict (x,y,z) of the target global position for the robot. If not specified robot will retain position.

        :type position: dict

        :param rotation: Optional. Dict (x,y,z) of the target global rotation of the robot. If not specified robot will retain rotation.

        :type rotation: dict
        """

        self.rem.setObjectLocation(object_id, position, rotation)

    def onNewObjectLocation(self, callback):
        """
        Configures the callback that is called when object location data is received.

        :param callback: The callback function to be called.

        :type callback: fun
        """

        self.rem.setObjectLocationCallback(callback)

    def loadItem(self, robot_id):
        """
        If the AGV Robobo is placed on a proper load zone, it will load and carry the item provided by that zone on top of the robot
        """

        self.rem.loadItem(robot_id)

    def unloadItem(self, robot_id):
        """
        If the AGV Robobo is placed on a proper unload zone and is carrying a loaded item, it will drop the loaded item
        """

        self.rem.unloadItem(robot_id)

    def isRobotLoaded(self, robot_id):
        """
        Returns the boolean load status of the Robot specified by the index

        :param robot_id: The ID of the specified robot. Incremental, starting by 0.

        :type robot_id: int
        """

        return self.rem.isRobotLoaded(robot_id)

    def onNewLoaded(self, callback):
        """
        Configures the callback that is called when load status data is received.

        :param callback: The callback function to be called.

        :type callback: fun
        """

        self.rem.setLoadedCallback(callback)
