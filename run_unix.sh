#!/usr/bin/env bash
# ===================================================================
#  One-click launcher for Linux and macOS.
#
#  Run it from a terminal:   ./run_unix.sh
#  (If it is not executable yet:   chmod +x run_unix.sh )
#
#  Like the Windows launcher, this tries to install everything it
#  needs automatically. On Linux/macOS installing system software
#  requires administrator rights, so IT WILL ASK FOR YOUR PASSWORD
#  (sudo) when it has to install Python or tkinter. If you would
#  rather not, just install "python3" and "python3-tk" yourself and
#  the script will skip straight to launching the game.
# ===================================================================
set -u
cd "$(dirname "$0")"

have() { command -v "$1" >/dev/null 2>&1; }

# Locate a working Python 3 into the PY variable. Returns non-zero if none.
find_python() {
    if have python3 && python3 -c 'import sys' >/dev/null 2>&1; then
        PY=python3; return 0
    fi
    if have python && python -c 'import sys; exit(0 if sys.version_info[0]==3 else 1)' >/dev/null 2>&1; then
        PY=python; return 0
    fi
    return 1
}

# True only when BOTH Python 3 and tkinter are usable.
ready() { find_python && "$PY" -c "import tkinter" >/dev/null 2>&1; }

install_linux() {
    if   have apt-get; then sudo apt-get update && sudo apt-get install -y python3 python3-tk
    elif have dnf;     then sudo dnf install -y python3 python3-tkinter
    elif have pacman;  then sudo pacman -S --noconfirm python tk
    elif have zypper;  then sudo zypper install -y python3 python3-tk
    elif have apk;     then sudo apk add python3 py3-tkinter
    else
        echo "Could not detect your package manager (apt/dnf/pacman/zypper/apk)."
        return 1
    fi
}

install_mac() {
    if ! have brew; then
        echo "Homebrew is needed to install Python. Installing Homebrew now"
        echo "(this is the official installer and may ask for your password)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || return 1
        # Make brew usable in this same session.
        [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
        [ -x /usr/local/bin/brew ]   && eval "$(/usr/local/bin/brew shellenv)"
    fi
    brew install python python-tk
}

# --- 1. Install Python + tkinter if they are not already present ----
if ! ready; then
    echo "Python 3 and/or tkinter are missing. Installing them now..."
    echo
    case "$(uname -s)" in
        Linux)  install_linux ;;
        Darwin) install_mac ;;
        *) echo "Unsupported operating system: $(uname -s)"; exit 1 ;;
    esac
    echo
fi

# --- 2. Make sure it actually worked --------------------------------
if ! ready; then
    echo "Automatic setup did not complete. Please install these manually:"
    echo "  macOS:          brew install python python-tk"
    echo "  Debian/Ubuntu:  sudo apt install python3 python3-tk"
    echo "  Fedora:         sudo dnf install python3 python3-tkinter"
    echo "  Arch:           sudo pacman -S python tk"
    exit 1
fi

# --- 3. Run the game -----------------------------------------------
echo "Using Python: $("$PY" --version 2>&1) at $(command -v "$PY")"
echo "Starting Chess..."
exec "$PY" main.py
