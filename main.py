"""
Elegant Always-On-Top Clock Widget for Windows
A minimal, draggable, transparent clock that floats above all windows.
Built with PyQt6 for rounded corners, drop shadow, and crisp DPI rendering.
"""

import ctypes
import os
import sys
import time
import winreg

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QMenu,
    QGraphicsDropShadowEffect,
)

# ─── Configuration ──────────────────────────────────────────────
CLOCK_FORMAT_24H = True           # True for 24-hour, False for 12-hour
SHOW_SECONDS = False              # Display seconds
SHOW_DATE = True                  # Display date below time

# Theme: white on black
BG_COLOR = "#0a0a0a"              # Near-black background
TIME_COLOR = "#f0f0f0"            # White for time digits
DATE_COLOR = "#b0b0b0"            # Light grey for date
STOPWATCH_COLOR = "#6bff6b"       # Green accent for stopwatch display
BORDER_COLOR = "#1a1a1a"          # Subtle dark border
BORDER_RADIUS = 8                 # Rounded corner radius in px

# Registry key for Windows startup
_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REGISTRY_VALUE_NAME = "ClockWidget"

# ─── QSS Styles ─────────────────────────────────────────────────
CONTAINER_STYLE = f"""
    QFrame#container {{
        background-color: {BG_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS}px;
    }}
"""

TIME_LABEL_STYLE = f"""
    QLabel {{
        color: {TIME_COLOR};
        background-color: transparent;
        font-family: Consolas;
        font-size: 24pt;
        font-weight: bold;
    }}
"""

STOPWATCH_LABEL_STYLE = f"""
    QLabel {{
        color: {STOPWATCH_COLOR};
        background-color: transparent;
        font-family: Consolas;
        font-size: 24pt;
        font-weight: bold;
    }}
"""

DATE_LABEL_STYLE = f"""
    QLabel {{
        color: {DATE_COLOR};
        background-color: transparent;
        font-family: 'Segoe UI';
        font-size: 9pt;
    }}
"""

MENU_STYLE = f"""
    QMenu {{
        background-color: {BORDER_COLOR};
        color: #e0e0e0;
        border: 1px solid #333333;
        font-family: 'Segoe UI';
        font-size: 9pt;
        padding: 4px 0px;
    }}
    QMenu::item {{
        padding: 4px 20px;
    }}
    QMenu::item:selected {{
        background-color: #333333;
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background-color: #333333;
        margin: 4px 8px;
    }}
"""


