# Navigation Keys - Final Behavior

## Key Bindings Summary

| Key | Behavior | Context |
|-----|----------|---------|
| **q** or **Q** | **Quit entire program** | Works from ANY menu level - always exits completely |
| **b** or **B** | **Go back one level** | Returns to previous menu (no effect at main menu) |
| **ESC** | **Context-aware back/quit** | Go back if in submenu, quit if at main menu |
| **1-9** | **Jump to option & execute** | Instantly selects and runs options 1-9 |
| **0** | **Jump to option 10 & execute** | Instantly selects and runs the 10th option |
| ↑/↓ or j/k | Navigate selection | Move highlight up/down without executing |
| Enter | Execute current selection | Runs the currently highlighted option |
| Page Up/Down | Fast navigation | Jump multiple items at once |

## Design Philosophy

### Always-Available Exit: 'q'
- **User need**: "I want to quit NOW, regardless of where I am"
- **Solution**: 'q' always quits the entire program
- **Use case**: User is 3 menus deep and wants to exit immediately

### Safe Navigation: 'b'
- **User need**: "I want to go back one step"
- **Solution**: 'b' always goes back one menu level
- **Use case**: User went into wrong submenu and wants to return

### Smart Context: 'ESC'
- **User need**: "I want the 'escape' key to do something sensible"
- **Solution**: ESC goes back if possible, quits if at main menu
- **Use case**: Standard terminal behavior - ESC = escape current context

### Quick Selection: Number Keys
- **User need**: "I can see option 3, just let me press 3"
- **Solution**: Number keys 1-9, 0 instantly execute options
- **Use case**: Fast workflow - no navigation needed

## Examples

### Scenario 1: Deep in Submenus
```
Main Menu
  └─> Upload Runtime Menu
      └─> Configuration Submenu
          └─> Advanced Options  ← You are here

Press 'q' → Exits entire program immediately
Press 'b' → Returns to Configuration Submenu
Press ESC → Returns to Configuration Submenu
```

### Scenario 2: At Main Menu
```
Main Menu  ← You are here
  1) Upload Runtime
  2) Start Runtime on Boot
  3) Edit Configuration
  ...

Press 'q' → Exits program
Press 'b' → Does nothing (already at main)
Press ESC → Exits program
Press '3' → Jumps to and executes "Edit Configuration"
```

### Scenario 3: Quick Workflow
```
User opens menu, sees:
  1) Upload Runtime
  2) Start Runtime on Boot
  3) Edit Configuration
  4) Servo Calibration
  5) Run Diagnostics

User knows they want diagnostics:
  Press '5' → Instantly runs diagnostics
  (No arrow navigation needed!)
```

## Reserved Keys

These keys will **NEVER** be captured by menu option shortcuts:

- **q** / **Q** - Reserved for quit
- **b** / **B** - Reserved for back
- **ESC** - Reserved for context-aware navigation

This means:
- Even if a menu option's label starts with 'Q' or 'B', those keys won't select it
- Use number keys (1-9, 0) to quickly select options
- Use arrow keys + Enter if the option is beyond number 10

## User Experience Goals

✅ **Speed**: Number keys provide instant execution  
✅ **Safety**: Always have a way to quit or go back  
✅ **Predictability**: 'q' always means quit, 'b' always means back  
✅ **Flexibility**: ESC provides context-aware behavior  
✅ **Discoverability**: Number prefixes show what keys do  

## Technical Implementation

```python
# In _handle_key_input():

elif key in (ord("q"), ord("Q")):
    # Always quit, regardless of menu level
    return False

elif key in (ord("b"), ord("B")):
    # Always go back one level (if possible)
    if len(self.menu_stack) > 1:
        self.menu_stack.pop()
        self.current_index = 0
        self.scroll_offset = 0

elif key == 27:  # ESC
    # Context-aware: back if submenu, quit if main
    if len(self.menu_stack) > 1:
        self.menu_stack.pop()
        self.current_index = 0
        self.scroll_offset = 0
    else:
        return False

elif ord("1") <= key <= ord("9"):
    # Number keys: instant jump + execute
    target_index = key - ord("1")
    if target_index < len(options):
        self.current_index = target_index
        self._adjust_scroll_offset(stdscr)
        self._execute_option(options[self.current_index])
```

## Comparison: Before vs After

### Before (No Number Shortcuts)
```
User workflow to select option 5:
1. Arrow down to option 5 (4 keypresses)
2. Press Enter
Total: 5 keypresses
```

### After (With Number Shortcuts)
```
User workflow to select option 5:
1. Press '5'
Total: 1 keypress
```

**80% reduction in keypresses!**

## Edge Cases Handled

✅ Pressing 'b' at main menu → Does nothing (graceful)  
✅ Pressing 'q' in deep submenu → Quits immediately (expected)  
✅ Pressing '9' when only 5 options → Ignored (safe)  
✅ Pressing ESC at main menu → Quits (standard behavior)  
✅ Pressing ESC in submenu → Goes back (standard behavior)  

## Testing Checklist

- [ ] Press 'q' from main menu → Quits
- [ ] Press 'q' from submenu → Quits (not back)
- [ ] Press 'b' from submenu → Goes back
- [ ] Press 'b' from main menu → Does nothing
- [ ] Press ESC from submenu → Goes back
- [ ] Press ESC from main menu → Quits
- [ ] Press '1' → Executes option 1 immediately
- [ ] Press '5' → Executes option 5 immediately
- [ ] Press '0' when 10+ options → Executes option 10
- [ ] Press arrow keys → Navigates without executing
