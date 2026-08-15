@echo off
TITLE Public Health Data Suite Launcher
COLOR 0A
echo =========================================================================
echo               Public Health Data Suite & UK Compliance Engine
echo               Architect: Engr. Tasaddaque Hussain Arain
echo =========================================================================
echo.
echo [1/2] Checking & Installing Dependencies...
python -m pip install -r requirements.txt --quiet --no-warn-script-location
echo.
echo [2/2] Launching Google Material 3 Interface in Web Browser...
python -m streamlit run main.py --browser.gatherUsageStats false
pause