"""
Always-On-Top Clock Widget for Windows (tkinter version)
A minimal, draggable clock that floats above all windows.
No external dependencies -- uses only Python's built-in tkinter.
"""

import ctypes
import tkinter as tk
from tkinter import font as tkfont
import time
import sys

# Tell Windows to render at native DPI instead of blurry upscaling
ctypes.windll.shcore.SetProcessDpiAwareness(2)

# ─── Configuration ──────────────────────────────────────────────
CLOCK_FORMAT_24H = True           # True for 24-hour, False for 12-hour
SHOW_SECONDS = True               # Display seconds
SHOW_DATE = True                  # Display date below time

# Theme: white on black
BG_COLOR = "#0a0a0a"              # Near-black background
TIME_COLOR = "#f0f0f0"            # White for time digits
DATE_COLOR = "#b0b0b0"            # Light grey for date
BORDER_COLOR = "#1a1a1a"          # Subtle dark border


class ClockWidget:
    """
    A frameless, always-on-top clock widget using pure tkinter.

    Algorithm:
    1. Create a borderless, always-on-top tkinter window.
    2. Build the UI: padded frame with time and date labels.
    3. Populate labels with current time before measuring for position.
    4. Position at top-right of screen.
    5. Bind left-click drag and right-click context menu to all widgets.
    6. Start a 200ms update loop to refresh the clock display.
    """

    def __init__(self):
        """
        Algorithm:
        1. Create the root Tk window with frameless and always-on-top flags.
        2. Call _build_ui() to construct labels and context menu.
        3. Populate labels once via _update_clock(schedule=False).
        4. Position at top-right via _position_top_right().
        5. Bind drag and right-click events to all visible widgets.
        6. Start the clock update loop.
        """
        self.root = tk.Tk()
        self.root.title("Clock Widget")

        # ── Window behaviour ────────────────────────────────────
        self.root.overrideredirect(True)          # Remove title bar
        self.root.attributes("-topmost", True)    # Always on top
        self.root.configure(bg=BG_COLOR)

        # ── Build UI ────────────────────────────────────────────
        self._build_ui()

        # Populate labels with real text before measuring for position
        self._update_clock(schedule=False)

        # Position at top-right corner of screen
        self._position_top_right()

        # ── Dragging state ──────────────────────────────────────
        self._drag_data = {"x": 0, "y": 0}

        # Bind drag events to all widgets
        for widget in [self.root, self.frame, self.time_label, self.date_label]:
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

        # Right-click context menu
        for widget in [self.root, self.frame, self.time_label, self.date_label]:
            widget.bind("<ButtonPress-3>", self._show_context_menu)

        # ── Start the clock ─────────────────────────────────────
        self._update_clock()

    def _build_ui(self):
        """
        Constructs all visible widgets: frame, time label, date label,
        and the right-click context menu.

        Algorithm:
        1. Create a padded frame as the main container with a 1px border.
        2. Create the time label with Consolas 24pt bold (monospace = no jitter).
        3. If date display is enabled, create a Segoe UI 9pt date label.
        4. Build the right-click context menu with toggle options.
        """
        # Main frame - minimal padding, clean edge
        self.frame = tk.Frame(
            self.root,
            bg=BG_COLOR,
            padx=6,
            pady=2,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        self.frame.pack(fill="both", expand=True)

        # Time label - Consolas monospace so digits don't cause width jitter
        self.time_font = tkfont.Font(family="Consolas", size=24, weight="bold")
        self.time_label = tk.Label(
            self.frame,
            text="",
            font=self.time_font,
            fg=TIME_COLOR,
            bg=BG_COLOR,
            anchor="center",
        )
        self.time_label.pack()

        # Date label - clean sans-serif, small
        if SHOW_DATE:
            self.date_font = tkfont.Font(family="Segoe UI", size=9)
            self.date_label = tk.Label(
                self.frame,
                text="",
                font=self.date_font,
                fg=DATE_COLOR,
                bg=BG_COLOR,
                anchor="center",
            )
            self.date_label.pack(pady=(0, 0))
        else:
            # Dummy label so drag/click bindings don't break
            self.date_label = tk.Label(self.frame, bg=BG_COLOR)

        # Context menu - dark theme to match
        self.context_menu = tk.Menu(
            self.root, tearoff=0,
            bg="#1a1a1a", fg="#e0e0e0",
            activebackground="#333333", activeforeground="#fff",
            font=("Segoe UI", 9),
        )
        self.context_menu.add_command(label="Toggle always on top", command=self._toggle_topmost)
        self.context_menu.add_command(label="Toggle 12/24h", command=self._toggle_format)
        self.context_menu.add_command(label="Toggle seconds", command=self._toggle_seconds)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Close", command=self._quit)

    def _position_top_right(self):
        """
        Places the widget at the top-right corner of the screen.

        Algorithm:
        1. Force tkinter to compute the widget's actual width/height.
        2. Read screen width and widget width.
        3. Set x to screen_width - widget_width - margin.
        4. Set y to margin from top.
        5. Apply the position via geometry().
        """
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        ww = self.root.winfo_width()
        margin = 8
        x = sw - ww - margin
        y = margin
        self.root.geometry(f"+{x}+{y}")

    def _update_clock(self, schedule=True):
        """
        Reads current local time and updates the time and date labels.

        Algorithm:
        1. Get current time via time.localtime().
        2. Build format string from CLOCK_FORMAT_24H and SHOW_SECONDS flags.
        3. Set the time label text.
        4. Build date string in "Friday, Feb 20 2026" format, set the date label.
        5. If schedule is True, queue the next refresh in 200ms.

        Args:
            schedule: bool - whether to keep refreshing on a 200ms loop.
                      False is used for the initial call before positioning.
        """
        now = time.localtime()

        if CLOCK_FORMAT_24H:
            fmt = "%H:%M:%S" if SHOW_SECONDS else "%H:%M"
        else:
            fmt = "%I:%M:%S %p" if SHOW_SECONDS else "%I:%M %p"

        time_str = time.strftime(fmt, now)
        self.time_label.config(text=time_str)

        if SHOW_DATE:
            date_str = time.strftime("%A, %b %d %Y", now)
            self.date_label.config(text=date_str)

        if schedule:
            self.root.after(200, self._update_clock)

    def _on_drag_start(self, event):
        """
        Records the mouse position at the start of a drag.

        Args:
            event: tkinter event with x, y coords of the click.
        """
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        """
        Moves the window to follow the mouse during a drag.

        Algorithm:
        1. Compute delta between current mouse pos and drag start pos.
        2. Add delta to the window's current screen position.
        3. Apply the new position.

        Args:
            event: tkinter event with current x, y coords.
        """
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        """
        Pops the right-click context menu at the cursor location.

        Args:
            event: tkinter event with x_root, y_root screen coords.
        """
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _toggle_topmost(self):
        """Toggles the always-on-top window attribute."""
        current = self.root.attributes("-topmost")
        self.root.attributes("-topmost", not current)

    def _toggle_format(self):
        """Toggles between 12-hour and 24-hour clock display."""
        global CLOCK_FORMAT_24H
        CLOCK_FORMAT_24H = not CLOCK_FORMAT_24H

    def _toggle_seconds(self):
        """Toggles seconds visibility in the time display."""
        global SHOW_SECONDS
        SHOW_SECONDS = not SHOW_SECONDS

    def _quit(self):
        """Destroys the window and exits the process."""
        self.root.destroy()
        sys.exit(0)

    def run(self):
        """Starts the tkinter main event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    widget = ClockWidget()
    widget.run()
