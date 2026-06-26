@echo off
REM ===================================================================
REM  One-click launcher for Windows.
REM
REM  Double-click this file to play. If Python is not installed it will
REM  try to install it automatically (via winget, or by downloading the
REM  official installer). Tkinter ships with Python, so nothing else is
REM  needed.
REM
REM  This window will stay open until you press a key, so if anything
REM  goes wrong you can read the message instead of it flashing shut.
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
    echo Could not install or locate a working Python automatically.
    echo Please install it manually from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    goto end
)

REM --- 4. Run the game -----------------------------------------------
:run
echo Using Python: %PYLAUNCH%
%PYLAUNCH% -c "import tkinter" >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Python is installed but Tkinter is missing, so the window
    echo cannot open. Re-run the Python installer and make sure
    echo "tcl/tk and IDLE" is selected, then run this file again.
    goto end
)

echo Starting Chess...
%PYLAUNCH% main.py
set "EXITCODE=%errorlevel%"
if not "%EXITCODE%"=="0" (
    echo.
    echo The game exited with an error ^(code %EXITCODE%^).
    echo If a Python error is shown above, please report it.
    goto end
)
REM Normal, clean exit. Nothing went wrong, so just leave quietly.
exit /b 0

REM ===================================================================
REM  Helper: locate a Python that can actually RUN code, store it in
REM  PYLAUNCH. We don't trust "-V" alone, because Windows ships a fake
REM  "python.exe" App-Execution-Alias stub that exists but runs nothing
REM  and silently closes the window. So we test by executing real code:
REM  the stub fails that test, a real interpreter passes it.
REM
REM  Checks the "py" launcher, then "python", then the default per-user
REM  install folder (PATH is not refreshed inside this session right
REM  after a silent install, so we look there directly).
REM ===================================================================
:find_python
set "PYLAUNCH="
py -3 -c "import sys" >nul 2>nul && ( set "PYLAUNCH=py -3" & exit /b )
python -c "import sys" >nul 2>nul && ( set "PYLAUNCH=python" & exit /b )
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys" >nul 2>nul && ( set PYLAUNCH="%%D\python.exe" & exit /b )
    )
)
exit /b

REM ===================================================================
REM  Single place every error path lands on, so the window always
REM  pauses and the message stays readable instead of flashing shut.
REM ===================================================================
:end
echo.
pause
exit /b 1
