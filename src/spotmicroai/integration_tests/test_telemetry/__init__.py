"""
Test Telemetry Module

This module provides integration tests for the telemetry display system.

Files:
- test_telemetry.py - Standalone test script that demonstrates the telemetry display with simulated robot data
- ../test_telemetry.sh - Shell script to run the telemetry test on the robot

Running the Test:
    On Development Machine:
        cd src
        export PYTHONPATH=.
        python integration_tests/test_telemetry/test_telemetry.py

    On Raspberry Pi:
        cd src
        ./integration_tests/test_telemetry.sh

What the Test Does:
    The test script:
    1. Creates a TelemetryDisplay instance
    2. Generates realistic mock data for all telemetry fields
    3. Updates the display continuously with varying values
    4. Simulates walking motion, controller inputs, and servo movements
    5. Runs until you press CTRL+C

This test does NOT require physical hardware, controller connection, or Raspberry Pi.
It's purely a visual test of the telemetry display functionality.
"""
