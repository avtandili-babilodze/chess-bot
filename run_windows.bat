@echo off
REM ===================================================================
REM  One-click launcher for Windows.
REM
REM  Chess with a graphical board: play a friend hot-seat or against the
REM  built-in computer opponent (you choose at the start of each game).
REM
REM  Double-click this file to play. If Python is not installed it will
REM  try to install it automatically (via winget, or by downloading the
REM  official installer). Tkinter ships with Python, so nothing else is
REM  needed.
REM
REM  This window ALWAYS waits for a key press before closing, so it can
REM  never just flash open and shut: whatever happens, you can read it.
REM ===================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Chess Launcher

REM --- 1. Is a *working* Python already available? -------------------
call :find_python
if defined PYLAUNCH goto run

REM --- 2. Not found: try to install it automatically ------------------
echo.
echo Python was not found on this computer.
echo Attempting to install it automatically (this needs an internet
echo connection and may ask for permission)...
echo.

where winget >nul 2>nul
if "!errorlevel!"=="0" (
    echo Installing Python via winget...
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
) else (
    echo winget is not available. Downloading the official installer...
    set "INSTALLER=%TEMP%\python-setup.exe"
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-setup.exe'"
    echo Installing Python ^(this may take a minute^)...
    "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
    del "%TEMP%\python-setup.exe" >nul 2>nul
)

REM --- 3. Look again after the install --------------------------------
call :find_python
if not defined PYLAUNCH (
    echo.
    echo Could not install or locate a working Python automatically.
    echo Please install it manually from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    goto end
)

REM --- 4. Run the game -----------------------------------------------
:run
echo Using Python: %PYLAUNCH%
%PYLAUNCH% -c "import sys; print('Python', sys.version.split()[0], 'at', sys.executable)"
echo.
%PYLAUNCH% -c "import tkinter" >nul 2>nul
if not "!errorlevel!"=="0" (
    echo Python is installed but Tkinter is missing, so the window
    echo cannot open. Re-run the Python installer and make sure
    echo "tcl/tk and IDLE" is selected, then run this file again.
    goto end
)

echo Starting Chess...
%PYLAUNCH% main.py
set "EXITCODE=!errorlevel!"
echo.
echo Chess has closed ^(exit code %EXITCODE%^).
if not "%EXITCODE%"=="0" echo If a Python error is shown above, please report it.
goto end

REM ===================================================================
REM  Helper: locate a Python that can actually RUN code, store it in
REM  PYLAUNCH. We don't trust the command merely existing, because
REM  Windows ships a fake "python.exe" App-Execution-Alias stub that
REM  runs nothing. So we make Python PRINT a known value and only
REM  accept it if that value actually comes back: the stub prints
REM  nothing, a real interpreter prints "42".
REM ===================================================================
:find_python
set "PYLAUNCH="
call :verify "py -3"
if defined PYLAUNCH exit /b
call :verify "python"
if defined PYLAUNCH exit /b
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if not defined PYLAUNCH if exist "%%D\python.exe" (
        for /f "delims=" %%v in ('"%%D\python.exe" -c "print(42)" 2^>nul') do (
            if "%%v"=="42" set PYLAUNCH="%%D\python.exe"
        )
    )
)
exit /b

:verify
REM %~1 is a python command. Set PYLAUNCH to it only if it really runs.
set "PYOUT="
for /f "delims=" %%v in ('%~1 -c "print(42)" 2^>nul') do set "PYOUT=%%v"
if "%PYOUT%"=="42" set "PYLAUNCH=%~1"
exit /b

REM ===================================================================
REM  Single place EVERY path lands on (success or failure) so the
REM  window always pauses and never flashes shut.
REM ===================================================================
:end
echo.
pause
exit /b
