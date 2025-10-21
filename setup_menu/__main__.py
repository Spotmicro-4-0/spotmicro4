#!/usr/bin/env python3
"""
SpotMicroAI Setup Tool - Package Entrypoint

This allows the setup_tool package to be executed directly:
    python3 -m setup_tool

It simply delegates execution to setup_tool.main.main().
"""

from setup_menu.main import main

if __name__ == "__main__":
    main()
