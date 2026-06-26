"""The tkinter front-end: draws the board and handles mouse input.

:class:`GUI` owns a :class:`~chess_game.engine.Chess` instance and translates
clicks into moves. It knows nothing about the rules beyond asking the engine
for legal moves and telling it to make them.
"""

import tkinter as tk
from tkinter import messagebox

from chess_game.engine import Chess
from chess_game.pieces import UNICODE, is_white, player_of


class GUI:
    """A tkinter chessboard window for a two-player (hot-seat) game."""

    SQ = 80              # size of one square in pixels
    LIGHT = "#F0D9B5"    # light board square
    DARK = "#B58863"     # dark board square
    SEL = "#829769"      # highlight for the selected square
    HINT = "#CDD26E"     # highlight for a legal destination

    def __init__(self, root):
        """Build the widgets (status bar, board canvas, New Game button)."""
        self.root = root
        root.title("Chess")
        root.resizable(False, False)

        self.g = Chess()
        self.sel = None              # currently selected square, or None
        self.hints = []              # legal destinations for the selection
        self.awaiting_promo = None   # square waiting for a promotion choice

        # Status bar across the top.
        self.sv = tk.StringVar(value="White's turn")
        tk.Label(root, textvariable=self.sv, font=("Arial", 13, "bold"),
                 bg="#2d2d2d", fg="white", pady=7).pack(fill="x")

        # The board itself.
        size = self.SQ * 8
        self.cv = tk.Canvas(root, width=size, height=size, highlightthickness=0)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.click)

        # Bottom bar with the New Game button.
        bar = tk.Frame(root, bg="#2d2d2d", pady=5)
        bar.pack(fill="x")
        tk.Button(bar, text="New Game", command=self.new_game,
                  font=("Arial", 11), bg="#4a4a4a", fg="white",
                  activebackground="#666666", activeforeground="white",
                  relief="flat", padx=15, pady=3).pack()

        self.redraw()

    # ── drawing ────────────────────────────────────────────────────────────────

    def redraw(self):
        """Repaint the whole board: squares, highlights, pieces and labels."""
        cv, sq = self.cv, self.SQ
        board = self.g.board
        cv.delete("all")

        for r in range(8):
            for c in range(8):
                x1, y1 = c * sq, r * sq
                x2, y2 = x1 + sq, y1 + sq

                # Square colour: selection and move hints win over the
                # normal light/dark checker pattern.
                if (r, c) == self.sel:
                    fill = self.SEL
                elif (r, c) in self.hints:
                    fill = self.HINT
                else:
                    fill = self.LIGHT if (r + c) % 2 == 0 else self.DARK
                cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")

                # A dot marks an empty square you can move to.
                if (r, c) in self.hints and board[r][c] == ".":
                    cx, cy = x1 + sq // 2, y1 + sq // 2
                    rad = sq // 5
                    cv.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                   fill="#556B2F", outline="")

                p = board[r][c]
                if p != ".":
                    self._draw_piece(p, x1, y1)

        self._draw_coordinates()
        self.sv.set(self.g.status)

    def _draw_piece(self, piece, x1, y1):
        """Draw *piece* centred in the square whose top-left is ``(x1, y1)``.

        tkinter text has no outline option, so we fake one by stamping the
        glyph in black at eight small offsets and then drawing the fill colour
        on top. White pieces become white-with-black-outline, black pieces
        dark-with-black-outline — clearly distinguishable on any square.
        """
        sq = self.SQ
        cx, cy = x1 + sq // 2, y1 + sq // 2
        # Always use the solid (lowercase) glyph; colour alone signals the side.
        sym = UNICODE[piece.lower()]
        fill = "#ffffff" if is_white(piece) else "#202020"
        font = ("DejaVu Sans", 44)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2),
                       (-2, -2), (2, -2), (-2, 2), (2, 2)]:
            self.cv.create_text(cx + dx, cy + dy, text=sym, font=font, fill="#000000")
        self.cv.create_text(cx, cy, text=sym, font=font, fill=fill)

    def _draw_coordinates(self):
        """Draw the file letters (a-h) and rank numbers (1-8) on the edges."""
        cv, sq = self.cv, self.SQ
        for i in range(8):
            rank_fg = self.DARK if i % 2 == 0 else self.LIGHT
            file_fg = self.LIGHT if i % 2 == 0 else self.DARK
            cv.create_text(3, i * sq + 12, text=str(8 - i),
                           font=("Arial", 8, "bold"), fill=rank_fg, anchor="w")
            cv.create_text((i + 1) * sq - 3, 8 * sq - 3, text="abcdefgh"[i],
                           font=("Arial", 8, "bold"), fill=file_fg, anchor="se")

    # ── interaction ────────────────────────────────────────────────────────────

    def click(self, event):
        """Handle a left-click: select a piece, or move the selected piece."""
        g = self.g
        if g.over or self.awaiting_promo:
            return
        sq = self.SQ
        c, r = event.x // sq, event.y // sq
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        if self.sel is None:
            # First click: select one of our own pieces.
            if player_of(g.board[r][c]) == g.turn:
                self.sel = (r, c)
                self.hints = g.legal_moves(r, c)
        else:
            sr, sc = self.sel
            if (r, c) in self.hints:
                # Second click on a legal square: make the move.
                needs_promo = g.move(sr, sc, r, c)
                self.sel = None
                self.hints = []
                if needs_promo:
                    self.awaiting_promo = (r, c)
                    self.redraw()
                    self._promo_dialog(r, c)
                    return
                if g.over:
                    self.redraw()
                    messagebox.showinfo("Game Over", g.status, parent=self.root)
                    return
            elif (r, c) == self.sel:
                # Clicking the selected piece again deselects it.
                self.sel = None
                self.hints = []
            elif player_of(g.board[r][c]) == g.turn:
                # Clicking another of our pieces switches the selection.
                self.sel = (r, c)
                self.hints = g.legal_moves(r, c)
            else:
                self.sel = None
                self.hints = []

        self.redraw()

    def _promo_dialog(self, r, c):
        """Pop up a modal dialog letting the player choose a promotion piece."""
        pl = "w" if r == 0 else "b"
        dlg = tk.Toplevel(self.root)
        dlg.title("Promote Pawn")
        dlg.resizable(False, False)
        dlg.transient(self.root)

        tk.Label(dlg, text="Promote pawn to:",
                 font=("Arial", 12, "bold"), pady=10).pack()
        frame = tk.Frame(dlg)
        frame.pack(padx=20, pady=(0, 15))

        def choose(pc):
            """Apply the chosen piece, close the dialog and refresh the board."""
            char = pc if pl == "w" else pc.lower()
            self.g.promote(r, c, char)
            self.awaiting_promo = None
            dlg.destroy()
            self.redraw()
            if self.g.over:
                messagebox.showinfo("Game Over", self.g.status, parent=self.root)

        for pc, name in [("Q", "Queen"), ("R", "Rook"),
                         ("B", "Bishop"), ("N", "Knight")]:
            sym = UNICODE[pc if pl == "w" else pc.lower()]
            tk.Button(frame, text=f"{sym}  {name}",
                      font=("Arial", 13), width=13, pady=5,
                      command=lambda x=pc: choose(x)).pack(pady=2, fill="x")

        # Closing the dialog with the window's X defaults to a queen.
        dlg.protocol("WM_DELETE_WINDOW", lambda: choose("Q"))

        # Centre the dialog over the main window.
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        # The window must be viewable before grabbing input, or some window
        # managers raise "grab failed: window not viewable".
        dlg.wait_visibility()
        dlg.grab_set()

    def new_game(self):
        """Start a fresh game and redraw the board."""
        self.g = Chess()
        self.sel = None
        self.hints = []
        self.awaiting_promo = None
        self.redraw()
