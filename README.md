# Chess

A two-player (hot-seat) chess game with a graphical board, written in pure Python with **tkinter**. No third-party libraries required.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-Free-green)

---

## Quick Start

| Platform | How to run |
|----------|------------|
| **Windows** | Double-click `run_windows.bat` — Python installs itself if needed |
| **macOS / Linux** | `python3 main.py` |

---

## Features

- Full legal-move enforcement for every piece
- Castling (kingside & queenside)
- En passant captures
- Pawn promotion (Queen, Rook, Bishop or Knight)
- Check, checkmate and stalemate detection
- Click-to-move with legal destinations highlighted
- Board coordinates (a–h, 1–8) and a **New Game** button

---

## How to Play

1. **White moves first.** White pieces start at the bottom, black at the top.
2. **Click one of your pieces** — it highlights and shows every legal destination with a yellow square or dot.
3. **Click a highlighted square** to move there.
4. When a pawn reaches the far rank, a dialog lets you pick the promotion piece.
5. The status bar shows whose turn it is, and announces check, checkmate or stalemate.

---

## Requirements

- **Python 3.8+**
- **tkinter** (Python's standard GUI toolkit)

| OS | How to get tkinter |
|----|--------------------|
| Windows / macOS | Included with the official installer from [python.org](https://www.python.org/downloads/) |
| Debian / Ubuntu / Kali | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |

---

## Running the Game

### Windows — one click

Double-click **`run_windows.bat`**.

If Python is not installed, the script installs it automatically — first via Windows' built-in `winget`, otherwise by downloading the official installer from python.org. An internet connection and a permission prompt may be required. Tkinter comes bundled, so nothing else is needed.

### macOS / Linux — command line

```bash
python3 main.py
```

---

## Project Structure

```
chess-bot/
├── chess_game/
│   ├── __init__.py      # package exports (Chess, GUI)
│   ├── pieces.py        # board constants, glyphs and colour helpers
│   ├── engine.py        # rules engine (no GUI) — Chess class
│   └── gui.py           # tkinter window — GUI class
├── main.py              # entry point
├── run_windows.bat      # one-click launcher for Windows
└── README.md
```

---

## Using the Engine Without the GUI

The rules engine has no GUI dependencies and can be imported on its own:

```python
from chess_game import Chess

game = Chess()
print(game.legal_moves(6, 4))   # white e2 pawn → [(5, 4), (4, 4)]
game.move(6, 4, 4, 4)           # play 1. e4
```

---

## License

Free to use and modify.
