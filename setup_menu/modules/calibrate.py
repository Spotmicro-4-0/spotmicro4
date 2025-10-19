#!/usr/bin/env python3
"""
SpotMicroAI Calibrate Submenu Launcher
--------------------------------------

This module can be executed standalone or as part of the setup_tool package.

Usage:
    python3 -m setup_tool.modules.calibrate

When invoked directly, it loads and runs the calibrate submenu
defined in `menus/calibrate.json`.
"""

import json
from pathlib import Path

from setup_tool.menu_app import MenuApp


def main() -> None:
    """
    Launch the calibrate submenu using MenuApp.

    Expects a `menus/calibrate.json` file with a structure like:

    {
      "calibrate_main": {
        "title": "Servo Calibration Menu",
        "options": [
          { "label": "Start Calibration", "action": "run", "command": "python3 scripts/start_calibration.py" },
          { "label": "View Servo Angles", "action": "run", "command": "python3 scripts/view_angles.py" },
          { "label": "Back", "action": "back" }
        ]
      }
    }
    """
    # Resolve path to the calibrate menu JSON
    base_dir = Path(__file__).resolve().parent.parent
    menu_path = base_dir / "menus" / "calibrate.json"

    if not menu_path.exists():
        raise FileNotFoundError(f"Missing menu file: {menu_path}")

    menus = json.loads(menu_path.read_text(encoding="utf-8"))
    app = MenuApp(menus, entry_menu="calibrate_main")
    app.run()


if __name__ == "__main__":
    main()
