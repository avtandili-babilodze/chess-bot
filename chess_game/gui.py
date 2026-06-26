"""The tkinter front-end: draws the board and handles mouse input.

:class:`GUI` owns a :class:`~chess_game.engine.Chess` instance and translates
clicks into moves. It knows nothing about the rules beyond asking the engine
for legal moves and telling it to make them.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from chess_game.bot import Bot
from chess_game.engine import Chess
from chess_game.pieces import UNICODE, is_white, player_of

# Difficulty presets: (search-depth cap, time budget in seconds).
DIFFICULTIES = {
    "Easy": (2, 1.0),
    "Medium": (3, 2.0),
    "Hard": (5, 4.0),
    "Master": (7, 8.0),
}


class GUI:
    """A tkinter chessboard window for a two-player (hot-seat) game."""

    SQ = 80              # size of one square in pixels
    LIGHT = "#F0D9B5"    # light board square
    DARK = "#B58863"     # dark board square
    SEL = "#829769"      # highlight for the selected square
    HINT = "#CDD26E"     # highlight for a legal destination
    TIP = "#3A6EA5"      # outline marking a suggested (hint) move

    def __init__(self, root):
        """Build the widgets (status bar, board canvas, New Game button)."""
        self.root = root
        root.title("Chess")
        root.resizable(False, False)

        self.g = Chess()
        self.sel = None              # currently selected square, or None
        self.hints = []              # legal destinations for the selection
        self.awaiting_promo = None   # square waiting for a promotion choice

        self.bot = None              # the AI opponent, or None for two players
        self.bot_color = None        # "w" / "b" the bot plays, or None
        self.flip = False            # True draws Black at the bottom
        self.thinking = False        # True while a search (move or hint) runs
        self._bot_result = None      # holder for a finished move search
        self._hint_result = None     # holder for a finished hint search
        self.hint_move = None        # (fr, fc, tr, tc) suggested move to show
        # A dedicated engine for hints, so they work in two-player games too.
        self.hint_engine = Bot(max_depth=4, time_limit=3.0)

        # Status bar across the top.
        self.sv = tk.StringVar(value="White's turn")
        tk.Label(root, textvariable=self.sv, font=("Arial", 13, "bold"),
                 bg="#2d2d2d", fg="white", pady=7).pack(fill="x")

        # The board itself.
        size = self.SQ * 8
        self.cv = tk.Canvas(root, width=size, height=size, highlightthickness=0)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.click)

        # Bottom bar with the New Game and Hint buttons.
        bar = tk.Frame(root, bg="#2d2d2d", pady=5)
        bar.pack(fill="x")
        inner = tk.Frame(bar, bg="#2d2d2d")
        inner.pack()                                    # centres the buttons
        tk.Button(inner, text="New Game", command=self.new_game,
                  font=("Arial", 11), bg="#4a4a4a", fg="white",
                  activebackground="#666666", activeforeground="white",
                  relief="flat", padx=15, pady=3).pack(side="left", padx=4)
        self.hint_btn = tk.Button(inner, text="Hint", command=self.show_hint,
                                  font=("Arial", 11), bg="#4a4a4a", fg="white",
                                  activebackground="#666666", activeforeground="white",
                                  relief="flat", padx=15, pady=3)
        self.hint_btn.pack(side="left", padx=4)

        self.redraw()
        # Ask how to play once the window is up.
        self.root.after(100, self.new_game)

    # ── coordinate mapping ─────────────────────────────────────────────────────

    def _screen(self, r, c):
        """Map a board square ``(r, c)`` to its on-screen ``(row, col)``.

        With the board flipped (playing Black) this mirrors both axes. The
        transform is its own inverse, so it also maps screen back to board.
        """
        return (7 - r, 7 - c) if self.flip else (r, c)

    # ── drawing ────────────────────────────────────────────────────────────────

    def redraw(self):
        """Repaint the whole board: squares, highlights, pieces and labels."""
        cv, sq = self.cv, self.SQ
        board = self.g.board
        cv.delete("all")

        for r in range(8):
            for c in range(8):
                dr, dc = self._screen(r, c)
                x1, y1 = dc * sq, dr * sq
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

        # Outline the from/to squares of a suggested move, if any.
        if self.hint_move:
            fr, fc, tr, tc = self.hint_move
            for hr, hc in [(fr, fc), (tr, tc)]:
                dr, dc = self._screen(hr, hc)
                x1, y1 = dc * sq, dr * sq
                cv.create_rectangle(x1 + 3, y1 + 3, x1 + sq - 3, y1 + sq - 3,
                                    outline=self.TIP, width=4)

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
        """Draw the file letters (a-h) and rank numbers (1-8) on the edges.

        Labels follow the board orientation, so they read correctly whether
        White or Black is at the bottom.
        """
        cv, sq = self.cv, self.SQ
        for i in range(8):
            rank_fg = self.DARK if i % 2 == 0 else self.LIGHT
            file_fg = self.LIGHT if i % 2 == 0 else self.DARK
            # Board row/col shown in display column/row ``i``.
            row = 7 - i if self.flip else i
            col = 7 - i if self.flip else i
            cv.create_text(3, i * sq + 12, text=str(8 - row),
                           font=("Arial", 8, "bold"), fill=rank_fg, anchor="w")
            cv.create_text((i + 1) * sq - 3, 8 * sq - 3, text="abcdefgh"[col],
                           font=("Arial", 8, "bold"), fill=file_fg, anchor="se")

    # ── interaction ────────────────────────────────────────────────────────────

    def click(self, event):
        """Handle a left-click: select a piece, or move the selected piece."""
        g = self.g
        if g.over or self.awaiting_promo or self.thinking:
            return
        # Any interaction clears a shown hint.
        self.hint_move = None
        # When playing the computer, ignore clicks during its turn.
        if self.bot and g.turn == self.bot_color:
            return
        sq = self.SQ
        dc, dr = event.x // sq, event.y // sq
        if not (0 <= dr < 8 and 0 <= dc < 8):
            return
        # Translate the clicked screen square into a board square.
        r, c = self._screen(dr, dc)

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
                # Hand off to the computer if it is now its turn.
                self.redraw()
                self._maybe_bot_move()
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
            else:
                self._maybe_bot_move()

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
        """Reset to a fresh game, then ask how the user wants to play."""
        self.g = Chess()
        self.sel = None
        self.hints = []
        self.awaiting_promo = None
        self.thinking = False
        self._bot_result = None
        self._hint_result = None
        self.hint_move = None
        self.redraw()
        self._setup_dialog()

    # ── opponent setup ───────────────────────────────────────────────────────

    def _setup_dialog(self):
        """Ask whether to play the computer; configure the bot accordingly."""
        dlg = tk.Toplevel(self.root)
        dlg.title("New Game")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.configure(bg="#2d2d2d")

        tk.Label(dlg, text="How would you like to play?",
                 font=("Arial", 13, "bold"), bg="#2d2d2d", fg="white",
                 pady=12).pack(padx=24)

        # Colour the human plays when facing the computer.
        color = tk.StringVar(value="w")
        crow = tk.Frame(dlg, bg="#2d2d2d")
        crow.pack(pady=(0, 6))
        tk.Label(crow, text="Play as:", font=("Arial", 11),
                 bg="#2d2d2d", fg="white").pack(side="left", padx=(0, 8))
        for text, val in [("White", "w"), ("Black", "b")]:
            tk.Radiobutton(crow, text=text, variable=color, value=val,
                           font=("Arial", 11), bg="#2d2d2d", fg="white",
                           selectcolor="#4a4a4a", activebackground="#2d2d2d",
                           activeforeground="white").pack(side="left")

        # Difficulty of the computer.
        drow = tk.Frame(dlg, bg="#2d2d2d")
        drow.pack(pady=(0, 10))
        tk.Label(drow, text="Difficulty:", font=("Arial", 11),
                 bg="#2d2d2d", fg="white").pack(side="left", padx=(0, 8))
        level = tk.StringVar(value="Hard")
        tk.OptionMenu(drow, level, *DIFFICULTIES).pack(side="left")

        def start(vs_computer):
            """Apply the chosen settings, close the dialog and kick things off."""
            if vs_computer:
                depth, budget = DIFFICULTIES[level.get()]
                self.bot = Bot(max_depth=depth, time_limit=budget)
                # The bot plays the colour the human did not pick.
                self.bot_color = "b" if color.get() == "w" else "w"
                # Show the human's pieces at the bottom.
                self.flip = color.get() == "b"
            else:
                self.bot = None
                self.bot_color = None
                self.flip = False
            dlg.destroy()
            self.redraw()
            self._maybe_bot_move()

        brow = tk.Frame(dlg, bg="#2d2d2d")
        brow.pack(padx=24, pady=(0, 16))
        tk.Button(brow, text="Play vs Computer", font=("Arial", 11),
                  bg="#4a7a4a", fg="white", activebackground="#5a8a5a",
                  activeforeground="white", relief="flat", padx=12, pady=4,
                  command=lambda: start(True)).pack(side="left", padx=4)
        tk.Button(brow, text="Two Players", font=("Arial", 11),
                  bg="#4a4a4a", fg="white", activebackground="#666666",
                  activeforeground="white", relief="flat", padx=12, pady=4,
                  command=lambda: start(False)).pack(side="left", padx=4)

        # Default to two players if the dialog is closed with the window's X.
        dlg.protocol("WM_DELETE_WINDOW", lambda: start(False))

        # Centre over the main window, then grab input modally.
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        dlg.wait_visibility()
        dlg.grab_set()

    # ── computer moves ───────────────────────────────────────────────────────

    def _maybe_bot_move(self):
        """If it is the computer's turn, start computing its move."""
        if not self.bot or self.g.over or self.thinking:
            return
        if self.g.turn != self.bot_color:
            return

        self.thinking = True
        self.sel = None
        self.hints = []
        self.sv.set("Computer is thinking…")
        self._bot_result = None

        # Search on a clone in a background thread so the UI stays responsive.
        snapshot = self.g.clone()
        threading.Thread(target=self._bot_worker, args=(snapshot,),
                         daemon=True).start()
        self.root.after(80, self._poll_bot)

    def _bot_worker(self, snapshot):
        """Run the search (off the main thread) and stash the chosen move."""
        move = self.bot.choose_move(snapshot)
        self._bot_result = (move,)            # tuple marks "done" (move may be None)

    def _poll_bot(self):
        """Poll for the background search to finish, then play its move."""
        if self._bot_result is None:
            self.root.after(80, self._poll_bot)
            return

        (move,) = self._bot_result
        self._bot_result = None
        self.thinking = False
        if move is None:
            return                            # no legal move (game already over)

        fr, fc, tr, tc = move
        if self.g.move(fr, fc, tr, tc):       # bot promotion: always a queen
            self.g.promote(tr, tc, "Q" if self.g.turn == "w" else "q")
        self.redraw()
        if self.g.over:
            messagebox.showinfo("Game Over", self.g.status, parent=self.root)

    # ── hints ──────────────────────────────────────────────────────────────────

    def show_hint(self):
        """Compute and highlight a strong move for the side to move."""
        g = self.g
        if g.over or self.awaiting_promo or self.thinking:
            return
        # In a game vs the computer, only hint on the human's turn.
        if self.bot and g.turn == self.bot_color:
            return

        self.thinking = True
        self.hint_move = None
        self.hint_btn.config(state="disabled")
        self.sv.set("Finding the best move…")
        self._hint_result = None

        snapshot = g.clone()
        threading.Thread(target=self._hint_worker, args=(snapshot,),
                         daemon=True).start()
        self.root.after(80, self._poll_hint)

    def _hint_worker(self, snapshot):
        """Run the hint search off the main thread and stash the result."""
        move = self.hint_engine.choose_move(snapshot)
        self._hint_result = (move,)

    def _poll_hint(self):
        """Poll for the hint search to finish, then display it on the board."""
        if self._hint_result is None:
            self.root.after(80, self._poll_hint)
            return

        (move,) = self._hint_result
        self._hint_result = None
        self.thinking = False
        self.hint_btn.config(state="normal")
        # Only show the move if it still applies (guards against a New Game
        # started while the search was running).
        self.hint_move = move if move in self.g.all_legal_moves() else None
        self.redraw()                          # restores the status text too
