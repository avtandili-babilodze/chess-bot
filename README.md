# Chess

A chess game with a graphical board, written in pure Python with **tkinter**. Play hot-seat against a friend or against a **built-in AI opponent**. No third-party libraries required.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-Free-green)

---

## Quick Start

| Platform | How to run |
|----------|------------|
| **Windows** | Double-click `run_windows.bat` — Python installs itself if needed |
| **macOS / Linux** | `./run_unix.sh` — Python & tkinter install themselves if needed |

---

## Features

- **Computer opponent** with four difficulty levels (Easy → Master) — pick your colour at the start of every game
- Full legal-move enforcement for every piece
- Castling (kingside & queenside)
- En passant captures
- Pawn promotion (Queen, Rook, Bishop or Knight)
- Check, checkmate and stalemate detection
- Click-to-move with legal destinations highlighted
- Board coordinates (a–h, 1–8) and a **New Game** button

---

## How to Play

1. **At the start of each game** a window asks how you want to play: *Play vs Computer* (choose your colour and difficulty) or *Two Players*. The same prompt appears whenever you click **New Game**.
2. **White moves first.** White pieces start at the bottom, black at the top.
3. **Click one of your pieces** — it highlights and shows every legal destination with a yellow square or dot.
4. **Click a highlighted square** to move there.
5. When a pawn reaches the far rank, a dialog lets you pick the promotion piece.
6. When playing the computer, the status bar reads *"Computer is thinking…"* while it searches; the board stays responsive.
7. The status bar shows whose turn it is, and announces check, checkmate or stalemate.

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

### macOS / Linux — one command

From a terminal in the project folder:

```bash
./run_unix.sh
```

If it is not executable yet, run `chmod +x run_unix.sh` first.

Like the Windows launcher, this installs everything it needs automatically. Installing system software on Linux/macOS requires administrator rights, so the script will ask for your password (`sudo`) when it has to install Python or tkinter. If you would rather install them yourself, add `python3` and `python3-tk` (see [Requirements](#requirements)) and the script will skip straight to launching the game.

Already have Python 3 and tkinter? You can also run the game directly:

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
│   ├── bot.py           # the AI opponent — alpha-beta search, Bot class
│   └── gui.py           # tkinter window — GUI class
├── main.py              # entry point
├── run_unix.sh          # one-command launcher for macOS / Linux
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
