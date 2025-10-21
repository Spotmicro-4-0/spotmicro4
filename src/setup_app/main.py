#!/usr/bin/env python3
"""
Main entry point for the SpotMicroAI Setup Tool.

This script dynamically loads all JSON menu definition files
and merges them in memory, without writing any intermediate files.

Run:
    python3 -m connect_tool
"""

import json
from pathlib import Path

from setup_app import MenuApp


def load_menus(base_dir: Path) -> dict:
    """
    Load and merge multiple menu JSON files into a single dictionary in memory.

    Args:
        base_dir (Path): Directory containing menu files.

    Returns:
        dict: Combined menu structure.
    """
    combined: dict[str, dict] = {}

    if not base_dir.exists():
        raise FileNotFoundError(f"Menu directory not found: {base_dir}")

    json_files = sorted(base_dir.glob("*.json"))
    if not json_files:
        print(f"[WARN] No menu definitions found in {base_dir}")

    for file_path in json_files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            combined.update(data)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse {file_path}: {e}")

    return combined


def main() -> None:
    """
    Application entry point.

    1. Load all menu definition files dynamically.
    2. Combine them in memory.
    3. Start the MenuApp with entry_menu="main".
    """
    base_dir = Path(__file__).resolve().parent / "menus"

    menus = load_menus(base_dir)
    if "main" not in menus:
        raise KeyError("Missing 'main' menu in loaded definitions.")

    app = MenuApp(menus, entry_menu="main")  # Pass dict directly
    app.run()


if __name__ == "__main__":
    main()
