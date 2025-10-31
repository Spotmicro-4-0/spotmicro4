#!/usr/bin/env python3
"""
CLI wrapper for the interactive inverse kinematics controller.

This module simply validates the requested corner argument and delegates
execution to the curses UI defined in ``inverse_kinematics_control``.
"""

from __future__ import annotations

import sys

from spotmicroai.spot_config.inverse_kinematics.inverse_kinematics_control import (
    CORNER_TO_SERVOS,
    main as run_control,
)


def _print_usage() -> None:
    """Display usage instructions and valid corner values."""
    valid_options = ", ".join(CORNER_TO_SERVOS.keys())
    print("Usage: inverse_kinematics.py <CORNER>")
    print(f"Valid corners: {valid_options}")


def main(argv: list[str] | None = None) -> None:
    """Entry point that validates arguments and launches the UI."""
    args = list(argv if argv is not None else sys.argv[1:])

    if len(args) != 1:
        _print_usage()
        sys.exit(1)

    corner = args[0].strip().lower()
    if corner not in CORNER_TO_SERVOS:
        print(f"Error: Invalid corner '{corner}'")
        _print_usage()
        sys.exit(1)

    run_control(corner)


if __name__ == "__main__":
    main()
