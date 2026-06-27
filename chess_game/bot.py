"""A strong chess AI for playing against the engine.

:class:`Bot` searches the game tree with **negamax + alpha-beta pruning**,
driven by **iterative deepening** under a time budget so it always returns a
move and digs deeper when it has time. A **quiescence search** extends capture
sequences past the depth limit to avoid the horizon effect, moves are ordered
**captures-first (MVV-LVA)** to make pruning bite, and positions are scored with
material values plus **piece-square tables** (with a separate king table for the
endgame). It talks to the engine only through :meth:`Chess.all_legal_moves`,
:meth:`Chess.clone`, :meth:`Chess.move` and :meth:`Chess.in_check`.
"""

import time

from chess_game.pieces import player_of


# Centipawn value of each piece (king kept finite but huge).
VALUE = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}

# A mate score; the ply count is subtracted so shorter mates are preferred.
MATE = 1_000_000


# ── piece-square tables (White's view; rank 8 is the first row) ───────────────
# A White piece at (r, c) reads table[r][c]; a Black piece mirrors to [7 - r][c].

PST = {
    "P": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "N": [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
    "B": [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ],
    "R": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [0, 0, 0, 5, 5, 0, 0, 0],
    ],
    "Q": [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ],
    "K": [
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [20, 20, 0, 0, 0, 0, 20, 20],
        [20, 30, 10, 0, 0, 10, 30, 20],
    ],
}

# A centralised king is good once the queens / heavy material are gone.
KING_ENDGAME = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
]


class _Timeout(Exception):
    """Raised internally to abort a search that has run out of time."""


# Transposition-table bound types: is the stored score exact, a lower bound
# (the search failed high / hit a beta cutoff), or an upper bound (failed low)?
_EXACT, _LOWER, _UPPER = 0, 1, 2

# Bonus added to a move's ordering score so the named class sorts ahead of plain
# quiet moves but behind real captures.  History scores stay below _KILLER.
_KILLER = 9_000
_TT_MOVE = 10_000_000        # the table's suggested move is always tried first


