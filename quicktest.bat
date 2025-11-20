@echo off
REM PenDoc Quick Test Script for Windows
REM This script runs a quick test of PenDoc with example data

echo ================================================
echo PenDoc Quick Test
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Installing Playwright browsers...
playwright install chromium

echo.
echo [3/3] Running test scan...
python pendoc.py --urls examples/urls.txt --output test_output

echo.
echo ================================================
echo Test complete!
echo Report generated in: test_output\index.html
echo ================================================
echo.
echo Opening report in browser...
start test_output\index.html

pause

