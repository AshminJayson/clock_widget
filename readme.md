# Always-On-Top Clock Widget

A sleek, minimal, always-on-top clock widget for Windows built with Python. Drag it anywhere on your screen -- it floats above all other windows.

Two versions included:
- **`main.py`** -- PyQt6 version with rounded corners, drop shadow, and checkable menu items
- **`main_tk.py`** -- Pure tkinter version with zero external dependencies

---

## Features

- **Always on top** -- stays visible above all windows
- **Draggable** -- click and drag anywhere to reposition
- **Right-click menu** -- toggle 12/24h format, seconds, always-on-top, or close
- **DPI-aware** -- crisp text on high-resolution displays
- **Top-right positioning** -- launches at the top-right corner of your screen
- **White-on-black theme** -- clean, minimal dark look

### PyQt6 version extras
- Rounded corners (8px border-radius)
- Subtle drop shadow
- Checkable menu items (visual check marks for active toggles)
- No taskbar entry

---

## Quick Start

### PyQt6 version (recommended)

```bash
pip install PyQt6    # or: uv pip install PyQt6
python main.py
```

### tkinter version (zero dependencies)

```bash
python main_tk.py
```

> **Requirements:** Python 3.7+ on Windows. The tkinter version uses only built-in modules. The PyQt6 version requires `PyQt6`.

---

## Usage

| Action             | How                          |
| ------------------ | ---------------------------- |
| **Move**           | Click and drag anywhere      |
| **Options menu**   | Right-click                  |
| **Toggle 12/24h**  | Right-click menu             |
| **Toggle seconds** | Right-click menu             |
| **Close**          | Right-click menu             |

---

## Configuration

Edit the constants at the top of either file:

```python
CLOCK_FORMAT_24H = True       # True for 24-hour format
SHOW_SECONDS = True           # Show/hide seconds
SHOW_DATE = True              # Show/hide date line

# Theme
BG_COLOR = "#0a0a0a"          # Background
TIME_COLOR = "#f0f0f0"        # Time text
DATE_COLOR = "#b0b0b0"        # Date text
BORDER_COLOR = "#1a1a1a"      # Border
```

---

## Troubleshooting

| Problem                       | Solution                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| `tkinter` not found           | Reinstall Python with "tcl/tk" checked, or run `sudo apt install python3-tk` on Linux |
| Blurry text (tkinter)         | The tkinter version calls `SetProcessDpiAwareness(2)` -- ensure you're on Windows 10+ |
| Widget appears behind windows | Right-click and check "Always on top" is enabled                                      |
| Can't drag the widget         | Left-click to drag (right-click opens the menu)                                       |

---

## License

MIT -- do whatever you want with it.
