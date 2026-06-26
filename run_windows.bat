@echo off
REM ===================================================================
REM  One-click launcher for Windows.
REM
REM  Double-click this file to play. If Python is not installed it will
REM  try to install it automatically (via winget, or by downloading the
REM  official installer). Tkinter ships with Python, so nothing else is
REM  needed.
REM ===================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM --- 1. Is Python already available? --------------------------------
call :find_python
if defined PYLAUNCH goto run

REM --- 2. Not found: try to install it automatically ------------------
echo.
echo Python was not found on this computer.
echo Attempting to install it automatically (this needs an internet
echo connection and may ask for permission)...
echo.

where winget >nul 2>nul
if %errorlevel%==0 (
    echo Installing Python via winget...
    winget install -e --id Python.Python.3.12 --scope user ^
        --accept-package-agreements --accept-source-agreements
) else (
    echo winget is not available. Downloading the official installer...
    set "INSTALLER=%TEMP%\python-setup.exe"
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-setup.exe'"
    echo Installing Python (this may take a minute)...
    "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
    del "%TEMP%\python-setup.exe" >nul 2>nul
)

REM --- 3. Look again after the install --------------------------------
call :find_python
if not defined PYLAUNCH (
    echo.
    echo Could not install or locate Python automatically.
    echo Please install it manually from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    echo.
    pause
    exit /b 1
)

REM --- 4. Run the game -----------------------------------------------
:run
echo Starting Chess...
%PYLAUNCH% main.py
if %errorlevel% neq 0 (
    echo.
    echo The game exited with an error.
    pause
)
exit /b

REM ===================================================================
REM  Helper: locate a usable Python and store the command in PYLAUNCH.
REM  Checks the "py" launcher, then "python" on PATH, then the default
REM  per-user install folder (PATH is not refreshed inside this session
REM  right after a silent install, so we look there directly).
REM ===================================================================
:find_python
set "PYLAUNCH="
py -3 -V >nul 2>nul && ( set "PYLAUNCH=py -3" & exit /b )
python -V >nul 2>nul && ( set "PYLAUNCH=python" & exit /b )
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" ( set PYLAUNCH="%%D\python.exe" & exit /b )
)
exit /b
