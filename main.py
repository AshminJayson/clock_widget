"""
Elegant Always-On-Top Clock Widget for Windows
A minimal, draggable, transparent clock that floats above all windows.
Built with PyQt6 for rounded corners, drop shadow, and crisp DPI rendering.
"""

import sys
import time

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QAction, QMouseEvent, QColor
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
SHOW_SECONDS = True               # Display seconds
SHOW_DATE = True                  # Display date below time

# Theme: white on black
BG_COLOR = "#0a0a0a"              # Near-black background
TIME_COLOR = "#f0f0f0"            # White for time digits
DATE_COLOR = "#b0b0b0"            # Light grey for date
BORDER_COLOR = "#1a1a1a"          # Subtle dark border
BORDER_RADIUS = 8                 # Rounded corner radius in px

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
    """

    def __init__(self):
        """
        Algorithm:
        1. Set window flags: frameless, always-on-top, tool (no taskbar entry).
        2. Set translucent background so rounded corners show through.
        3. Initialize toggle state as instance variables.
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
        self._drag_position = None

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
        Creates the right-click menu with checkable toggle actions and a
        close action.

        Algorithm:
        1. Create a QMenu styled to match the dark theme.
        2. Add checkable actions for always-on-top, 24h format, seconds.
        3. Set their initial checked state from instance variables.
        4. Connect each to its toggle method.
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

    def _update_clock(self):
        """
        Reads current local time and updates the time and date labels.

        Algorithm:
        1. Get current time via time.localtime().
        2. Build format string from _clock_format_24h and _show_seconds flags.
        3. Set the time label text.
        4. Build date string in "Friday, Feb 20 2026" format.
        5. Set or clear the date label based on _show_date.
        """
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

    # ── Mouse events for drag-to-move ────────────────────────────
    def mousePressEvent(self, event: QMouseEvent):
        """
        Records the cursor offset from the window's top-left at drag start.

        Args:
            event: QMouseEvent with button and global position.
        """
        if event.button() == Qt.MouseButton.LeftButton:
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
        if self._drag_position is not None:
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
        self._context_menu.exec(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ClockWidget()
    widget.show()
    sys.exit(app.exec())
