# Spotmicro4 Source Code

This directory contains the source code for the Spotmicro4 robot project.

## Setup Tool

The `setup_tool` folder contains a command-line utility that can connect to the robot over WiFi and SSH. It performs various operations, including:

- Packaging the runtime code
- Deploying the packaged code to the Raspberry Pi (RPi)

To use the setup tool, navigate to the `setup_tool` directory and run the appropriate commands. Refer to the tool's documentation for detailed instructions.

## Robot Folder

The `robot` folder contains the runtime code that is packaged as an artifact and sent to the Raspberry Pi for execution on the robot.

This code includes the main application logic, controllers, and utilities necessary for the robot's operation.
