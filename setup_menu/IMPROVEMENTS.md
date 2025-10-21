# Menu App Improvements - Review Summary

## Issues Found

### 1. **Menu Items Spilling Outside Box**
When the terminal height is reduced, menu items would continue to be drawn outside the menu box boundaries. The original code had a break statement (`if y_pos >= h - 1: break`) but this checked against terminal height, not the box boundaries.

### 2. **No Scrolling Support**
With many menu items in a small terminal, only the first few items were visible and there was no way to access the hidden items.

### 3. **Silent Truncation**
Items were hidden without any indication to the user that content was being truncated.

### 4. **Poor Minimum Size Handling**
The "terminal too small" message appeared at h < 5 or w < 20, which was too permissive and could still cause rendering issues.

## Improvements Implemented

### 1. **Viewport-Based Scrolling**
- Added `scroll_offset` attribute to track the viewport position
- Implemented `_calculate_visible_items()` to determine how many items fit in the current terminal size
- Items are now drawn relative to the scroll offset, ensuring only visible items are rendered
- The viewport automatically follows the current selection

### 2. **Visual Scroll Indicators**
- When scrolled down: displays "↑ More above ↑" at the top
- When more items below: displays "↓ More below ↓" at the bottom
- These indicators use the highlighted color to stand out

### 3. **Enhanced Navigation**
- **Arrow keys / j/k**: Still work for single-item navigation
- **Page Up/Page Down**: NEW - Jump through items quickly
- Scroll offset automatically adjusts to keep the current selection visible

### 4. **Better Size Validation**
- Minimum terminal size increased to 10h x 30w for better UX
- `_calculate_visible_items()` properly accounts for all UI elements:
  - Borders (2 lines)
  - Title (2 lines)
  - Spacing (2 lines)
  - Shadow (1 line)
- Returns 0 if terminal is too small, preventing crashes

### 5. **Proper State Management**
- `scroll_offset` is reset to 0 when:
  - Navigating to a submenu
  - Returning from a submenu
  - Pressing q/ESC to go back
- This prevents carrying scroll state between different menus

### 6. **Improved Error Messages**
- More informative messages when terminal is too small
- Messages are properly centered and positioned

## Technical Details

### New Methods

```python
def _calculate_visible_items(self, terminal_height: int) -> int:
    """Calculate how many menu items can fit in the terminal."""
    # Returns the maximum number of items that can be displayed
    # in the current terminal height
```

```python
def _adjust_scroll_offset(self, stdscr) -> None:
    """Adjust scroll offset to keep current selection visible."""
    # Ensures the selected item is always visible by adjusting
    # the viewport when needed
```

### Modified Drawing Logic

The `_draw_menu()` method now:
1. Calculates visible items based on terminal size
2. Draws only items within the viewport range: `[scroll_offset, scroll_offset + visible_items]`
3. Adds scroll indicators when appropriate
4. Ensures items never exceed box boundaries

### Key Formula

```python
# Items are drawn from scroll_offset to items_end
items_end = min(self.scroll_offset + visible_items, len(options))

for i in range(self.scroll_offset, items_end):
    display_index = i - self.scroll_offset
    y_pos = start_y + 3 + display_index
    # ... draw item at y_pos
```

## Testing

A test script `test_menu_scroll.py` has been created to demonstrate:
- Scrolling through 20+ menu items
- Behavior in different terminal sizes
- Scroll indicators in action
- Page Up/Down navigation

### To Test:
```bash
python3 test_menu_scroll.py
```

Then try:
1. Shrinking the terminal height to see scrolling in action
2. Using Page Up/Down to navigate quickly
3. Resizing the terminal while the menu is open
4. Navigating between menus to verify state resets

## Benefits

✅ **No more spillage**: Items stay within box boundaries  
✅ **All items accessible**: Even with 100+ items in a tiny terminal  
✅ **User feedback**: Clear indicators when content is truncated  
✅ **Smooth navigation**: Viewport follows selection automatically  
✅ **Better UX**: Page Up/Down for faster navigation  
✅ **Robust**: Handles extreme terminal sizes gracefully  

## Backward Compatibility

All existing functionality is preserved:
- Same JSON structure
- Same keyboard shortcuts (arrow keys, j/k, Enter, q/ESC)
- Same visual appearance when all items fit
- No breaking changes to the API
