# Clock Widget

## Project overview
A minimal always-on-top clock widget for Windows with two implementations:
- `main.py` -- PyQt6 version (rounded corners, drop shadow, checkable menus)
- `main_tk.py` -- Pure tkinter version (zero external deps)

## Setup
```bash
source .venv/Scripts/activate
uv pip install PyQt6  # only needed for main.py
```

## Running
```bash
python main.py       # PyQt6 version
python main_tk.py    # tkinter version
```

## Process management
The clock runs as `pythonw.exe` (windowless Python). A single-instance mutex prevents duplicates.

```bash
# Check for running instances
tasklist //FO CSV | grep -i "pythonw"

# Kill all instances
taskkill //F //IM pythonw.exe

# Start a new instance (from project root)
source .venv/Scripts/activate && pythonw main.py &
```

## Architecture
Both versions are single-file, single-class implementations. No modules, no packages. Configuration constants live at the top of each file. The widget is a frameless, always-on-top, draggable window with a right-click context menu.

### PyQt6 version (`main.py`)
- `ClockWidget(QWidget)` with transparent outer window and styled inner QFrame
- QSS stylesheets for theming (defined as module-level constants)
- QTimer for 200ms clock refresh
- Mouse events for drag, contextMenuEvent for right-click menu

### tkinter version (`main_tk.py`)
- `ClockWidget` class wrapping a `tk.Tk` root window
- `ctypes.windll.shcore.SetProcessDpiAwareness(2)` for crisp DPI rendering
- `root.after(200, ...)` for clock refresh loop
- Event bindings for drag and right-click

## Conventions
- White-on-black theme: BG `#0a0a0a`, time `#f0f0f0`, date `#b0b0b0`
- Consolas 24pt bold for time (monospace prevents width jitter)
- Segoe UI 9pt for date
- Widget positions at top-right of screen on launch
- All functions must have docstrings with algorithm description
