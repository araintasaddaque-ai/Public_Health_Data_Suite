@echo off
SETLOCAL EnableDelayedExpansion
TITLE Public Health Data Suite ^& Governance Workbench

cls
echo =======================================================================
echo          PUBLIC HEALTH DATA SUITE ^& GOVERNANCE WORKBENCH
echo          Lead System Architect: Engr. Tasaddaque Hussain Arain
echo =======================================================================
echo.

echo [INFO] Launching local zero-knowledge environment... Please wait.
echo.

:: 1. Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to System PATH.
    echo Please install Python 3.10+ and ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and create virtual environment if missing
if not exist "venv" (
    echo [INFO] Creating isolated Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 4. Install / Verify dependencies
echo [INFO] Verifying platform dependencies...
python -m pip install --upgrade pip >nul 2>&1

if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found. Proceeding with installed environment...
)

echo.
echo =======================================================================
echo          SUCCESS: Starting Streamlit Governance Workbench
echo          Local URL: http://localhost:8501
echo =======================================================================
echo.

:: 5. Launch Streamlit application
streamlit run main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Workbench execution terminated with error code %errorlevel%.
    pause
)