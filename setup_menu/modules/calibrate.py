#!/usr/bin/env python3
from setup_menu.modules.base_menu_launcher import BaseMenuLauncher


class CalibrateLauncher(BaseMenuLauncher):
    MENU_FILENAME = "calibrate.json"
    ENTRY_KEY = "calibrate_main"


def main():
    CalibrateLauncher.run()


if __name__ == "__main__":
    main()
