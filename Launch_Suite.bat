@echo off
TITLE Public Health Data Suite & Governance Workbench
COLOR 0A

echo =======================================================================
echo          PUBLIC HEALTH DATA SUITE & GOVERNANCE WORKBENCH
echo          Lead System Architect: Engr. Tasaddaque Hussain Arain
echo =======================================================================
echo.
echo Launching local zero-knowledge environment... Please wait.
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to system PATH.
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit
)

if not exist "venv" (
    echo [INFO] Creating isolated Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo [INFO] Verifying platform dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo.
echo =======================================================================
echo  SUCCESS: Launching browser interface...
echo  To close the server, close this command prompt window.
echo =======================================================================
echo.
streamlit run main.py

pause