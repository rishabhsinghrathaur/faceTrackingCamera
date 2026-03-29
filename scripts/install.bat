@echo off
REM Installation script for Windows

echo ======================================
echo Face Tracking Camera - Installation
echo ======================================
echo.

REM Check Python
echo [1/5] Checking Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Python not found. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

python --version
echo + Python found
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo   Virtual environment already exists (skipping)
) else (
    python -m venv venv
    echo + Virtual environment created
)
echo.

REM Install dependencies
echo [3/5] Installing Python dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo + Dependencies installed
echo.

REM Create directories
echo [4/5] Setting up directories...
if not exist logs mkdir logs
if not exist models mkdir models
echo + Directories created
echo.

REM Check for COM ports
echo [5/5] Checking serial ports...
echo + If you have issues, check Device Manager for COM port number
echo + Update config.yaml with correct COM port (e.g., COM3)
echo.

echo ======================================
echo + Installation complete!
echo ======================================
echo.
echo Next steps:
echo   1. Connect Arduino with servo to USB
echo   2. Run calibration: venv\Scripts\activate ^&^& python scripts\run.py calibrate
echo   3. Capture face: venv\Scripts\activate ^&^& python scripts/run.py capture
echo   4. Start tracking: venv\Scripts\activate ^&^& python scripts/run.py track
echo.
echo For help: python scripts\run.py --help
echo.
pause
