# Numerical Shortcuts Enhancement

## Overview

The menu system now includes **numerical shortcuts** for quick option selection. Each menu item displays a number prefix (1), 2), 3), etc.), and pressing that number key will instantly jump to and execute that option.

## Visual Example

### Before:
```
┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│                                │
│    Upload Runtime              │  
│    Start Runtime on Boot       │  
│    Edit Configuration          │
│    Servo Calibration           │
│    Run Diagnostics             │
│    Review Logs                 │
│    Exit                        │
└────────────────────────────────┘
```

### After:
```
┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│                                │
│    1) Upload Runtime           │  <- Press '1' to execute
│    2) Start Runtime on Boot    │  <- Press '2' to execute
│    3) Edit Configuration       │  <- Press '3' to execute
│    4) Servo Calibration        │  <- Press '4' to execute
│    5) Run Diagnostics          │  <- Press '5' to execute
│    6) Review Logs              │  <- Press '6' to execute
│    7) Exit                     │  <- Press '7' to execute
└────────────────────────────────┘
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **1-9** | Jump to and execute options 1-9 |
| **0** | Jump to and execute option 10 |
| **q** or **Q** | Quit the entire program (from any menu level) |
| **b** or **B** | Go back to previous menu (does nothing at main menu) |
| **ESC** | Go back to previous menu, or quit if at main menu |
| ↑/↓ or j/k | Navigate without executing |
| Enter | Execute currently highlighted option |
| Page Up/Down | Fast navigation through long lists |

## Behavior

### Instant Execution
Unlike arrow keys which only move the highlight, **pressing a number key immediately executes that option**. This provides a fast workflow:

1. See the menu
2. Press the number
3. Option executes immediately

No need to navigate and then press Enter!

### Number Display

- **Items 1-9**: Show numbers 1-9 with keyboard shortcuts
- **Item 10**: Shows as "0)" and accessible via '0' key
- **Items 11+**: Show numbers 11, 12, etc. but no keyboard shortcuts (use arrow keys)

### Back/Quit Keys

The 'q' and 'b' keys are **reserved** for navigation:
- They will **not** trigger menu options
- **'q'** = always quit the entire program (from any menu level)
- **'b'** = always go back one menu level (does nothing at main menu)
- **'ESC'** = go back one level, or quit if at main menu
- This ensures you can always escape from any menu

## Examples

### Quick Workflow
```bash
# User wants to run diagnostics
# Opens menu -> Sees "5) Run Diagnostics"
# Presses '5' -> Diagnostics run immediately
```

### Navigation vs Execution
```bash
# Arrow keys: Highlight only (no execution)
Press ↓ → Highlight moves to option 2
Press ↓ → Highlight moves to option 3
Press Enter → Execute option 3

# Number keys: Instant execution
Press '3' → Option 3 executes immediately
```

### Scrolling with Numbers
```bash
# Menu has 20 items, only 5 visible at a time
# Currently showing items 1-5

Press '7' → Scrolls to show item 7 and executes it
Press '2' → Scrolls back to show item 2 and executes it
```

## Technical Details

### Implementation

The enhancement adds:

1. **Number prefix rendering**: Each menu item gets a number prefix during drawing
2. **Key handler extension**: Handles keys '0'-'9' in `_handle_key_input()`
3. **Auto-execution**: When a number key is pressed, both highlights and executes
4. **Reserved keys**: 'q' and 'b' are explicitly reserved for navigation

### Code Changes

```python
# In _draw_menu():
if i < 9:
    number_prefix = f"{i + 1}) "
elif i == 9:
    number_prefix = "0) "
else:
    number_prefix = f"{i + 1}) "  # Show number but no keyboard shortcut

labeled_item = number_prefix + label

# In _handle_key_input():
elif ord("1") <= key <= ord("9"):
    target_index = key - ord("1")
    if target_index < len(options):
        self.current_index = target_index
        self._adjust_scroll_offset(stdscr)
        self._execute_option(options[self.current_index])
```

### Viewport Integration

Number shortcuts work seamlessly with scrolling:
- Pressing a number automatically scrolls to show that item
- The `_adjust_scroll_offset()` ensures the selected item is visible
- Then executes immediately

## Menu JSON Updates

**No changes needed!** The numerical shortcuts work with your existing JSON menu definitions. The numbers are added automatically at render time.

Your existing menus like:
```json
{
  "main": {
    "title": "Spotmicro Setup Tool",
    "options": [
      {
        "label": "Upload Runtime",
        "action": "submenu",
        "target": "upload_runtime"
      },
      ...
    ]
  }
}
```

Will automatically display as:
```
1) Upload Runtime
2) Start Runtime on Boot
...
```

## Testing

Run the test script:
```bash
python3 test_menu_scroll.py
```

Try these interactions:
1. Press '1' → Instantly executes option 1
2. Press '5' → Instantly executes option 5
3. Navigate to submenu → Press 'q' → Quits entire program
4. Navigate to submenu → Press 'b' → Goes back to previous menu
5. Press 'ESC' → Goes back one level (or quits at main menu)
6. Use arrows → Navigate without executing
7. Press Enter → Execute highlighted option

## Benefits

✅ **Faster navigation** - One keypress instead of arrow+enter  
✅ **Visual clarity** - Numbers make options easy to reference  
✅ **Muscle memory** - Consistent numbering across all menus  
✅ **Backward compatible** - Existing workflows still work  
✅ **Smart defaults** - q/b reserved for navigation  
✅ **Scrolling aware** - Works seamlessly with viewport scrolling  

## Edge Cases

### More than 10 items
- Items 1-10 have keyboard shortcuts (1-9, 0)
- Items 11+ show numbers but require arrow keys
- This is intentional to keep the interface simple

### Reserved letters in labels
- Labels can still contain 'q' or 'b' in the text
- Only bare 'q' or 'b' keypresses trigger navigation
- Labels like "Quit" or "Back" work fine with numerical shortcuts

### Rapid pressing
- Each number press fully executes before accepting the next
- Prevents accidental double-execution
- Clean state management between actions
