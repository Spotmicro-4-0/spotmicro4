#!/usr/bin/env python3
from .base_menu_launcher import BaseMenuLauncher


class DeployLauncher(BaseMenuLauncher):
    MENU_FILENAME = "deploy.json"
    ENTRY_KEY = "deploy_main"


def main():
    DeployLauncher.run()


if __name__ == "__main__":
    main()
