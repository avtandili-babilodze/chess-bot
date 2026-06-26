"""A small, dependency-free chess game with a tkinter GUI.

Sub-modules
-----------
pieces : board constants, piece glyphs and colour helpers.
engine : the :class:`~chess_game.engine.Chess` rules engine (no GUI).
gui    : the :class:`~chess_game.gui.GUI` tkinter front-end.
"""

from chess_game.engine import Chess
from chess_game.gui import GUI

__all__ = ["Chess", "GUI"]
__version__ = "1.0.0"
