#!/usr/bin/env python3
"""
SpotMicroAI Deploy Submenu Launcher
-----------------------------------

This module can be executed standalone or as part of the setup_tool package.

Usage:
    python3 -m setup_tool.modules.deploy

When invoked directly, it loads and runs the deploy submenu
defined in `menus/deploy.json`.
"""

import json
from pathlib import Path

from setup_tool.menu_app import MenuApp


def main() -> None:
    """
    Launch the deploy submenu using MenuApp.

    Expects a `menus/deploy.json` file with a structure like:

    {
      "deploy_main": {
        "title": "Deployment Menu",
        "options": [
          { "label": "Copy Files to Robot", "action": "run", "command": "python3 scripts/deploy_package.py" },
          { "label": "Restart Services", "action": "run", "command": "sudo systemctl restart spotmicro" },
          { "label": "Back", "action": "back" }
        ]
      }
    }
    """
    # Resolve path to the deploy menu JSON
    base_dir = Path(__file__).resolve().parent.parent
    menu_path = base_dir / "menus" / "deploy.json"

    if not menu_path.exists():
        raise FileNotFoundError(f"Missing menu file: {menu_path}")

    menus = json.loads(menu_path.read_text(encoding="utf-8"))
    app = MenuApp(menus, entry_menu="deploy_main")
    app.run()


if __name__ == "__main__":
    main()
