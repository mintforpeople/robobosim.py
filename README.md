# robobosim.py
RoboboSim.py is the library used to directly interact with the functions exclusive to the [simulator](https://github.com/mintforpeople/robobo-programming/wiki/Unity) for the for the Robobo educational robot (http://www.theroboboproject.com) in the Python language.

## Installation
To use this library on your project, install it with pip:
```pip install robobosim```

And import it like:
```from robobosim.RoboboSim import RoboboSim```

## Basic usage
See `index.html` in the `docs` folder.

## Sample code
```python
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
```