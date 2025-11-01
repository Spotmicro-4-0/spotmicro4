#!/usr/bin/env python3
"""
Test script for the telemetry display system.

This script demonstrates the telemetry display with mock data,
useful for testing without running the full robot system.
"""

import time
import math
from spotmicroai.runtime.telemetry_controller.telemetry_controller import TelemetryDisplay
from spotmicroai.runtime.motion_controller.models.coordinate import Coordinate


def generate_mock_telemetry(t: float) -> dict:
    """Generate mock telemetry data for testing.

    Parameters
    ----------
    t : float
        Time value for generating varying test data

    Returns
    -------
    dict
        Mock telemetry data dictionary
    """
    # Simulate walking motion with sine waves
    forward = math.sin(t * 0.5) * 0.5
    rotation = math.cos(t * 0.3) * 0.3
    cycle_index = int(t * 2) % 6
    cycle_ratio = (t * 2) % 1.0

    # Simulate leg positions
    base_x = 30 + math.sin(t) * 10
    base_y = 150 + math.cos(t * 0.5) * 20
    base_z = math.sin(t * 1.5) * 15

    leg_positions = {
        'front_right': Coordinate(base_x, base_y, base_z),
        'front_left': Coordinate(-base_x, base_y, base_z),
        'rear_right': Coordinate(base_x, base_y - 5, -base_z),
        'rear_left': Coordinate(-base_x, base_y - 5, -base_z),
    }

    # Simulate controller events
    controller_events = {
        'lx': math.sin(t * 0.7) * 0.8,
        'ly': forward,
        'rz': rotation,
        'lz': 0.0,
        'hat0x': 0,
        'hat0y': 0,
        'gas': 0.0,
        'brake': 0.0,
        'a': int(t) % 5 == 0,
        'b': 0,
        'x': 0,
        'y': 0,
        'start': 0,
        'select': 0,
    }

    # Simulate servo angles
    servo_angles = {
        'front_shoulder_right': 85 + math.sin(t) * 10,
        'front_leg_right': 45 + math.cos(t * 1.2) * 15,
        'front_foot_right': 120 + math.sin(t * 0.8) * 20,
        'front_shoulder_left': 95 - math.sin(t) * 10,
        'front_leg_left': 135 - math.cos(t * 1.2) * 15,
        'front_foot_left': 60 - math.sin(t * 0.8) * 20,
        'rear_shoulder_right': 90 + math.cos(t * 0.6) * 8,
        'rear_leg_right': 40 + math.sin(t * 1.1) * 12,
        'rear_foot_right': 125 + math.cos(t * 0.9) * 18,
        'rear_shoulder_left': 90 - math.cos(t * 0.6) * 8,
        'rear_leg_left': 140 - math.sin(t * 1.1) * 12,
        'rear_foot_left': 55 - math.cos(t * 0.9) * 18,
    }

    return {
        'is_activated': True,
        'is_running': True,
        'frame_rate': 50.0,
        'loop_time_ms': 15.0 + math.sin(t * 2) * 3.0,
        'idle_time_ms': 5.0 - math.sin(t * 2) * 3.0,
        'forward_factor': forward,
        'rotation_factor': rotation,
        'lean_factor': math.sin(t * 0.4) * 25,
        'height_factor': 40 + math.cos(t * 0.3) * 10,
        'walking_speed': 10.0,
        'elapsed_time': t % 10,
        'cycle_index': cycle_index,
        'cycle_ratio': cycle_ratio,
        'controller_events': controller_events,
        'leg_positions': leg_positions,
        'servo_angles': servo_angles,
    }


def main():
    """Run the telemetry display test."""
    print("=" * 80)
    print("SpotMicroAI Telemetry Display - Test Mode")
    print("=" * 80)
    print("\nThis script demonstrates the telemetry display with simulated data.")
    print("The display will update continuously with mock robot state information.")
    print("\nPress CTRL+C to exit.\n")

    time.sleep(2)

    display = TelemetryDisplay()
    display.initialize()

    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            telemetry_data = generate_mock_telemetry(elapsed)
            display.update(telemetry_data)
            time.sleep(0.1)  # Update at 10 Hz for the test

    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Test completed. Telemetry display stopped.")
        print("=" * 80)


if __name__ == "__main__":
    main()