class ClockWidget(QWidget):
    """
    A frameless, always-on-top clock widget with rounded corners and drop shadow.

    Algorithm:
    1. Create a transparent outer QWidget (the OS window rectangle is invisible).
    2. Nest a styled QFrame inside it with rounded corners and a drop shadow.
    3. Place time and date labels inside the frame.
    4. Use a QTimer to refresh the display every 200ms.
    5. Handle drag-to-move via mouse events, right-click via contextMenuEvent.
    6. Stopwatch mode reuses the same timer and time label with a green accent.
    7. Windows startup toggle reads/writes HKCU Run registry key.
    """

    def __init__(self):
        """
        Algorithm:
        1. Set window flags: frameless, always-on-top, tool (no taskbar entry).
        2. Set translucent background so rounded corners show through.
        3. Initialize toggle and stopwatch state as instance variables.
        4. Build the UI (container, labels, shadow) and context menu.
        5. Populate labels with current time before measuring size.
        6. Position widget at top-right of screen.
        7. Start the 200ms update timer.
        """
        super().__init__()

        # Window flags: frameless, stays on top, Tool prevents taskbar entry
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # Transparent outer widget so rounded corners aren't boxed
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Toggle state (instance vars instead of globals)
        self._clock_format_24h = CLOCK_FORMAT_24H
        self._show_seconds = SHOW_SECONDS
        self._show_date = SHOW_DATE
        self._always_on_top = True
        self._draggable = False
        self._drag_position = None

        # Stopwatch state
        self._stopwatch_running = False
        self._stopwatch_elapsed_ms = 0
        self._stopwatch_last_tick = None

        # Build widgets and context menu
        self._build_ui()
        self._build_context_menu()

        # Populate labels before measuring for position
        self._update_clock()

        # Place at top-right of screen
        self._position_top_right()

        # Start the clock refresh timer (200ms for smooth seconds)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_clock)
        self._timer.start(200)

    def _build_ui(self):
        """
        Constructs the widget tree: outer layout -> container frame -> inner
        layout -> time label + date label. Applies QSS and drop shadow.

        Algorithm:
        1. Create outer QVBoxLayout with 6px margins (room for drop shadow).
        2. Create a QFrame container with rounded-corner QSS.
        3. Attach a QGraphicsDropShadowEffect to the container.
        4. Create inner QVBoxLayout with tight margins (6h, 2v).
        5. Create time and date QLabels, style them, add to inner layout.
        """
        # Outer layout: margins give the drop shadow room to render
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)

        # Container frame: the visible dark rounded rectangle
        self._container = QFrame()
        self._container.setObjectName("container")
        self._container.setStyleSheet(CONTAINER_STYLE)

        # Drop shadow on the container
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 120))
        self._container.setGraphicsEffect(shadow)

        # Inner layout: matches tkinter padx=6, pady=2
        inner_layout = QVBoxLayout(self._container)
        inner_layout.setContentsMargins(6, 2, 6, 2)
        inner_layout.setSpacing(0)

        # Time label
        self._time_label = QLabel()
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet(TIME_LABEL_STYLE)
        inner_layout.addWidget(self._time_label)

        # Date label
        self._date_label = QLabel()
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date_label.setStyleSheet(DATE_LABEL_STYLE)
        inner_layout.addWidget(self._date_label)

        outer_layout.addWidget(self._container)

    def _build_context_menu(self):
        """
        Creates the right-click menu with checkable toggle actions, a stopwatch
        submenu, and a close action.

        Algorithm:
        1. Create a QMenu styled to match the dark theme.
        2. Add checkable actions for always-on-top, 24h format, seconds.
        3. Add checkable action for startup with Windows.
        4. Add a Stopwatch submenu with Start, Stop, Reset actions.
        5. Add a separator and a Close action.
        """
        self._context_menu = QMenu(self)
        self._context_menu.setStyleSheet(MENU_STYLE)

        # Always on top - checkable toggle
        self._topmost_action = QAction("Always on top", self)
        self._topmost_action.setCheckable(True)
        self._topmost_action.setChecked(self._always_on_top)
        self._topmost_action.triggered.connect(self._toggle_topmost)
        self._context_menu.addAction(self._topmost_action)

        # 24-hour format - checkable toggle
        self._format_action = QAction("24-hour format", self)
        self._format_action.setCheckable(True)
        self._format_action.setChecked(self._clock_format_24h)
        self._format_action.triggered.connect(self._toggle_format)
        self._context_menu.addAction(self._format_action)

        # Show seconds - checkable toggle
        self._seconds_action = QAction("Show seconds", self)
        self._seconds_action.setCheckable(True)
        self._seconds_action.setChecked(self._show_seconds)
        self._seconds_action.triggered.connect(self._toggle_seconds)
        self._context_menu.addAction(self._seconds_action)

        # Start with Windows - checkable toggle using registry
        self._startup_action = QAction("Start with Windows", self)
        self._startup_action.setCheckable(True)
        self._startup_action.setChecked(self._is_startup_enabled())
        self._startup_action.triggered.connect(self._toggle_startup)
        self._context_menu.addAction(self._startup_action)

        # Draggable - checkable toggle, off by default (locked at top-right)
        self._draggable_action = QAction("Draggable", self)
        self._draggable_action.setCheckable(True)
        self._draggable_action.setChecked(self._draggable)
        self._draggable_action.triggered.connect(self._toggle_draggable)
        self._context_menu.addAction(self._draggable_action)

        self._context_menu.addSeparator()

        # Stopwatch submenu
        stopwatch_menu = QMenu("Stopwatch", self)
        stopwatch_menu.setStyleSheet(MENU_STYLE)

        start_action = QAction("Start", self)
        start_action.triggered.connect(self._stopwatch_start)
        stopwatch_menu.addAction(start_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self._stopwatch_stop)
        stopwatch_menu.addAction(stop_action)

        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self._stopwatch_reset)
        stopwatch_menu.addAction(reset_action)

        self._context_menu.addMenu(stopwatch_menu)

        self._context_menu.addSeparator()

        # Close action
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        self._context_menu.addAction(close_action)

    def _position_top_right(self):
        """
        Places the widget at the top-right corner of the primary screen,
        respecting the taskbar.

        Algorithm:
        1. Call adjustSize() to force Qt to compute the real widget size.
        2. Get available screen geometry (excludes taskbar).
        3. Compute x = right edge - widget width - margin.
        4. Compute y = top edge + margin.
        5. Move the widget.
        """
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 8
        x = screen.right() - self.width() - margin
        y = screen.top() + margin
        self.move(x, y)

    # ── Clock / Stopwatch display ────────────────────────────────
    def _update_clock(self):
        """
        Refreshes the time label with either clock or stopwatch display.

        Algorithm:
        1. If stopwatch is running, accumulate elapsed time from monotonic clock,
           format as HH:MM:SS, display in green accent style.
        2. If stopwatch is paused (elapsed > 0 but not running), show frozen value.
        3. Otherwise, show normal clock time and date.
        """
        if self._stopwatch_running:
            # Accumulate elapsed time using monotonic clock for accuracy
            now_mono = time.monotonic()
            self._stopwatch_elapsed_ms += (now_mono - self._stopwatch_last_tick) * 1000
            self._stopwatch_last_tick = now_mono
            self._show_stopwatch_display()
            return

        if self._stopwatch_elapsed_ms > 0:
            # Paused: show frozen stopwatch value
            self._show_stopwatch_display()
            return

        # Normal clock display
        self._time_label.setStyleSheet(TIME_LABEL_STYLE)
        now = time.localtime()

        if self._clock_format_24h:
            fmt = "%H:%M:%S" if self._show_seconds else "%H:%M"
        else:
            fmt = "%I:%M:%S %p" if self._show_seconds else "%I:%M %p"

        self._time_label.setText(time.strftime(fmt, now))

        if self._show_date:
            self._date_label.setText(time.strftime("%A, %b %d %Y", now))
            self._date_label.show()
        else:
            self._date_label.hide()

    def _show_stopwatch_display(self):
        """
        Formats the accumulated stopwatch milliseconds as HH:MM:SS and
        displays it in the time label with green accent styling.

        Algorithm:
        1. Convert elapsed_ms to total seconds.
        2. Compute hours, minutes, seconds.
        3. Format as zero-padded HH:MM:SS string.
        4. Apply green stopwatch style and set text.
        5. Hide the date label (not relevant in stopwatch mode).
        """
        total_secs = int(self._stopwatch_elapsed_ms / 1000)
        hrs = total_secs // 3600
        mins = (total_secs % 3600) // 60
        secs = total_secs % 60
        self._time_label.setStyleSheet(STOPWATCH_LABEL_STYLE)
        self._time_label.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
        self._date_label.setText("Stopwatch")
        self._date_label.show()

    def _stopwatch_start(self):
        """
        Starts or resumes the stopwatch.

        Algorithm:
        1. Record current monotonic time as the tick reference.
        2. Set running flag to True.
        """
        self._stopwatch_last_tick = time.monotonic()
        self._stopwatch_running = True

    def _stopwatch_stop(self):
        """
        Pauses the stopwatch, preserving accumulated elapsed time.

        Algorithm:
        1. If running, accumulate final delta from last tick.
        2. Set running flag to False.
        """
        if self._stopwatch_running:
            now_mono = time.monotonic()
            self._stopwatch_elapsed_ms += (now_mono - self._stopwatch_last_tick) * 1000
            self._stopwatch_running = False

    def _stopwatch_reset(self):
        """
        Resets the stopwatch to zero and reverts to normal clock display.

        Algorithm:
        1. Set running to False, elapsed to 0, last_tick to None.
        2. Restore the time label style to normal clock.
        3. Call _update_clock() to immediately show the clock.
        """
        self._stopwatch_running = False
        self._stopwatch_elapsed_ms = 0
        self._stopwatch_last_tick = None
        self._time_label.setStyleSheet(TIME_LABEL_STYLE)
        self._update_clock()

    # ── Windows startup registry ─────────────────────────────────
    def _is_startup_enabled(self):
        """
        Checks if the ClockWidget registry value exists in the HKCU Run key.

        Algorithm:
        1. Open the HKCU Run registry key for reading.
        2. Try to query the ClockWidget value.
        3. Return True if it exists, False otherwise.

        Returns:
            bool - True if the startup registry entry exists.
        """
        try:
            # Open HKCU Run key and check for our value
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_KEY) as key:
                winreg.QueryValueEx(key, _REGISTRY_VALUE_NAME)
                return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def _toggle_startup(self):
        """
        Toggles the Windows startup registry entry. If it exists, delete it.
        If it doesn't, create it pointing to pythonw.exe with this script.

        Algorithm:
        1. Check if startup is currently enabled.
        2. If enabled: open the Run key and delete the ClockWidget value.
        3. If disabled: build the command string using pythonw.exe and the
           absolute path to this script, then write it to the registry.
        """
        if self._is_startup_enabled():
            # Remove the registry entry
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, _REGISTRY_VALUE_NAME)
        else:
            # Build command: use pythonw.exe to avoid a console window on startup
            python_dir = os.path.dirname(sys.executable)
            pythonw = os.path.join(python_dir, "pythonw.exe")
            script_path = os.path.abspath(__file__)
            command = f'"{pythonw}" "{script_path}"'

            # Write the registry entry
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, _REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, command
                )

    # ── Toggle methods ───────────────────────────────────────────
    def _toggle_topmost(self):
        """
        Toggles the always-on-top window flag.

        Algorithm:
        1. Flip _always_on_top state.
        2. Read current window flags.
        3. Set or clear WindowStaysOnTopHint.
        4. Reapply flags and call show() (Qt hides window on flag change).
        """
        self._always_on_top = not self._always_on_top
        flags = self.windowFlags()
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        # setWindowFlags hides the widget; must re-show
        self.show()

    def _toggle_format(self):
        """Flips between 12h and 24h display, updates immediately."""
        self._clock_format_24h = not self._clock_format_24h
        self._update_clock()

    def _toggle_seconds(self):
        """Flips seconds visibility, updates immediately."""
        self._show_seconds = not self._show_seconds
        self._update_clock()

    def _toggle_draggable(self):
        """Flips draggable mode. When disabled, resets position to top-right."""
        self._draggable = not self._draggable
        if not self._draggable:
            self._drag_position = None
            self._position_top_right()

    # ── Mouse events for drag-to-move (only when draggable) ──────
    def mousePressEvent(self, event: QMouseEvent):
        """
        Records the cursor offset from the window's top-left at drag start,
        only if draggable mode is enabled.

        Args:
            event: QMouseEvent with button and global position.
        """
        if self._draggable and event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Moves the window to follow the cursor during a drag.

        Args:
            event: QMouseEvent with current global position.
        """
        if self._draggable and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Clears drag state when the mouse button is released.

        Args:
            event: QMouseEvent (button release).
        """
        self._drag_position = None
        event.accept()

    def contextMenuEvent(self, event):
        """
        Shows the right-click context menu at the cursor position, syncing
        checkable action states first.

        Args:
            event: QContextMenuEvent with global position.
        """
        # Sync check marks to current state before showing
        self._topmost_action.setChecked(self._always_on_top)
        self._format_action.setChecked(self._clock_format_24h)
        self._seconds_action.setChecked(self._show_seconds)
        self._startup_action.setChecked(self._is_startup_enabled())
        self._draggable_action.setChecked(self._draggable)
        self._context_menu.exec(event.globalPos())


def _acquire_single_instance_lock():
    """
    Attempts to create a Windows named mutex to enforce single-instance.

    Algorithm:
    1. Call CreateMutexW with a unique name for this app.
    2. Check GetLastError() -- ERROR_ALREADY_EXISTS (183) means another
       instance holds the mutex.
    3. If another instance exists, return False. Otherwise return True.
    4. The mutex handle is intentionally kept alive (not closed) for the
       lifetime of the process. Windows releases it on process exit.

    Returns:
        bool - True if this is the first instance, False if another is running.
    """
    # CreateMutexW returns a handle; if the mutex already exists, GetLastError
    # returns ERROR_ALREADY_EXISTS but the handle is still valid.
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, "ClockWidget_SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return False
    return handle != 0


if __name__ == "__main__":
    if not _acquire_single_instance_lock():
        sys.exit(0)

    app = QApplication(sys.argv)
    widget = ClockWidget()
    widget.show()
    sys.exit(app.exec())
