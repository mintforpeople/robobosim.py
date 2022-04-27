import time
from robobosim.remotelib import Remote

class RoboboSim:
    def __init__(self, ip):
        """
        Creates a new Robobo Sim library instance.

        :param ip: The IP address of the machine running RoboboSim.

        :type ip: string
        """

        self.rem = Remote(ip)

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
        Pauses the program for the specified time. After that time, next instruction is executed.

        :param seconds: Time to wait in seconds (>0). Decimals like 0.2 are allowed.

        :type seconds: float
        """

        time.sleep(seconds)

    def resetSimulation(self):
        """
        Resets the state of the current simulation running on RoboboSim
        """

        self.rem.resetSimulation()
    
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