class Bot:
    """Picks a move for one side using a time-limited alpha-beta search.

    *max_depth* caps how deep iterative deepening goes; *time_limit* (seconds)
    is the real governor — the search returns the best move from the deepest
    fully-completed iteration once the budget is spent.

    Ordering is sharpened with a **transposition table** (positions reached by
    different move orders are searched once), **killer moves** (quiet moves that
    caused a cutoff at the same ply) and a **history heuristic** (quiet moves
    that have caused cutoffs anywhere).  Better ordering means alpha-beta prunes
    more, which lets iterative deepening reach greater depth in the same time.
    """

    def __init__(self, max_depth=7, time_limit=4.0):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self._start = 0.0
        # Transposition table: position key -> (depth, flag, value, best_move).
        self._tt = {}
        # killers[ply] holds up to two quiet moves that caused a beta cutoff.
        self._killers = []
        # history[move] accumulates how often a quiet move has caused a cutoff.
        self._history = {}

    # ── evaluation ───────────────────────────────────────────────────────────

    def _is_endgame(self, board):
        """Return ``True`` when little heavy material remains (king centralises)."""
        heavy = 0
        for row in board:
            for p in row:
                u = p.upper()
                if u in ("Q", "R", "B", "N"):
                    heavy += VALUE[u]
        return heavy <= 2 * VALUE["R"] + 2 * VALUE["B"]

    def evaluate(self, game):
        """Score *game* in centipawns from White's perspective (White is +)."""
        board = game.board
        endgame = self._is_endgame(board)
        score = 0
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p == ".":
                    continue
                u = p.upper()
                val = VALUE[u]
                if u == "K" and endgame:
                    pst = KING_ENDGAME
                else:
                    pst = PST[u]
                if p.isupper():                         # White
                    score += val + pst[r][c]
                else:                                   # Black: mirror the table
                    score -= val + pst[7 - r][c]
        return score

    def _eval_stm(self, game):
        """Evaluation from the side-to-move's perspective (for negamax)."""
        s = self.evaluate(game)
        return s if game.turn == "w" else -s

    # ── move helpers ─────────────────────────────────────────────────────────

    def _apply(self, game, move):
        """Return the position after *move*, auto-promoting pawns to a queen."""
        fr, fc, tr, tc = move
        g = game.clone()
        if g.move(fr, fc, tr, tc):                      # needs a promotion choice
            g.promote(tr, tc, "Q" if g.turn == "w" else "q")
        return g

    def _is_capture(self, game, move):
        """Return ``True`` if *move* captures (incl. en passant)."""
        fr, fc, tr, tc = move
        if game.board[tr][tc] != ".":
            return True
        # A pawn moving diagonally onto an empty square is an en-passant capture.
        return game.board[fr][fc].upper() == "P" and fc != tc

    def _position_key(self, game):
        """A hashable key identifying *game*'s position for the table.

        Captures everything that affects the legal moves and evaluation: the
        board, the side to move, castling rights and the en-passant target.
        """
        board = tuple(tuple(row) for row in game.board)
        castle = (tuple(game.castle["w"]), tuple(game.castle["b"]))
        return (board, game.turn, castle, game.ep)

    def _capture_score(self, game, m):
        """MVV-LVA score for a capture, or ``None`` when *m* is a quiet move."""
        fr, fc, tr, tc = m
        victim = game.board[tr][tc]
        if victim != ".":
            attacker = game.board[fr][fc]
            return VALUE[victim.upper()] * 10 - VALUE[attacker.upper()]
        if self._is_capture(game, m):                   # en passant
            return VALUE["P"] * 10 - VALUE["P"]
        return None

    def _order(self, game, moves):
        """Order captures most-valuable-victim first (used by quiescence)."""
        def key(m):
            score = self._capture_score(game, m)
            return score if score is not None else -1

        return sorted(moves, key=key, reverse=True)

    def _order_search(self, game, moves, ply, tt_move):
        """Order moves for the main search.

        Priority: the transposition table's move, then captures by MVV-LVA,
        then this ply's killer moves, then quiet moves by history score.  Good
        ordering is what makes alpha-beta actually prune.
        """
        killers = self._killers[ply] if ply < len(self._killers) else ()

        def key(m):
            if m == tt_move:
                return _TT_MOVE
            cap = self._capture_score(game, m)
            if cap is not None:
                return _KILLER + cap                    # captures above killers
            if m in killers:
                return _KILLER - 1
            return self._history.get(m, 0)

        return sorted(moves, key=key, reverse=True)

    def _record_cutoff(self, game, m, depth, ply):
        """Reward a quiet move that caused a beta cutoff (killer + history)."""
        if self._capture_score(game, m) is not None:
            return                                       # captures don't need help
        slot = self._killers[ply]
        if m not in slot:
            slot[1] = slot[0]
            slot[0] = m
        self._history[m] = self._history.get(m, 0) + depth * depth

    def _check_time(self):
        if time.time() - self._start > self.time_limit:
            raise _Timeout()

    # ── search ───────────────────────────────────────────────────────────────

    def _quiesce(self, game, alpha, beta, ply):
        """Search only captures from a position to reach a quiet evaluation."""
        self._check_time()
        stand = self._eval_stm(game)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        captures = [m for m in game.all_legal_moves() if self._is_capture(game, m)]
        for m in self._order(game, captures):
            val = -self._quiesce(self._apply(game, m), -beta, -alpha, ply + 1)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    def _negamax(self, game, depth, alpha, beta, ply):
        """Negamax with alpha-beta pruning; returns a side-to-move score."""
        self._check_time()
        while ply >= len(self._killers):                # grow killer slots lazily
            self._killers.append([None, None])

        alpha_orig = alpha
        key = self._position_key(game)
        entry = self._tt.get(key)
        tt_move = None
        if entry is not None:
            e_depth, e_flag, e_value, e_move = entry
            tt_move = e_move
            if e_depth >= depth:                         # a deep-enough result
                if e_flag == _EXACT:
                    return e_value
                if e_flag == _LOWER and e_value > alpha:
                    alpha = e_value
                elif e_flag == _UPPER and e_value < beta:
                    beta = e_value
                if alpha >= beta:
                    return e_value

        moves = game.all_legal_moves()
        if not moves:                                   # checkmate or stalemate
            if game.in_check(game.board, game.turn):
                return -MATE + ply                      # prefer slower defeats
            return 0                                     # stalemate = draw
        if depth == 0:
            return self._quiesce(game, alpha, beta, ply)

        best, best_move = -MATE * 3, None
        for m in self._order_search(game, moves, ply, tt_move):
            val = -self._negamax(self._apply(game, m), depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best, best_move = val, m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                self._record_cutoff(game, m, depth, ply)
                break                                    # opponent won't allow this

        # Store the result, tagging it as exact or a bound for future probes.
        if best <= alpha_orig:
            flag = _UPPER
        elif best >= beta:
            flag = _LOWER
        else:
            flag = _EXACT
        self._tt[key] = (depth, flag, best, best_move)
        return best

    def choose_move(self, game):
        """Return the best ``(fr, fc, tr, tc)`` move for *game*, or ``None``.

        Runs iterative deepening: each depth's result seeds the next as the
        first move to try, and the deepest completed depth wins. Safe to call
        on a clone from a background thread.
        """
        self._start = time.time()
        self._tt = {}
        self._killers = []
        self._history = {}
        moves = game.all_legal_moves()
        if not moves:
            return None

        best_move = self._order(game, moves)[0]
        for depth in range(1, self.max_depth + 1):
            alpha, beta = -MATE * 3, MATE * 3
            current_best, best_val = None, -MATE * 4
            # Try the previous iteration's best move first.
            ordered = self._order_search(game, moves, 0, best_move)
            try:
                for m in ordered:
                    val = -self._negamax(self._apply(game, m), depth - 1,
                                         -beta, -alpha, 1)
                    if val > best_val:
                        best_val, current_best = val, m
                    if val > alpha:
                        alpha = val
            except _Timeout:
                break                                    # keep the last full depth
            if current_best is not None:
                best_move = current_best
            if best_val >= MATE - 100:                   # forced mate found
                break
        return best_move
