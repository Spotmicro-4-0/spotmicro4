"""
Visual comparison of before/after behavior when terminal is shrunk.

BEFORE (Terminal height = 15, 10 menu items):
┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│                                │
│    Option 1                    │
│    Option 2                    │
│    Option 3                    │
│    Option 4                    │
└────────────────────────────────┘
    Option 5                        <- SPILLS OUTSIDE!
    Option 6                        <- SPILLS OUTSIDE!
    Option 7                        <- HIDDEN
    Option 8                        <- HIDDEN
    Option 9                        <- HIDDEN
    Option 10                       <- HIDDEN

Problems:
- Items 5-6 render outside the box
- Items 7-10 are completely inaccessible
- No indication that items are hidden


AFTER (Terminal height = 15, 10 menu items):
┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│                                │
│    Option 1                    │
│    Option 2                    │
│    Option 3                    │
│    Option 4                    │
│    ↓ More below ↓              │
└────────────────────────────────┘

[User scrolls down with arrow keys]

┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│    ↑ More above ↑              │
│    Option 3                    │
│    Option 4                    │
│    Option 5                    │  <- Now visible!
│    Option 6                    │  <- Now visible!
│    ↓ More below ↓              │
└────────────────────────────────┘

[User continues scrolling down]

┌────────────────────────────────┐
│      Spotmicro Setup Tool      │
│    ↑ More above ↑              │
│    Option 7                    │  <- Now visible!
│    Option 8                    │  <- Now visible!
│    Option 9                    │  <- Now visible!
│    Option 10                   │  <- Now visible!
│                                │
└────────────────────────────────┘

Benefits:
✅ All items stay within box boundaries
✅ All 10 items are accessible via scrolling
✅ Clear visual indicators show hidden content
✅ Viewport follows selection automatically
✅ Page Up/Down for fast navigation


VIEWPORT CONCEPT:
═══════════════════════════════════════════════

Menu has 10 items total:
[Item 1] [Item 2] [Item 3] [Item 4] [Item 5] [Item 6] [Item 7] [Item 8] [Item 9] [Item 10]

Terminal can show 4 items at a time:
        ┌─────────────────────┐
        │   <- VIEWPORT ->    │
        └─────────────────────┘

scroll_offset = 0:
[Item 1] [Item 2] [Item 3] [Item 4] [Item 5] [Item 6] [Item 7] [Item 8] [Item 9] [Item 10]
╰──────────────────────────╯
    Visible in viewport

scroll_offset = 3:
[Item 1] [Item 2] [Item 3] [Item 4] [Item 5] [Item 6] [Item 7] [Item 8] [Item 9] [Item 10]
                            ╰──────────────────────────╯
                                Visible in viewport

scroll_offset = 6:
[Item 1] [Item 2] [Item 3] [Item 4] [Item 5] [Item 6] [Item 7] [Item 8] [Item 9] [Item 10]
                                                        ╰──────────────────────────╯
                                                            Visible in viewport


AUTO-SCROLL BEHAVIOR:
═══════════════════════════════════════════════

When user presses ↓ and selection moves below viewport:
  scroll_offset automatically increments

When user presses ↑ and selection moves above viewport:
  scroll_offset automatically decrements

When user presses Page Down:
  current_index jumps by (visible_items - 1)
  scroll_offset adjusts to show new position

Result: Selected item always stays visible!
"""
