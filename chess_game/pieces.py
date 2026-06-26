"""Board constants, piece glyphs and small colour helper functions.

Board representation
--------------------
The board is an 8x8 list of lists indexed ``board[row][col]`` where ``row`` 0
is the top (black's back rank) and ``row`` 7 is the bottom (white's back rank).

Each square holds a single character:

* Uppercase ``KQRBNP`` -> white pieces.
* Lowercase ``kqrbnp`` -> black pieces.
* ``'.'``               -> an empty square.
"""

# Marker used for an empty square.
EMPTY = "."

# Maps a piece character to the Unicode chess glyph used when drawing it.
UNICODE = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}

# The standard starting position, top (black) to bottom (white).
INITIAL = [
    list("rnbqkbnr"),
    list("pppppppp"),
    list("........"),
    list("........"),
    list("........"),
    list("........"),
    list("PPPPPPPP"),
    list("RNBQKBNR"),
]


def is_white(piece):
    """Return ``True`` if *piece* is a white piece (an uppercase letter)."""
    return piece in "KQRBNP"


def is_black(piece):
    """Return ``True`` if *piece* is a black piece (a lowercase letter)."""
    return piece in "kqrbnp"


def player_of(piece):
    """Return ``'w'`` / ``'b'`` for the owner of *piece*, or ``None`` if empty."""
    if is_white(piece):
        return "w"
    if is_black(piece):
        return "b"
    return None


def opp(player):
    """Return the opposing player colour (``'w'`` <-> ``'b'``)."""
    return "b" if player == "w" else "w"
