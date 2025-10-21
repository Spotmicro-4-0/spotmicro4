#!/usr/bin/env python3
"""
Test script to demonstrate menu scrolling with many items.
"""

from setup_menu.menu_app import MenuApp

# Create a test menu with many items to demonstrate scrolling
test_menus = {
    "main": {
        "title": "Scrolling Test Menu",
        "options": [
            {"label": f"Option {i+1}", "action": "run", "command": f"echo 'Selected option {i+1}'"} for i in range(20)
        ]
        + [{"label": "Submenu Test", "action": "submenu", "target": "submenu"}, {"label": "Exit", "action": "exit"}],
    },
    "submenu": {
        "title": "Submenu with Few Items",
        "options": [
            {"label": "Item A", "action": "run", "command": "echo 'Item A'"},
            {"label": "Item B", "action": "run", "command": "echo 'Item B'"},
            {"label": "Item C", "action": "run", "command": "echo 'Item C'"},
            {"label": "Back", "action": "back"},
        ],
    },
}

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MENU SCROLLING TEST")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("  - Scrolling through many menu items")
    print("  - Scroll indicators (↑ More above ↑ / ↓ More below ↓)")
    print("  - Page Up/Page Down navigation")
    print("  - Proper handling of small terminal heights")
    print("\nTry resizing your terminal to see how it responds!")
    print("\nNavigation:")
    print("  ↑/↓ or j/k : Move selection")
    print("  Page Up/Down: Fast navigation")
    print("  Enter: Select option")
    print("  q/ESC: Go back or quit")
    print("\nPress Enter to start...")
    input()

    app = MenuApp(test_menus, entry_menu="main")
    app.run()
