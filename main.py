"""Entry point: open the chess window.

Run with::

    python main.py
"""

import tkinter as tk

from chess_game.gui import GUI


def main():
    """Create the root window, attach the GUI and start the event loop."""
    root = tk.Tk()
    GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
