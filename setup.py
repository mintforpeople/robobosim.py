import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="robobosim",                     # This is the name of the package
    version="0.5",                        # The initial release version
    author="The Robobo Project",                     # Full name of the author
    author_email='info@theroboboproject.com',
    description="Robobo Sim remote control library",
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type="text/markdown",
    #repository_url="https://github.com/mintforpeople/robobosim.py",
    #packages=setuptools.find_packages(),    # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],                                      # Information to filter the project on PyPi website
    python_requires='>=3.6',                # Minimum version requirement of the package
    py_modules=["robobosim"],             # Name of the python package
    packages=setuptools.find_packages('src'),
    package_dir={'':'src'},     # Directory of the source code of the package
    #packages=setuptools.find_packages(include=['.*']),
    install_requires=['websocket-client']                     # Install other dependencies if any

)