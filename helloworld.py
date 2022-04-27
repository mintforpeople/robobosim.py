# Import the library
from robobosim.RoboboSim import RoboboSim

# Connect to the RoboboSim
IP = "localhost"
sim = RoboboSim(IP)
sim.connect()

sim.wait(0.5)
# Get current location and print it
loc = sim.getRobotLocation(0)
print(loc["position"])
sim.wait(0.5)

# Move the Robot -20mm in the X axis
pos = loc['position']
pos["x"] -= 20
sim.setRobotLocation(0, loc['position'])
sim.wait(0.5)

# Reset the simulation
sim.resetSimulation()

sim.disconnect()