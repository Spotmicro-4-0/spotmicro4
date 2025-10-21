# setup_tool/modules/base_menu_launcher.py

import json
from pathlib import Path

from setup_app.menu_app import MenuApp


class BaseMenuLauncher:
    """
    Abstract base class for all setup_tool submenu launchers.
    """

    MENU_FILENAME = None
    ENTRY_KEY = None

    @classmethod
    def run(cls):
        if not cls.MENU_FILENAME or not cls.ENTRY_KEY:
            raise ValueError(f"{cls.__name__} must define MENU_FILENAME and ENTRY_KEY")

        base_dir = Path(__file__).resolve().parent.parent
        menu_path = base_dir / "menus" / cls.MENU_FILENAME

        if not menu_path.exists():
            raise FileNotFoundError(f"Missing menu file: {menu_path}")

        menus = json.loads(menu_path.read_text(encoding="utf-8"))
        app = MenuApp(menus, entry_menu=cls.ENTRY_KEY)
        app.run()
