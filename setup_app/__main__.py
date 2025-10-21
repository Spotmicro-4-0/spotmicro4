#!/usr/bin/env python3
"""
SpotMicroAI Setup Tool - Package Entrypoint

This allows the connect_tool package to be executed directly:
    python3 -m connect_tool

It simply delegates execution to connect_tool.main.main().
"""

from setup_app.main import main

if __name__ == "__main__":
    main()
