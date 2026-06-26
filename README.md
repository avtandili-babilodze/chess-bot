# Chess

A simple two-player (hot-seat) chess game with a graphical board, written in
pure Python with **tkinter**. No third-party libraries required — you play
both sides on the same window.

![board](https://img.shields.io/badge/python-3.8%2B-blue)

## Features

- Full legal-move enforcement for every piece
- Castling (kingside & queenside)
- En passant captures
- Pawn promotion (choose Queen, Rook, Bishop or Knight)
- Check, checkmate and stalemate detection
- Click-to-move with legal destinations highlighted
- Board coordinates (a–h, 1–8) and a "New Game" button

## How to play

1. **White moves first.** White pieces are at the **bottom**, black at the **top**.
2. **Click one of your pieces** — it is highlighted and every legal move is
   shown with a yellow square or a dot.
3. **Click a highlighted square** to move there.
4. When a pawn reaches the far rank, a dialog lets you pick the promotion piece.
5. The status bar at the top shows whose turn it is, check, checkmate or
   stalemate. Click **New Game** to start over.

## Requirements

- **Python 3.8 or newer**
- **tkinter** (Python's standard GUI toolkit)
  - **Windows / macOS:** included with the official installer from
    [python.org](https://www.python.org/downloads/) — nothing to install.
  - **Debian / Ubuntu / Kali Linux:** `sudo apt install python3-tk`
  - **Fedora:** `sudo dnf install python3-tkinter`

## Running the game

### Windows (one click)

Double-click **`run_windows.bat`**. That's it.

If Python is **not** installed, the script tries to install it for you
automatically — first with Windows' built-in `winget`, otherwise by
downloading the official installer from python.org. This needs an internet
connection and may show a permission prompt. Once Python is present it just
launches the game (tkinter comes bundled, so there is nothing else to install).

### Any platform (command line)

From the project folder:

```bash
python main.py
```

(Use `python3 main.py` on systems where `python` points at Python 2.)

## Project structure

```
chess-bot/
├── chess_game/          # the game package
│   ├── __init__.py      # package exports (Chess, GUI)
│   ├── pieces.py        # board constants, glyphs and colour helpers
│   ├── engine.py        # the rules engine (no GUI) — Chess class
│   └── gui.py           # the tkinter window — GUI class
├── main.py              # entry point: opens the window
├── run_windows.bat      # one-click launcher for Windows
├── .gitignore
└── README.md
```

The rules engine (`chess_game/engine.py`) has no GUI dependencies, so it can be
imported and tested on its own:

```python
from chess_game import Chess

game = Chess()
print(game.legal_moves(6, 4))   # white e2 pawn -> [(5, 4), (4, 4)]
game.move(6, 4, 4, 4)           # play 1. e4
```

## License

Free to use and modify.
