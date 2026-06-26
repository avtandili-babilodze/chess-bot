"""The chess rules engine.

:class:`Chess` holds the board state and implements all the rules: move
generation, check / checkmate / stalemate detection, castling, en passant and
pawn promotion. It is completely independent of the GUI, so it can be unit
tested or reused on its own.
"""

from chess_game.pieces import INITIAL, player_of, opp


class Chess:
    """A single chess game: board state plus all the move rules."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Restore the standard starting position and a fresh game state."""
        self.board = [row[:] for row in INITIAL]
        self.turn = "w"
        self.ep = None                              # en passant target (row, col)
        self.castle = {"w": [True, True],           # [kingside, queenside]
                       "b": [True, True]}
        self.status = "White's turn"
        self.over = False

    # ── attack detection ─────────────────────────────────────────────────────

    def attacks(self, board, r, c, by):
        """Return ``True`` if player *by* attacks square ``(r, c)`` on *board*."""
        for sr in range(8):
            for sc in range(8):
                p = board[sr][sc]
                if player_of(p) != by:
                    continue
                t = p.upper()
                if t == "P":
                    d = -1 if by == "w" else 1
                    if sr + d == r and abs(sc - c) == 1:
                        return True
                elif t == "N":
                    if (abs(sr - r), abs(sc - c)) in {(1, 2), (2, 1)}:
                        return True
                elif t == "K":
                    if max(abs(sr - r), abs(sc - c)) == 1:
                        return True
                elif t in ("B", "R", "Q"):
                    dirs = []
                    if t in ("B", "Q"):
                        dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    if t in ("R", "Q"):
                        dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in dirs:
                        nr, nc = sr + dr, sc + dc
                        while 0 <= nr < 8 and 0 <= nc < 8:
                            if nr == r and nc == c:
                                return True
                            if board[nr][nc] != ".":
                                break
                            nr += dr
                            nc += dc
        return False

    def in_check(self, board, pl):
        """Return ``True`` if player *pl*'s king is under attack on *board*."""
        king = "K" if pl == "w" else "k"
        for r in range(8):
            for c in range(8):
                if board[r][c] == king:
                    return self.attacks(board, r, c, opp(pl))
        return False

    # ── move generation ───────────────────────────────────────────────────────

    def pseudo_moves(self, r, c):
        """List moves for the piece at ``(r, c)`` ignoring checks and castling.

        These are "pseudo-legal": geometrically valid for the piece, but they
        may still leave the mover's own king in check. :meth:`legal_moves`
        filters those out.
        """
        board = self.board
        p = board[r][c]
        pl = player_of(p)
        t = p.upper()
        moves = []

        if t == "P":
            d = -1 if pl == "w" else 1
            start = 6 if pl == "w" else 1
            # One square forward, then two from the starting rank.
            if 0 <= r + d < 8 and board[r + d][c] == ".":
                moves.append((r + d, c))
                if r == start and board[r + 2 * d][c] == ".":
                    moves.append((r + 2 * d, c))
            # Diagonal captures, including en passant.
            for dc in [-1, 1]:
                nr, nc = r + d, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if player_of(board[nr][nc]) == opp(pl):
                        moves.append((nr, nc))
                    elif self.ep and (nr, nc) == self.ep:
                        moves.append((nr, nc))

        elif t == "N":
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and player_of(board[nr][nc]) != pl:
                    moves.append((nr, nc))

        elif t in ("B", "R", "Q"):
            # Slide along each direction until blocked or off-board.
            dirs = []
            if t in ("B", "Q"):
                dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            if t in ("R", "Q"):
                dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if player_of(board[nr][nc]) == pl:
                        break
                    moves.append((nr, nc))
                    if board[nr][nc] != ".":
                        break
                    nr += dr
                    nc += dc

        elif t == "K":
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if not (dr == 0 and dc == 0):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and player_of(board[nr][nc]) != pl:
                            moves.append((nr, nc))

        return moves

    def _apply(self, board, fr, fc, tr, tc):
        """Return a *copy* of *board* after moving ``(fr,fc)`` -> ``(tr,tc)``.

        Used only to test a candidate move for legality, so it leaves the real
        board untouched. Handles the en-passant capture and the rook hop of a
        castling move.
        """
        b = [row[:] for row in board]
        p = b[fr][fc]
        t = p.upper()
        pl = player_of(p)

        # En passant: remove the pawn that was captured in passing.
        if t == "P" and self.ep and (tr, tc) == self.ep:
            d = 1 if pl == "w" else -1
            b[tr + d][tc] = "."

        # Castling: move the rook to the far side of the king.
        if t == "K" and abs(tc - fc) == 2:
            if tc == 6:
                b[fr][5] = b[fr][7]
                b[fr][7] = "."
            else:
                b[fr][3] = b[fr][0]
                b[fr][0] = "."

        b[tr][tc] = p
        b[fr][fc] = "."
        return b

    def legal_moves(self, r, c):
        """Return the fully legal destination squares for the piece at ``(r, c)``.

        Returns an empty list if the square is empty or holds an enemy piece.
        Adds castling moves for the king and removes any move that would leave
        the mover's own king in check.
        """
        p = self.board[r][c]
        if player_of(p) != self.turn:
            return []

        pl = player_of(p)
        moves = self.pseudo_moves(r, c)

        # Castling: king on its home square, not in check, with empty,
        # un-attacked squares between it and an eligible rook.
        if p.upper() == "K":
            kr = 7 if pl == "w" else 0
            if r == kr and c == 4 and not self.in_check(self.board, pl):
                at = lambda sq: self.attacks(self.board, kr, sq, opp(pl))
                if self.castle[pl][0]:                                  # kingside
                    if self.board[kr][5] == "." and self.board[kr][6] == ".":
                        if not at(5) and not at(6):
                            moves.append((kr, 6))
                if self.castle[pl][1]:                                  # queenside
                    if all(self.board[kr][col] == "." for col in [1, 2, 3]):
                        if not at(3) and not at(2):
                            moves.append((kr, 2))

        # Keep only moves that do not leave our own king in check.
        legal = []
        for tr, tc in moves:
            b = self._apply(self.board, r, c, tr, tc)
            if not self.in_check(b, self.turn):
                legal.append((tr, tc))
        return legal

    def all_legal_moves(self):
        """Return every legal move for the side to move as ``(fr, fc, tr, tc)``."""
        moves = []
        for r in range(8):
            for c in range(8):
                if player_of(self.board[r][c]) == self.turn:
                    for tr, tc in self.legal_moves(r, c):
                        moves.append((r, c, tr, tc))
        return moves

    def clone(self):
        """Return a deep-enough copy of this game for AI search.

        Copies the mutable board / castling state so a search can make and
        explore moves on the copy without disturbing the real game.
        """
        new = Chess.__new__(Chess)
        new.board = [row[:] for row in self.board]
        new.turn = self.turn
        new.ep = self.ep
        new.castle = {"w": self.castle["w"][:], "b": self.castle["b"][:]}
        new.status = self.status
        new.over = self.over
        return new

    def has_any_legal(self, pl):
        """Return ``True`` if player *pl* has at least one legal move."""
        old = self.turn
        self.turn = pl
        found = any(
            self.legal_moves(r, c)
            for r in range(8)
            for c in range(8)
            if player_of(self.board[r][c]) == pl
        )
        self.turn = old
        return found

    # ── making a move ─────────────────────────────────────────────────────────

    def move(self, fr, fc, tr, tc):
        """Execute the move ``(fr,fc)`` -> ``(tr,tc)`` on the real board.

        Assumes the move is already known to be legal. Updates castling rights,
        the en-passant target and performs castling / en-passant side effects.

        Returns ``True`` when the move lands a pawn on the back rank and a
        promotion choice is still needed; in that case the turn does **not**
        advance until :meth:`promote` is called. Otherwise returns ``False``
        and hands the turn to the opponent.
        """
        p = self.board[fr][fc]
        pl = player_of(p)
        old_ep = self.ep
        self.ep = None

        # Moving the king forfeits both castling rights (and may be a castle).
        if p.upper() == "K":
            self.castle[pl] = [False, False]
            if abs(tc - fc) == 2:
                if tc == 6:
                    self.board[fr][5] = self.board[fr][7]
                    self.board[fr][7] = "."
                else:
                    self.board[fr][3] = self.board[fr][0]
                    self.board[fr][0] = "."

        # Moving a rook forfeits castling rights on that side.
        if p == "R":
            if fr == 7 and fc == 0:
                self.castle["w"][1] = False
            if fr == 7 and fc == 7:
                self.castle["w"][0] = False
        if p == "r":
            if fr == 0 and fc == 0:
                self.castle["b"][1] = False
            if fr == 0 and fc == 7:
                self.castle["b"][0] = False

        # En passant capture: remove the pawn that moved past us last turn.
        if p.upper() == "P" and old_ep and (tr, tc) == old_ep:
            d = 1 if pl == "w" else -1
            self.board[tr + d][tc] = "."

        # A two-square pawn push creates a new en-passant target behind it.
        if p.upper() == "P" and abs(tr - fr) == 2:
            self.ep = ((fr + tr) // 2, tc)

        self.board[tr][tc] = p
        self.board[fr][fc] = "."

        # Reaching the far rank: caller must pick a promotion piece.
        if p == "P" and tr == 0:
            return True
        if p == "p" and tr == 7:
            return True

        self._end_turn()
        return False

    def promote(self, r, c, piece_char):
        """Replace the pawn at ``(r, c)`` with *piece_char* and end the turn."""
        self.board[r][c] = piece_char
        self._end_turn()

    def _end_turn(self):
        """Switch the side to move and refresh the status / game-over flags."""
        self.turn = opp(self.turn)
        name = "White" if self.turn == "w" else "Black"
        if not self.has_any_legal(self.turn):
            if self.in_check(self.board, self.turn):
                winner = "Black" if self.turn == "w" else "White"
                self.status = f"Checkmate! {winner} wins!"
            else:
                self.status = "Stalemate — Draw!"
            self.over = True
        elif self.in_check(self.board, self.turn):
            self.status = f"{name} is in check!"
        else:
            self.status = f"{name}'s turn"
