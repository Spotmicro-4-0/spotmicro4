#!/bin/bash
# Create a file /usr/local/bin/startup_beep.sh
# Simple double beep on GPIO 21 (BCM numbering)
# Make sure this runs as root or with sudo privileges

GPIO=21
BEEP_DURATION=0.1  # seconds
PAUSE_BETWEEN=0.2  # seconds

# Export the GPIO if not already exported
if [ ! -d /sys/class/gpio/gpio$GPIO ]; then
    echo $GPIO > /sys/class/gpio/export
    sleep 0.1
fi

# Set direction to out
echo "out" > /sys/class/gpio/gpio$GPIO/direction

# Function to beep once
beep_once() {
    echo 1 > /sys/class/gpio/gpio$GPIO/value
    sleep $BEEP_DURATION
    echo 0 > /sys/class/gpio/gpio$GPIO/value
}

# Two short beeps
beep_once
sleep $PAUSE_BETWEEN
beep_once

# Optional: unexport to clean up (not necessary if you want GPIO to stay reserved)
# echo $GPIO > /sys/class/gpio/unexport
