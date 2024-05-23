# Import the library
from robobosim.RoboboSim import RoboboSim

# Connect to the RoboboSim
IP = "localhost"
sim = RoboboSim(IP)
sim.connect()

sim.wait(0.5)
# Get the interactable objects of the scene
objects = sim.getObjects()
if objects != None and len(objects) > 0:
    # Get the first object of the list, provided that there is at least one
    object_one = objects[0]
    print(object_one)
    # Get the object's absolute position
    loc = sim.getObjectLocation(object_one)
    print(loc["position"])
    sim.wait(0.5)

    # Move the selected object +50mm in the X axis
    pos = loc['position']
    pos["x"] += 50
    sim.setObjectLocation(object_one, loc['position'])
    sim.wait(0.5)

sim.disconnect()